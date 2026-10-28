"""Runs grading in the background and reports progress.

A batch of 100 responses takes roughly a minute, which is too long to hold an
HTTP request open, and UC-3 requires the interface to show a processing
indicator while it runs. So grading happens on a worker thread and the browser
polls for progress.

The work is split in two:

  run_grading_job  -- synchronous, does the grading. Called directly by tests.
  start_grading    -- spawns a thread that calls it. Used by the web routes.

Keeping them separate means the pipeline is testable without any threading.
"""
import json
import threading
import traceback

from .db import open_connection
from .grading import (
    GraderConfigError,
    GraderError,
    GraderRateLimitError,
    GraderTransientError,
    ResponseItem,
)
from .grading.base import GradeResult
from .grading.factory import build_grader
from .grading.prompt import EMPTY_RESPONSE_FEEDBACK


def _chunk(items, size):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _set_status(conn, assignment_id, status, error=None):
    conn.execute(
        "UPDATE assignment SET status = ?, error_message = ? WHERE id = ?",
        (status, error, assignment_id),
    )
    conn.commit()


def _bump_progress(conn, assignment_id, amount):
    conn.execute(
        "UPDATE assignment SET progress_done = progress_done + ? WHERE id = ?",
        (amount, assignment_id),
    )
    conn.commit()


def _save_result(conn, response_id, result, model_name):
    part_scores = json.dumps(list(result.part_scores)) if result.part_scores else None
    conn.execute(
        """INSERT INTO grading_result
               (response_id, score, feedback_ar, model_name, error, part_scores)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(response_id) DO UPDATE SET
               score = excluded.score,
               feedback_ar = excluded.feedback_ar,
               model_name = excluded.model_name,
               error = excluded.error,
               part_scores = excluded.part_scores""",
        (response_id, result.score, result.feedback_ar, model_name, result.error,
         part_scores),
    )


def _grade(grader, items, ideal, rubric, max_score, parts):
    # Only a marked-in-parts question passes `parts`, so a grader written
    # against the original four-argument interface keeps working.
    if parts:
        return grader.grade_batch(items, ideal, rubric, max_score, parts=parts)
    return grader.grade_batch(items, ideal, rubric, max_score)


