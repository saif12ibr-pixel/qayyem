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
    request,
    url_for,
)

from .auth import login_required
from .db import get_db
from .export import (
    attachment_header,
    build_student_workbook,
    build_workbook,
    filename_for,
    student_filename_for,
    format_breakdown,
    format_score,
)
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
        """SELECT sr.id AS response_id, sr.student_id, sr.response_text, sr.row_number,
                  sr.question_id, gr.score, gr.feedback_ar, gr.model_name, gr.error,
                  gr.part_scores, gr.reviewed_at, gr.ai_score
           FROM student_response sr
           LEFT JOIN grading_result gr ON gr.response_id = sr.id
           LEFT JOIN question q ON q.id = sr.question_id
           WHERE sr.assignment_id = ?
           ORDER BY sr.row_number, q.position""",
        (assignment_id,),
    ).fetchall()


def _asked(row, title):
    """What the student was asked, for the review panel: {"text", "options"},
    the file's column heading when the question itself was not kept, or None."""
    text = row["question_text"] or title
    if not text:
        return None
    options = json.loads(row["question_options"]) if row["question_options"] else []
    return {"text": text, "options": options}


def with_breakdown(rows, assignment, questions):
    """Rows as dicts, each with "breakdown": [{"name", "score", "marks"}] for a
    question marked in parts, and an empty list otherwise. Each also carries
    its question's "scheme" and "max_score", which the review form needs."""
    schemes = {None: json.loads(assignment["parts"]) if assignment["parts"] else None}
    maxes = {None: assignment["max_score"]}
    asked = {None: _asked(assignment, None)}
    for q in questions:
        schemes[q["id"]] = json.loads(q["parts"]) if q["parts"] else None
        maxes[q["id"]] = q["max_score"]
        asked[q["id"]] = _asked(q, q["title"])

    result = []
    for row in rows:
        entry = dict(row)
        scheme = schemes.get(row["question_id"])
        entry["scheme"] = scheme or []
        entry["max_score"] = maxes.get(row["question_id"], assignment["max_score"])
        entry["question"] = asked.get(row["question_id"])
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


# Performance bands, as a percentage of the maximum score.
HIGH_PERCENT = 80
LOW_PERCENT = 50
TOP_COUNT = 5


def _percent(score, max_score):
    return round(score / max_score * 100, 1) if score is not None and max_score else None


def _band(percent):
    if percent >= HIGH_PERCENT:
        return "high"
    return "average" if percent >= LOW_PERCENT else "low"


def student_summaries(rows, assignment, questions):
    """One summary per student, for the class overview and the student search.

    Each has the student's total and percentage, the average percentage over
    their questions, their best question, and their answers. Students with a
    missing score are kept (for the search) but get no percentage, rank or band.
    """
    titles = {q["id"]: _("Q%(n)s", n=q["position"]) for q in questions}
    summaries = []
    for student in group_by_student(rows):
        answers = []
        for a in student["answers"]:
            answers.append(dict(a, label=titles.get(a["question_id"], _("Answer")),
                                percent=_percent(a["score"], a["max_score"])))
        scored = [a for a in answers if a["percent"] is not None]
        complete = student["total"] is not None
        percent = _percent(student["total"], assignment["max_score"]) if complete else None
        summaries.append({
            "student_id": student["student_id"],
            "total": student["total"],
            "max_score": assignment["max_score"],
            "percent": percent,
            "average_percent": (round(sum(a["percent"] for a in scored) / len(scored), 1)
                                if complete and scored else None),
            "best": max(scored, key=lambda a: a["percent"]) if complete and len(answers) > 1 else None,
            "band": _band(percent) if complete else None,
            "rank": None,
            "answers": answers,
        })
    ranked = sorted((s for s in summaries if s["percent"] is not None),
                    key=lambda s: s["percent"], reverse=True)
    for position, s in enumerate(ranked, start=1):
        s["rank"] = position
    return summaries, ranked


def class_overview(ranked):
    """The top students and the low / average / high groups, lowest first."""
    if not ranked:
        return None
    lowest_first = list(reversed(ranked))
    return {
        "top": ranked[:TOP_COUNT],
        "graded": len(ranked),
        "highest": ranked[0],
        "lowest": ranked[-1],
        "bands": [(band, [s for s in lowest_first if s["band"] == band])
                  for band in ("low", "average", "high")],
    }


