"""Results dashboard, progress polling, and Excel download (UC-4, UC-5)."""
import json
from datetime import datetime, timezone

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    url_for,
)

from .auth import login_required
from .db import get_db
from .export import build_workbook, filename_for, format_breakdown, format_score
from .i18n import gettext as _

bp = Blueprint("results", __name__, url_prefix="/results")
bp.add_app_template_filter(format_score, "score")
bp.add_app_template_filter(format_breakdown, "breakdown")


def _owned_assignment(assignment_id):
    """Fetch an assignment, or 404 unless the signed-in instructor owns it.

    The ownership test is the control that satisfies SS 4.3.2 ("must not expose
    student response data to unauthorized users"). Without it, any signed-in
    instructor could read another's results by changing the id in the URL.
    """
    row = get_db().execute(
        "SELECT * FROM assignment WHERE id = ? AND instructor_id = ?",
        (assignment_id, g.instructor["id"]),
    ).fetchone()
    if row is None:
        abort(404)
    return row


def _result_rows(assignment_id):
    return get_db().execute(
        """SELECT sr.student_id, sr.response_text, sr.row_number, sr.question_id,
                  gr.score, gr.feedback_ar, gr.model_name, gr.error, gr.part_scores
           FROM student_response sr
           LEFT JOIN grading_result gr ON gr.response_id = sr.id
           LEFT JOIN question q ON q.id = sr.question_id
           WHERE sr.assignment_id = ?
           ORDER BY sr.row_number, q.position""",
        (assignment_id,),
    ).fetchall()


def with_breakdown(rows, assignment, questions):
    """Rows as dicts, each with "breakdown": [{"name", "score", "marks"}] for a
    question marked in parts, and an empty list otherwise."""
    schemes = {None: json.loads(assignment["parts"]) if assignment["parts"] else None}
    for q in questions:
        schemes[q["id"]] = json.loads(q["parts"]) if q["parts"] else None

    result = []
    for row in rows:
        entry = dict(row)
        scheme = schemes.get(row["question_id"])
        scores = json.loads(row["part_scores"]) if row["part_scores"] else None
        entry["breakdown"] = (
            [{"name": p["name"], "score": s, "marks": p["marks"]}
             for p, s in zip(scheme, scores)]
            if scheme and scores else []
        )
        result.append(entry)
    return result


def _questions(assignment_id):
    """The questions of a multi-question assignment; empty for a single one."""
    return get_db().execute(
        "SELECT * FROM question WHERE assignment_id = ? ORDER BY position",
        (assignment_id,),
    ).fetchall()


def group_by_student(rows):
    """One entry per student: their answers in question order and their total.

    The total is None until every answer has a score, so a half-graded exam is
    never shown as a low mark.
    """
    students = {}
    for row in rows:
        entry = students.setdefault(row["student_id"], {"student_id": row["student_id"],
                                                        "answers": []})
        entry["answers"].append(row)
    for entry in students.values():
        scores = [a["score"] for a in entry["answers"]]
        entry["total"] = None if None in scores else round(sum(scores), 2)
    return list(students.values())


@bp.route("/")
@login_required
def index():
    rows = get_db().execute(
        """SELECT a.*,
                  (SELECT COUNT(*) FROM student_response sr WHERE sr.assignment_id = a.id)
                      AS response_count,
                  (SELECT COUNT(*) FROM question q
                    WHERE q.assignment_id = a.id AND q.ideal_answer IS NULL)
                      AS question_count
           FROM assignment a
           WHERE a.instructor_id = ?
           ORDER BY a.created_at DESC, a.id DESC""",
        (g.instructor["id"],),
    ).fetchall()
    return render_template("results_index.html", assignments=rows)


@bp.route("/<int:assignment_id>")
@login_required
def detail(assignment_id):
    assignment = _owned_assignment(assignment_id)
    questions = _questions(assignment_id)
    if assignment["status"] == "pending" and questions and questions[0]["ideal_answer"] is None:
        # An exam file whose questions have not been set up yet.
        return redirect(url_for("upload.questions", assignment_id=assignment_id))

    rows = with_breakdown(_result_rows(assignment_id), assignment, questions)
    students = group_by_student(rows) if questions else []
    if questions:
        scored = [s["total"] for s in students if s["total"] is not None]
        total = len(students)
    else:
        scored = [r["score"] for r in rows if r["score"] is not None]
        total = len(rows)
    summary = {
        "total": total,
        "graded": len(scored),
        "failed": sum(1 for r in rows if r["error"]),
        "average": round(sum(scored) / len(scored), 2) if scored else None,
    }
    return render_template(
        "results.html", assignment=assignment, rows=rows, summary=summary,
        questions=questions, students=students,
    )


@bp.route("/<int:assignment_id>/status")
@login_required
def status(assignment_id):
    """Progress for the polling indicator required by UC-3."""
    assignment = _owned_assignment(assignment_id)
    return jsonify(
        {
            "status": assignment["status"],
            "done": assignment["progress_done"],
            "total": assignment["progress_total"],
            "error": assignment["error_message"],
        }
    )


@bp.route("/<int:assignment_id>/export.xlsx")
@login_required
def export(assignment_id):
    assignment = _owned_assignment(assignment_id)

    if assignment["status"] != "complete":
        # UC-5 alternate flow: downloading before grading finishes.
        flash(_("Grading is not finished yet, so there is nothing to download."), "warning")
        return redirect(url_for("results.detail", assignment_id=assignment_id))

    questions = _questions(assignment_id)
    rows = with_breakdown(_result_rows(assignment_id), assignment, questions)
    payload = build_workbook(assignment, rows, questions)

    db = get_db()
    db.execute(
        "UPDATE assignment SET exported_at = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"), assignment_id),
    )
    db.commit()

    return Response(
        payload,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="' + filename_for(assignment) + '"',
            "Content-Length": str(len(payload)),
        },
    )
