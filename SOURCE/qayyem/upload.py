"""Upload and start grading (UC-2, and the trigger for UC-3)."""
from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from .auth import login_required
from .db import get_db
from .settings import grading_readiness
from .jobs import run_grading_job, start_grading
from .parsing import ParseError, parse_responses

bp = Blueprint("upload", __name__)

MAX_UPLOAD_BYTES = 8 * 1024 * 1024


@bp.route("/", methods=("GET",))
@login_required
def home():
    return redirect(url_for("upload.new"))


def _readiness():
    """Whether the signed-in instructor has a usable provider and key."""
    row = get_db().execute(
        "SELECT * FROM instructor WHERE id = ?", (g.instructor["id"],)
    ).fetchone()
    return grading_readiness(current_app.config, row)


@bp.route("/upload", methods=("GET", "POST"))
@login_required
def new():
    if request.method == "GET":
        return render_template("upload.html", form={}, readiness=_readiness())

    form = {
        "ideal_answer": (request.form.get("ideal_answer") or "").strip(),
        "rubric": (request.form.get("rubric") or "").strip(),
        "max_score": (request.form.get("max_score") or "10").strip(),
    }
    upload = request.files.get("file")

    errors = []
    if not form["ideal_answer"]:
        errors.append("Enter the ideal answer that student responses are compared against.")

    try:
        max_score = float(form["max_score"])
        if max_score <= 0 or max_score > 1000:
            raise ValueError
    except ValueError:
        max_score = None
        errors.append("Maximum score must be a number between 0 and 1000.")

    data = upload.read() if upload else b""
    if len(data) > MAX_UPLOAD_BYTES:
        errors.append("That file is larger than 8 MB.")

    responses = []
    if not errors:
        try:
            responses = parse_responses(
                upload.filename if upload else "",
                data,
                max_rows=int(current_app.config.get("MAX_ROWS", 500)),
            )
        except ParseError as exc:
            errors.append(str(exc))

    if errors:
        for message in errors:
            flash(message, "danger")
        return render_template("upload.html", form=form, readiness=_readiness()), 400

    db = get_db()
    cursor = db.execute(
        """INSERT INTO assignment
           (instructor_id, title, ideal_answer, rubric, max_score, status, progress_total)
           VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
        (
            g.instructor["id"],
            upload.filename,
            form["ideal_answer"],
            form["rubric"] or None,
            max_score,
            len(responses),
        ),
    )
    assignment_id = cursor.lastrowid

    db.executemany(
        "INSERT INTO student_response (assignment_id, student_id, response_text, row_number) "
        "VALUES (?, ?, ?, ?)",
        [
            (assignment_id, r["student_id"], r["response_text"], r["row_number"])
            for r in responses
        ],
    )
    db.commit()

    application = current_app._get_current_object()
    if application.config.get("GRADING_SYNC"):
        # Tests grade inline so assertions do not race a worker thread.
        run_grading_job(application, assignment_id)
    else:
        start_grading(application, assignment_id)

    flash(
        "Grading " + str(len(responses)) + " response(s). This page updates as it runs.",
        "info",
    )
    return redirect(url_for("results.detail", assignment_id=assignment_id))