@bp.route("/")
@login_required
def index():
    rows = get_db().execute(
        """SELECT a.*, s.name AS subject_name,
                  (SELECT COUNT(*) FROM student_response sr WHERE sr.assignment_id = a.id)
                      AS response_count,
                  (SELECT COUNT(*) FROM question q
                    WHERE q.assignment_id = a.id AND q.ideal_answer IS NULL)
                      AS question_count
           FROM assignment a
           LEFT JOIN subject s ON s.id = a.subject_id
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
        "reviewed": sum(1 for r in rows if r["reviewed_at"]),
    }
    subject = None
    if assignment["subject_id"]:
        subject = get_db().execute("SELECT * FROM subject WHERE id = ?",
                                   (assignment["subject_id"],)).fetchone()
    summaries, ranked = student_summaries(rows, assignment, questions)
    return render_template(
        "results.html", assignment=assignment, rows=rows, summary=summary,
        questions=questions, students=students, subject=subject,
        editable=assignment["status"] in ("complete", "failed"),
        summaries=summaries, overview=class_overview(ranked),
        bands={"low": LOW_PERCENT, "high": HIGH_PERCENT},
    )


def _number(raw, low, high):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if low <= value <= high else None


@bp.route("/<int:assignment_id>/responses/<int:response_id>", methods=("POST",))
@login_required
def review(assignment_id, response_id):
    """The instructor's own grade for one answer, replacing the model's.

    The model's score is kept in ai_score, so the change stays on record, and
    the result set is marked as not downloaded again, since any Excel file
    taken before now is out of date.
    """
    assignment = _owned_assignment(assignment_id)
    back = redirect(url_for("results.detail", assignment_id=assignment_id)
                    + "#r" + str(response_id))
    if assignment["status"] not in ("complete", "failed"):
        flash(_("Wait for grading to finish before changing grades."), "warning")
        return back

    db = get_db()
    response = db.execute(
        "SELECT * FROM student_response WHERE id = ? AND assignment_id = ?",
        (response_id, assignment_id),
    ).fetchone()
    if response is None:
        abort(404)
    question = None
    if response["question_id"] is not None:
        question = db.execute("SELECT * FROM question WHERE id = ?",
                              (response["question_id"],)).fetchone()
    owner = question or assignment
    max_score = owner["max_score"]
    scheme = json.loads(owner["parts"]) if owner["parts"] else None

    part_scores = None
    if scheme:
        raw = request.form.getlist("part_score")
        part_scores = [_number(value, 0, p["marks"]) for value, p in zip(raw, scheme)]
        if len(raw) != len(scheme) or None in part_scores:
            flash(_("Each part's score must be between 0 and its marks."), "danger")
            return back
        score = round(sum(part_scores), 2)
    else:
        score = _number(request.form.get("score"), 0, max_score)
        if score is None:
            flash(_("The score must be between 0 and %(max)s.", max=format_score(max_score)),
                  "danger")
            return back
    feedback = (request.form.get("feedback_ar") or "").strip() or None
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    parts_json = json.dumps(part_scores) if part_scores is not None else None

    existing = db.execute("SELECT * FROM grading_result WHERE response_id = ?",
                          (response_id,)).fetchone()
    if existing is None:
        db.execute(
            "INSERT INTO grading_result (response_id, score, feedback_ar, part_scores, "
            "reviewed_at) VALUES (?, ?, ?, ?, ?)",
            (response_id, score, feedback, parts_json, now),
        )
    else:
        ai_score = existing["ai_score"] if existing["reviewed_at"] else existing["score"]
        db.execute(
            "UPDATE grading_result SET score = ?, feedback_ar = ?, part_scores = ?, "
            "error = NULL, reviewed_at = ?, ai_score = ? WHERE response_id = ?",
            (score, feedback, parts_json, now, ai_score, response_id),
        )
    db.execute("UPDATE assignment SET exported_at = NULL WHERE id = ?", (assignment_id,))
    db.commit()
    flash(_("Saved the grade for %(student)s.", student=response["student_id"]), "success")
    return back


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

    return _xlsx(payload, filename_for(assignment))


def _xlsx(payload, filename):
    return Response(
        payload,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": attachment_header(filename),
            "Content-Length": str(len(payload)),
        },
    )


@bp.route("/<int:assignment_id>/student.xlsx")
@login_required
def export_student(assignment_id):
    """One student's answers, scores, feedback and averages as Excel.

    This does not count as downloading the result set: the class's grades are
    still deleted at sign-out unless the full Excel file is taken.
    """
    assignment = _owned_assignment(assignment_id)
    if assignment["status"] != "complete":
        flash(_("Grading is not finished yet, so there is nothing to download."), "warning")
        return redirect(url_for("results.detail", assignment_id=assignment_id))

    questions = _questions(assignment_id)
    rows = with_breakdown(_result_rows(assignment_id), assignment, questions)
    summaries, ranked = student_summaries(rows, assignment, questions)
    wanted = (request.args.get("student") or "").strip()
    student = next((s for s in summaries if s["student_id"] == wanted), None)
    if student is None:
        abort(404)
    payload = build_student_workbook(assignment, student, len(ranked))
    return _xlsx(payload, student_filename_for(assignment, student["student_id"]))