def run_grading_job(app, assignment_id):
    """Grade every response for an assignment. Returns the final status."""
    conn = open_connection(app.config["DATABASE"])
    try:
        assignment = conn.execute(
            "SELECT * FROM assignment WHERE id = ?", (assignment_id,)
        ).fetchone()
        if assignment is None:
            return "failed"

        rows = conn.execute(
            "SELECT id, question_id, student_id, response_text FROM student_response "
            "WHERE assignment_id = ? ORDER BY question_id, row_number",
            (assignment_id,),
        ).fetchall()

        conn.execute(
            "UPDATE assignment SET status='grading', progress_done=0, progress_total=?, "
            "error_message=NULL WHERE id = ?",
            (len(rows), assignment_id),
        )
        conn.commit()

        # Grade with this assignment owner's provider and key, falling back to
        # the server's configuration for anything they have not set.
        try:
            instructor = conn.execute(
                "SELECT * FROM instructor WHERE id = ?", (assignment["instructor_id"],)
            ).fetchone()
            if instructor is None:
                grader = build_grader(app.config)
            else:
                from .settings import grader_for_instructor

                grader = grader_for_instructor(app.config, instructor)
        except GraderConfigError as exc:
            _set_status(conn, assignment_id, "failed", str(exc))
            return "failed"

        # Each question is graded against its own ideal answer and rubric. A
        # single-question upload has no question rows and uses the assignment's.
        contexts = {
            None: (assignment["ideal_answer"], assignment["rubric"] or "",
                   float(assignment["max_score"]),
                   json.loads(assignment["parts"]) if assignment["parts"] else None),
        }
        for question in conn.execute(
            "SELECT * FROM question WHERE assignment_id = ?", (assignment_id,)
        ):
            contexts[question["id"]] = (
                question["ideal_answer"] or "", question["rubric"] or "",
                float(question["max_score"]),
                json.loads(question["parts"]) if question["parts"] else None,
            )

        # An empty response needs no AI call: UC-3 alternate flow 2 specifies a
        # score of zero with a default message. Skipping it also saves tokens.
        gradable = []
        for row in rows:
            if not (row["response_text"] or "").strip():
                conn.execute(
                    """INSERT INTO grading_result
                       (response_id, score, feedback_ar, model_name, error)
                       VALUES (?, 0, ?, ?, NULL)
                       ON CONFLICT(response_id) DO UPDATE SET
                           score = 0, feedback_ar = excluded.feedback_ar""",
                    (row["id"], EMPTY_RESPONSE_FEEDBACK, "no-response"),
                )
                conn.commit()
                _bump_progress(conn, assignment_id, 1)
            else:
                gradable.append(row)

        batch_size = max(1, int(app.config.get("GRADING_BATCH_SIZE", 10)))
        failed_permanently = None
        rate_limited = None

        # Batches never mix questions, since a batch shares one ideal answer.
        # Student IDs are unique within a question, so they still key results.
        batches = []
        for question_id in dict.fromkeys(r["question_id"] for r in gradable):
            group = [r for r in gradable if r["question_id"] == question_id]
            batches.extend((contexts[question_id], b) for b in _chunk(group, batch_size))

        for (ideal, rubric, max_score, parts), batch in batches:
            by_student = {r["student_id"]: r["id"] for r in batch}
            items = [ResponseItem(r["student_id"], r["response_text"]) for r in batch]

            try:
                results = _grade(grader, items, ideal, rubric, max_score, parts)
            except GraderRateLimitError as exc:
                # Do NOT split the batch here. The provider is refusing because
                # too many requests arrived; retrying each item separately would
                # send ten times more, burning quota that is often a daily
                # allowance. Stop cleanly instead and keep the uploaded data.
                results = [
                    GradeResult(i.student_id, None, "",
                                error="Not graded: provider rate limit reached")
                    for i in items
                ]
                rate_limited = str(exc)
            except (GraderError, GraderTransientError) as exc:
                # A batch can also fail for reasons specific to one response.
                # Here splitting is worth it, so a single bad row cannot cost
                # the other nine their grades.
                results = _grade_individually(
                    grader, items, ideal, rubric, max_score, parts, str(exc)
                )
                if isinstance(exc, GraderConfigError):
                    failed_permanently = str(exc)

            for result in results:
                response_id = by_student.get(result.student_id)
                if response_id is not None:
                    _save_result(conn, response_id, result, grader.name)
            conn.commit()
            _bump_progress(conn, assignment_id, len(batch))

            if failed_permanently or rate_limited:
                break

        if failed_permanently:
            _set_status(conn, assignment_id, "failed", failed_permanently)
            return "failed"

        if rate_limited:
            _set_status(
                conn,
                assignment_id,
                "failed",
                "The AI provider refused further requests because the account's "
                "rate limit or quota was reached. Grading stopped rather than "
                "retrying, which would only use more of the allowance. Your "
                "uploaded responses were kept -- wait for the quota to reset, or "
                "use a key with a higher limit, then grade again. Provider said: "
                + rate_limited[:200],
            )
            return "failed"

        _set_status(conn, assignment_id, "complete")
        return "complete"

    except Exception:  # noqa: BLE001 - a worker thread must not die silently
        app.logger.error("Grading job %s crashed:\n%s", assignment_id, traceback.format_exc())
        try:
            _set_status(
                conn,
                assignment_id,
                "failed",
                "An unexpected error stopped grading. Your uploaded responses "
                "were kept, so you can try grading again.",
            )
        except Exception:  # noqa: BLE001
            pass
        return "failed"
    finally:
        conn.close()


def _grade_individually(grader, items, ideal, rubric, max_score, parts, batch_error):
    """Grade items one by one after their batch failed."""
    from .grading.base import GradeResult

    results = []
    for item in items:
        try:
            results.extend(_grade(grader, [item], ideal, rubric, max_score, parts))
        except (GraderError, GraderTransientError) as exc:
            results.append(
                GradeResult(
                    item.student_id,
                    None,
                    "",
                    error="Grading failed: " + str(exc)[:200],
                )
            )
    if not results:
        results = [
            GradeResult(i.student_id, None, "", error="Grading failed: " + batch_error[:200])
            for i in items
        ]
    return results


def start_grading(app, assignment_id):
    """Run run_grading_job on a daemon thread and return it."""
    thread = threading.Thread(
        target=run_grading_job,
        args=(app, assignment_id),
        name="grading-" + str(assignment_id),
        daemon=True,
    )
    thread.start()
    return thread
