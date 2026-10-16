"""Results dashboard, progress polling, and Excel download (UC-4, UC-5)."""
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
from .export import build_workbook, filename_for

bp = Blueprint("results", __name__, url_prefix="/results")


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
        """SELECT sr.student_id, sr.response_text, sr.row_number,
                  gr.score, gr.feedback_ar, gr.model_name, gr.error
           FROM student_response sr
           LEFT JOIN grading_result gr ON gr.response_id = sr.id
           WHERE sr.assignment_id = ?
           ORDER BY sr.row_number""",
        (assignment_id,),
    ).fetchall()


@bp.route("/")
@login_required
def index():
    rows = get_db().execute(
        """SELECT a.*,
                  (SELECT COUNT(*) FROM student_response sr WHERE sr.assignment_id = a.id)
                      AS response_count
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
    rows = _result_rows(assignment_id)
    scored = [r["score"] for r in rows if r["score"] is not None]
    summary = {
        "total": len(rows),
        "graded": len(scored),
        "failed": sum(1 for r in rows if r["error"]),
        "average": round(sum(scored) / len(scored), 2) if scored else None,
    }
    return render_template(
        "results.html", assignment=assignment, rows=rows, summary=summary
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
        flash("Grading is not finished yet, so there is nothing to download.", "warning")
        return redirect(url_for("results.detail", assignment_id=assignment_id))

    rows = _result_rows(assignment_id)
    payload = build_workbook(assignment, rows)

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
