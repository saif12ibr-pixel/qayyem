"""Upload and start grading (UC-2, and the trigger for UC-3)."""
import json

from flask import (
    Blueprint,
    abort,
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
from .i18n import gettext as _
from .jobs import run_grading_job, start_grading
from .parsing import ParseError, parse_exam
from .reference import extract_reference_text

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


IDEAL_SOURCES = ("text", "file", "both")
MAX_PARTS = 6


def _ideal_answer(typed, reference, source=None):
    """The ideal answer from the typed text, a book or slides file, or both.

    `source` is the instructor's choice of "text", "file" or "both"; only that
    input is used, so a file left selected after switching back to a typed
    answer cannot slip into the grading. Without a choice, whatever was
    supplied is used.

    Returns (text, error); exactly one of them is set.
    """
    has_file = bool(reference and reference.filename)
    if source == "text":
        has_file = False
    elif source == "file":
        typed = ""
        if not has_file:
            return None, _("Choose a book or slides file to use as the ideal answer.")
    elif source == "both" and not (typed and has_file):
        return None, _("You chose both: type the ideal answer and choose a book or slides file.")

    reference_text = ""
    if has_file:
        try:
            reference_text = extract_reference_text(reference.filename, reference.read())
        except ParseError as exc:
            return None, str(exc)

    if not typed and not reference_text:
        return None, _(
            "Enter the ideal answer, or upload a book or slides file, that student "
            "responses are compared against."
        )

    # The typed answer leads; the uploaded material backs it up.
    if not reference_text:
        return typed, None
    return (
        (typed + "\n\n" if typed else "")
        + "Reference material (" + reference.filename + "):\n" + reference_text
    ), None


def _max_score(raw):
    """Returns (value, error); exactly one of them is set."""
    try:
        value = float(raw)
        if value <= 0 or value > 1000:
            raise ValueError
    except ValueError:
        return None, _("Maximum score must be a number between 0 and 1000.")
    return value, None


def _part_rows(suffix=""):
    """The marking-scheme rows as typed, blank rows dropped, for re-display."""
    names = request.form.getlist("part_name" + suffix)
    marks = request.form.getlist("part_marks" + suffix)
    rows = [((n or "").strip(), (m or "").strip()) for n, m in zip(names, marks)]
    return [row for row in rows if row[0] or row[1]]


def _parts(rows):
    """Validate marking-scheme rows. Returns (parts or None, error)."""
    if not rows:
        return None, None
    if len(rows) == 1:
        return None, _("Split the marks into at least two parts, or remove the part.")
    if len(rows) > MAX_PARTS:
        return None, _("A question can have at most %(count)s parts.", count=MAX_PARTS)
    parts = []
    for name, raw_marks in rows:
        try:
            marks = float(raw_marks)
        except ValueError:
            marks = 0
        if not name or marks <= 0:
            return None, _("Each part needs a name and marks greater than 0.")
        parts.append({"name": name, "marks": marks})
    if sum(p["marks"] for p in parts) > 1000:
        return None, _("Maximum score must be a number between 0 and 1000.")
    return parts, None


def _parts_from_json(raw):
    return [(p["name"], "%g" % p["marks"]) for p in json.loads(raw)] if raw else []


def _start(assignment_id, response_count):
    application = current_app._get_current_object()
    if application.config.get("GRADING_SYNC"):
        # Tests grade inline so assertions do not race a worker thread.
        run_grading_job(application, assignment_id)
    else:
        start_grading(application, assignment_id)

    flash(
        _("Grading %(count)s response(s). This page updates as it runs.", count=response_count),
        "info",
    )
    return redirect(url_for("results.detail", assignment_id=assignment_id))


@bp.route("/upload", methods=("GET", "POST"))
@login_required
def new():
    if request.method == "GET":
        return render_template("upload.html", form={}, readiness=_readiness())

    form = {
        "ideal_answer": (request.form.get("ideal_answer") or "").strip(),
        "ideal_source": request.form.get("ideal_source"),
        "rubric": (request.form.get("rubric") or "").strip(),
        "max_score": (request.form.get("max_score") or "10").strip(),
        "parts": _part_rows(),
    }
    upload = request.files.get("file")

    errors = []
    parts, error = _parts(form["parts"])
    if error:
        errors.append(error)
    if parts:
        # Marked in parts: the maximum is their sum, whatever the box says.
        max_score = sum(p["marks"] for p in parts)
    else:
        max_score, error = _max_score(form["max_score"])
        if error:
            errors.append(error)

    data = upload.read() if upload else b""
    if len(data) > MAX_UPLOAD_BYTES:
        errors.append(_("That file is larger than 8 MB."))

    exam = None
    if not errors:
        try:
            exam = parse_exam(
                upload.filename if upload else "",
                data,
                max_rows=int(current_app.config.get("MAX_ROWS", 500)),
            )
        except ParseError as exc:
            errors.append(str(exc))

    # A multi-question file gets its ideal answers on the next page, one per
    # question, so the single ideal answer on this page is not needed.
    multi = exam is not None and len(exam["questions"]) > 1
    ideal_answer = None
    if not multi:
        ideal_answer, error = _ideal_answer(
            form["ideal_answer"], request.files.get("reference"), form["ideal_source"]
        )
        if error:
            errors.append(error)

    if errors:
        for message in errors:
            flash(message, "danger")
        return render_template("upload.html", form=form, readiness=_readiness()), 400

    parts_json = json.dumps(parts, ensure_ascii=False) if parts else None
    students = exam["students"]
    db = get_db()
    cursor = db.execute(
        """INSERT INTO assignment
           (instructor_id, title, ideal_answer, rubric, max_score, parts, status,
            progress_total)
           VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
        (
            g.instructor["id"],
            upload.filename,
            ideal_answer or "",
            form["rubric"] or None,
            max_score,
            None if multi else parts_json,
            len(students) * len(exam["questions"]),
        ),
    )
    assignment_id = cursor.lastrowid

    for position, title in enumerate(exam["questions"]):
        question_id = None
        if multi:
            # The rubric, max score and parts typed on this page become each
            # question's starting values on the next, where any can differ.
            question_id = db.execute(
                "INSERT INTO question (assignment_id, position, title, rubric, max_score, parts) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (assignment_id, position + 1, title, form["rubric"] or None, max_score,
                 parts_json),
            ).lastrowid
        db.executemany(
            "INSERT INTO student_response "
            "(assignment_id, question_id, student_id, response_text, row_number) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (assignment_id, question_id, s["student_id"], s["answers"][position],
                 s["row_number"])
                for s in students
            ],
        )
    db.commit()

    if multi:
        flash(
            _("This file has %(count)s questions. Give each one its ideal answer and "
              "maximum score, then start grading.", count=len(exam["questions"])),
            "info",
        )
        return redirect(url_for("upload.questions", assignment_id=assignment_id))

    return _start(assignment_id, len(students))


@bp.route("/upload/<int:assignment_id>/questions", methods=("GET", "POST"))
@login_required
def questions(assignment_id):
    """Per-question ideal answers, rubrics and maximum scores for an exam file."""
    db = get_db()
    assignment = db.execute(
        "SELECT * FROM assignment WHERE id = ? AND instructor_id = ?",
        (assignment_id, g.instructor["id"]),
    ).fetchone()
    if assignment is None:
        abort(404)
    if assignment["status"] != "pending":
        return redirect(url_for("results.detail", assignment_id=assignment_id))

    rows = db.execute(
        "SELECT * FROM question WHERE assignment_id = ? ORDER BY position",
        (assignment_id,),
    ).fetchall()
    if not rows:
        abort(404)

    if request.method == "GET":
        form = {}
        for q in rows:
            suffix = "_" + str(q["id"])
            form["rubric" + suffix] = q["rubric"] or ""
            form["max_score" + suffix] = "%g" % q["max_score"]
            form["parts" + suffix] = _parts_from_json(q["parts"])
        return render_template(
            "questions.html", assignment=assignment, questions=rows, form=form
        )

    form = {key: (value or "").strip() for key, value in request.form.items()}
    errors = []
    updates = []
    for q in rows:
        suffix = "_" + str(q["id"])
        form["parts" + suffix] = _part_rows(suffix)
        ideal, ideal_error = _ideal_answer(
            form.get("ideal_answer" + suffix, ""),
            request.files.get("reference" + suffix),
            form.get("ideal_source" + suffix),
        )
        parts, parts_error = _parts(form["parts" + suffix])
        score_error = None
        if parts:
            max_score = sum(p["marks"] for p in parts)
        else:
            max_score, score_error = _max_score(form.get("max_score" + suffix, ""))
        for error in (ideal_error, parts_error, score_error):
            if error:
                errors.append(_(
                    "Question %(number)s (%(title)s): %(error)s",
                    number=q["position"], title=q["title"], error=error,
                ))
        updates.append((
            ideal, form.get("rubric" + suffix) or None, max_score,
            json.dumps(parts, ensure_ascii=False) if parts else None, q["id"],
        ))

    if errors:
        for message in errors:
            flash(message, "danger")
        return render_template(
            "questions.html", assignment=assignment, questions=rows, form=form
        ), 400

    db.executemany(
        "UPDATE question SET ideal_answer = ?, rubric = ?, max_score = ?, parts = ? "
        "WHERE id = ?",
        updates,
    )
    # The assignment's maximum is the whole exam's, so totals read against it.
    db.execute(
        "UPDATE assignment SET max_score = ? WHERE id = ?",
        (sum(u[2] for u in updates), assignment_id),
    )
    db.commit()
    return _start(assignment_id, assignment["progress_total"])
