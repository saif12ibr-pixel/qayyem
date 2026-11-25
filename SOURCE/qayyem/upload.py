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

from . import bank
from .auth import login_required
from .db import get_db
from .settings import grading_readiness
from .i18n import gettext as _
from .jobs import run_grading_job, start_grading
from .parsing import ParseError, parse_submissions
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


def combined_rubric(subject, rubric):
    """The subject's grading guidelines followed by the question's own rubric."""
    parts = [subject["rubric"] if subject else None, rubric]
    return "\n".join(p for p in parts if p) or ""


def question_rubric(subject, rubric):
    """Remove the subject-wide guidance before storing a question's own rubric."""
    rubric = (rubric or "").strip()
    shared = (subject["rubric"] or "").strip() if subject else ""
    if shared and rubric.startswith(shared):
        rubric = rubric[len(shared):].lstrip("\n").strip()
    return rubric or None


def bank_form(subject, question, suffix=""):
    """Form values for grading one of a subject's bank questions."""
    form = {"rubric" + suffix: combined_rubric(subject, question["rubric"]),
            "max_score" + suffix: "%g" % question["max_score"],
            "question_text" + suffix: question["text"],
            "parts" + suffix: _parts_from_json(question["parts"])}
    if question["ideal_answer"]:
        form["ideal_answer" + suffix] = question["ideal_answer"]
        form["ideal_source" + suffix] = "text"
    return form


def save_bank_question(subject, exam, position, text, options, ideal_answer, rubric,
                       max_score, parts, question_id=None):
    """Save the reviewed question in its subject bank; return True if new."""
    db = get_db()
    rubric = question_rubric(subject, rubric)
    if question_id:
        db.execute(
            "UPDATE bank_question SET text = ?, ideal_answer = ?, rubric = ?, "
            "max_score = ?, parts = ? WHERE id = ? AND subject_id = ?",
            (text, ideal_answer, rubric, max_score, parts, question_id, subject["id"]),
        )
        return False
    db.execute(
        "INSERT INTO bank_question "
        "(subject_id, exam_type, position, text, options, ideal_answer, rubric, max_score, parts) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (subject["id"], exam, position, text, options, ideal_answer, rubric, max_score, parts),
    )
    return True


def _render(form, status=200):
    subject = bank.owned_subject(form.get("subject_id"), missing=None)
    exam = bank.exam_type(form.get("exam_type"))
    return render_template(
        "upload.html", form=form, readiness=_readiness(), subjects=bank.subjects(),
        subject=subject, exam_types=bank.EXAM_TYPES,
        counts=bank.exam_counts(subject["id"]) if subject else {},
        bank_questions=bank.questions(subject["id"], exam) if subject else [],
    ), status


@bp.route("/upload", methods=("GET", "POST"))
@login_required
def new():
    if request.method == "GET":
        # Which of the subject's exams is being graded, kept across the reload
        # that picking a subject, exam or bank question does.
        question_mode = request.args.get("question_mode", "single")
        if question_mode not in ("single", "multiple"):
            question_mode = "single"
        student_mode = request.args.get("student_mode", "multiple")
        if student_mode not in ("single", "multiple"):
            student_mode = "multiple"
        form = {
            "exam_type": bank.exam_type(request.args.get("exam")),
            "question_mode": question_mode,
            "student_mode": student_mode,
            "question_text": "",
        }
        subject = bank.owned_subject(request.args.get("subject", type=int), missing=None)
        if subject is not None:
            form.update(subject_id=subject["id"], rubric=subject["rubric"] or "")
            question_id = request.args.get("question", type=int)
            if question_id:
                question = bank.owned_question(subject["id"], question_id)
                form.update(bank_form(subject, question))
                form["bank_question"] = question["id"]
        return _render(form)

    subject = bank.owned_subject(request.form.get("subject_id", type=int), missing=None)
    question_mode = request.form.get("question_mode") or "auto"
    student_mode = request.form.get("student_mode") or "auto"
    bank_question = request.form.get("bank_question", type=int)
    if question_mode == "multiple":
        bank_question = None
    form = {
        "subject_id": subject["id"] if subject else None,
        "bank_question": bank_question,
        "ideal_answer": (request.form.get("ideal_answer") or "").strip(),
        "ideal_source": request.form.get("ideal_source"),
        "question_text": (request.form.get("question_text") or "").strip(),
        "rubric": (request.form.get("rubric") or "").strip(),
        "max_score": (request.form.get("max_score") or "10").strip(),
        "parts": _part_rows(),
        "exam_type": bank.exam_type(request.form.get("exam_type")),
        "question_mode": question_mode if question_mode in ("single", "multiple") else "single",
        "student_mode": student_mode if student_mode in ("single", "multiple") else "multiple",
    }
    # One class list, or several files at once (lists or answer papers).
    uploads = [f for f in request.files.getlist("file") if f and f.filename]

    errors = []
    if question_mode not in ("single", "multiple", "auto"):
        errors.append(_("Choose single question or multiple questions."))
        form["question_mode"] = "single"
    if student_mode not in ("single", "multiple", "auto"):
        errors.append(_("Choose one student or multiple students."))
        form["student_mode"] = "multiple"
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

    files = [(f.filename, f.read()) for f in uploads]
    for filename, data in files:
        if len(data) > MAX_UPLOAD_BYTES:
            errors.append(_("'%(name)s' is larger than 8 MB.", name=filename))

    exam = None
    if not errors:
        try:
            # Answer papers are split into as many answers as the chosen exam
            # of the bank has questions (unless one bank question is chosen).
            question_count = None
            if subject and not form["bank_question"] and question_mode == "auto":
                question_count = bank.exam_counts(subject["id"])[form["exam_type"]] or None
            elif subject and not form["bank_question"] and question_mode == "multiple":
                bank_count = bank.exam_counts(subject["id"])[form["exam_type"]]
                question_count = bank_count if bank_count > 1 else None
            exam = parse_submissions(
                files, max_rows=int(current_app.config.get("MAX_ROWS", 500)),
                question_count=question_count,
            )
        except ParseError as exc:
            errors.append(str(exc))

    if exam is not None:
        question_total = len(exam["questions"])
        if question_mode == "single" and question_total > 1:
            errors.append(_(
                "This upload contains multiple questions. Choose Multiple questions, "
                "or upload a single-question file."
            ))
        elif question_mode == "multiple" and question_total < 2:
            errors.append(_(
                "Only one question was found. Choose Single question, or upload an "
                "exam with at least two questions."
            ))
        student_total = len(exam["students"])
        if student_mode == "single" and student_total != 1:
            errors.append(_(
                "This upload contains %(count)s students. Choose Multiple students, "
                "or upload one student's responses.", count=student_total
            ))
        elif student_mode == "multiple" and student_total < 2:
            errors.append(_(
                "Only one student was found. Choose One student, or upload responses "
                "for at least two students."
            ))

    # A multi-question file gets its ideal answers on the next page, one per
    # question, so the single ideal answer on this page is not needed.
    multi = exam is not None and len(exam["questions"]) > 1
    ideal_answer = None
    if not multi and question_mode != "multiple":
        ideal_answer, error = _ideal_answer(
            form["ideal_answer"], request.files.get("reference"), form["ideal_source"]
        )
        if error:
            errors.append(error)
    if errors:
        for message in errors:
            flash(message, "danger")
        return _render(form, 400)

    parts_json = json.dumps(parts, ensure_ascii=False) if parts else None
    students = exam["students"]
    db = get_db()
    # Graded from a bank question: keep what it asked, for the review panel.
    banked = None
    if subject and form["bank_question"] and not multi:
        banked = db.execute(
            "SELECT * FROM bank_question WHERE id = ? AND subject_id = ? AND exam_type = ?",
            (form["bank_question"], subject["id"], form["exam_type"]),
        ).fetchone()
        if banked is None:
            abort(400)

    if subject and not multi and not form["question_text"]:
        form["question_text"] = banked["text"] if banked else exam["questions"][0]

    bank_saved = False
    if subject and not multi:
        question_text = form["question_text"] or (banked["text"] if banked else "")
        if not question_text:
            question_text = exam["questions"][0]
        bank_saved = save_bank_question(
            subject, form["exam_type"],
            banked["position"] if banked else bank.next_position(subject["id"], form["exam_type"]),
            question_text, banked["options"] if banked else None,
            ideal_answer, form["rubric"], max_score, parts_json,
            banked["id"] if banked else None,
        )

    cursor = db.execute(
        """INSERT INTO assignment
           (instructor_id, subject_id, title, ideal_answer, rubric, max_score, parts,
            question_text, question_options, exam_type, status, progress_total)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
        (
            g.instructor["id"],
            subject["id"] if subject else None,
            files[0][0] if len(files) == 1 else _(
                "%(first)s and %(count)s more", first=files[0][0], count=len(files) - 1),
            ideal_answer or "",
            form["rubric"] or None,
            max_score,
            None if multi else parts_json,
            form["question_text"] or (banked["text"] if banked else None),
            banked["options"] if banked else None,
            form["exam_type"] if subject else None,
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

    if bank_saved:
        flash(_("Added this question to the %(subject)s question bank.",
                subject=subject["name"]), "success")
    elif subject:
        flash(_("Saved this question to the %(subject)s question bank.",
                subject=subject["name"]), "success")
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

    # With a subject, question N of the file starts from question N of its bank.
    subject = bank.owned_subject(assignment["subject_id"], missing=None)
    banked = {}
    if subject is not None:
        exam = bank.exam_type(assignment["exam_type"])
        banked = {b["position"]: b for b in bank.questions(subject["id"], exam)}

    if request.method == "GET":
        form = {}
        for q in rows:
            suffix = "_" + str(q["id"])
            source = banked.get(q["position"])
            form["question_text" + suffix] = source["text"] if source else q["title"]
            form["rubric" + suffix] = q["rubric"] or ""
            form["max_score" + suffix] = "%g" % q["max_score"]
            form["parts" + suffix] = _parts_from_json(q["parts"])
            if source:
                form.update(bank_form(subject, source, suffix))
        return render_template(
            "questions.html", assignment=assignment, questions=rows, form=form,
            subject=subject, banked=banked,
        )

    form = {key: (value or "").strip() for key, value in request.form.items()}
    errors = []
    updates = []
    bank_updates = []
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
        source = banked.get(q["position"])
        question_text = form.get("question_text" + suffix, "").strip()
        if not question_text:
            question_text = source["text"] if source else q["title"]
        rubric = form.get("rubric" + suffix) or None
        parts_json = json.dumps(parts, ensure_ascii=False) if parts else None
        updates.append((
            ideal, rubric, max_score, parts_json, question_text,
            source["options"] if source else None,
            q["id"],
        ))
        if subject and question_text:
            bank_updates.append((
                q["position"], question_text, source["options"] if source else None,
                ideal, rubric, max_score, parts_json, source["id"] if source else None,
            ))

    if errors:
        for message in errors:
            flash(message, "danger")
        return render_template(
            "questions.html", assignment=assignment, questions=rows, form=form,
            subject=subject, banked=banked,
        ), 400

    db.executemany(
        "UPDATE question SET ideal_answer = ?, rubric = ?, max_score = ?, parts = ?, "
        "question_text = ?, question_options = ? WHERE id = ?",
        updates,
    )
    for position, text, options, ideal, rubric, max_score, parts_json, question_id in bank_updates:
        save_bank_question(
            subject, bank.exam_type(assignment["exam_type"]), position, text, options,
            ideal, rubric, max_score, parts_json, question_id,
        )
    # The assignment's maximum is the whole exam's, so totals read against it.
    db.execute(
        "UPDATE assignment SET max_score = ? WHERE id = ?",
        (sum(u[2] for u in updates), assignment_id),
    )
    db.commit()
    if subject:
        flash(_("Saved the reviewed questions to the %(subject)s question bank.",
                subject=subject["name"]), "success")
    return _start(assignment_id, assignment["progress_total"])
