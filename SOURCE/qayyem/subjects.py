"""Subjects: each course the instructor teaches, with its own question bank,
grading guidelines and grading sessions.

Questions are typed in, or imported from the Word file the exam was written
in: the instructor's AI model picks the questions out of it (question_ai.py),
or, without one, its numbering does (question_doc.py), and the bank downloads as an Excel sheet with the
correct answers starred. Grading a subject's answers starts from its bank, so
ideal answers and marks are not retyped for every class.
"""
import json

from flask import (
    Blueprint,
    Response,
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
from .export import attachment_header, build_bank_workbook, safe_filename
from .i18n import gettext as _
from .parsing import ParseError
from .question_ai import read_questions
from .question_doc import ideal_from_options, parse_option_lines
from .settings import grader_for_instructor
from .upload import MAX_UPLOAD_BYTES, _max_score, _part_rows, _parts, _parts_from_json

bp = Blueprint("subjects", __name__, url_prefix="/subjects")
bp.add_app_template_filter(json.loads, "fromjson")

MAX_SUBJECTS = 100


def _subject_form():
    return {
        "name": (request.form.get("name") or "").strip()[:120],
        "code": (request.form.get("code") or "").strip()[:30],
        "rubric": (request.form.get("rubric") or "").strip(),
    }


@bp.route("/", methods=("GET", "POST"))
@login_required
def index():
    rows = bank.subjects()
    if request.method == "POST":
        form = _subject_form()
        if not form["name"]:
            flash(_("Give the subject a name."), "danger")
            return render_template("subjects.html", subjects=rows, form=form), 400
        if len(rows) >= MAX_SUBJECTS:
            flash(_("You can have at most %(count)s subjects.", count=MAX_SUBJECTS), "danger")
            return render_template("subjects.html", subjects=rows, form=form), 400
        db = get_db()
        subject_id = db.execute(
            "INSERT INTO subject (instructor_id, name, code, rubric) VALUES (?, ?, ?, ?)",
            (g.instructor["id"], form["name"], form["code"] or None, form["rubric"] or None),
        ).lastrowid
        db.commit()
        flash(_("Subject “%(name)s” created. Add its questions, or import them from Word.",
                name=form["name"]), "success")
        return redirect(url_for("subjects.detail", subject_id=subject_id))
    return render_template("subjects.html", subjects=rows, form={})


@bp.route("/<int:subject_id>")
@login_required
def detail(subject_id):
    subject = bank.owned_subject(subject_id)
    exam = bank.exam_type(request.args.get("exam"))
    search = (request.args.get("q") or "").strip()
    question_type = request.args.get("type", "all")
    if question_type not in ("all", "msq", "open"):
        question_type = "all"
    all_questions = bank.questions(subject_id, exam)
    msq_ids = {q["id"] for q in all_questions if bank.options(q)}
    type_counts = {
        "all": len(all_questions),
        "msq": len(msq_ids),
        "open": len(all_questions) - len(msq_ids),
    }
    questions = all_questions
    if question_type == "msq":
        questions = [q for q in questions if q["id"] in msq_ids]
    elif question_type == "open":
        questions = [q for q in questions if q["id"] not in msq_ids]
    if search:
        needle = search.casefold()
        questions = [q for q in questions if needle in (
            q["text"] + " " + (q["ideal_answer"] or "") + " " + (q["options"] or "")
        ).casefold()]
    sessions = get_db().execute(
        """SELECT a.*,
                  (SELECT COUNT(*) FROM student_response sr WHERE sr.assignment_id = a.id)
                      AS response_count
           FROM assignment a
           WHERE a.subject_id = ? AND a.instructor_id = ?
           ORDER BY a.created_at DESC, a.id DESC""",
        (subject_id, g.instructor["id"]),
    ).fetchall()
    return render_template(
        "subject.html", subject=subject, questions=questions,
        options={q["id"]: bank.options(q) for q in questions},
        total=sum(q["max_score"] for q in questions), sessions=sessions,
        exam=exam, exam_types=bank.EXAM_TYPES, counts=bank.exam_counts(subject_id),
        search=search, question_type=question_type, type_counts=type_counts,
        type_labels={"all": _("All"), "msq": _("MSQ"), "open": _("Open question")},
    )


@bp.route("/<int:subject_id>/edit", methods=("POST",))
@login_required
def edit(subject_id):
    bank.owned_subject(subject_id)
    form = _subject_form()
    if not form["name"]:
        flash(_("Give the subject a name."), "danger")
    else:
        db = get_db()
        db.execute("UPDATE subject SET name = ?, code = ?, rubric = ? WHERE id = ?",
                   (form["name"], form["code"] or None, form["rubric"] or None, subject_id))
        db.commit()
        flash(_("Subject saved."), "success")
    return redirect(url_for("subjects.detail", subject_id=subject_id))


@bp.route("/<int:subject_id>/delete", methods=("POST",))
@login_required
def delete(subject_id):
    subject = bank.owned_subject(subject_id)
    db = get_db()
    db.execute("DELETE FROM subject WHERE id = ?", (subject_id,))
    db.commit()
    flash(_("Subject “%(name)s” and its question bank were deleted.", name=subject["name"]),
          "success")
    return redirect(url_for("subjects.index"))


@bp.route("/<int:subject_id>/import", methods=("POST",))
@login_required
def import_word(subject_id):
    """Add the questions of an exam written in Word to one exam of the bank."""
    bank.owned_subject(subject_id)
    exam = bank.exam_type(request.form.get("exam_type"))
    back = url_for("subjects.detail", subject_id=subject_id, exam=exam)
    upload = request.files.get("document")
    if upload is None or not upload.filename:
        flash(_("Choose the Word file with the questions."), "danger")
        return redirect(back)
    data = upload.read()
    if len(data) > MAX_UPLOAD_BYTES:
        flash(_("That file is larger than 8 MB."), "danger")
        return redirect(back)
    def make_grader():
        row = get_db().execute(
            "SELECT * FROM instructor WHERE id = ?", (g.instructor["id"],)
        ).fetchone()
        return grader_for_instructor(current_app.config, row)

    try:
        parsed, warnings = read_questions(upload.filename, data, make_grader)
    except ParseError as exc:
        flash(str(exc), "danger")
        return redirect(back)

    db = get_db()
    if request.form.get("mode") == "replace":
        db.execute("DELETE FROM bank_question WHERE subject_id = ? AND exam_type = ?",
                   (subject_id, exam))
    start = bank.next_position(subject_id, exam) - 1
    db.executemany(
        "INSERT INTO bank_question "
        "(subject_id, exam_type, position, text, options, ideal_answer, max_score) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (subject_id, exam, start + n, q["text"],
             json.dumps(q["options"], ensure_ascii=False) if q["options"] else None,
             q["ideal_answer"], q["max_score"])
            for n, q in enumerate(parsed, start=1)
        ],
    )
    db.commit()

    flash(_("Imported %(count)s question(s) from “%(name)s”. Check them below.",
            count=len(parsed), name=upload.filename), "success")
    for warning in warnings:
        flash(warning, "warning")
    return redirect(back)


@bp.route("/<int:subject_id>/questions.xlsx")
@login_required
def export(subject_id):
    subject = bank.owned_subject(subject_id)
    exam = bank.exam_type(request.args.get("exam"))
    payload = build_bank_workbook(subject, bank.questions(subject_id, exam))
    return Response(
        payload,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": attachment_header(
                safe_filename("qayyem-questions-",
                              (subject["code"] or subject["name"]) + "-" + exam, ".xlsx")),
            "Content-Length": str(len(payload)),
        },
    )


# --- one question -------------------------------------------------------------

def _option_lines(options):
    return "\n".join(
        o["label"] + ") " + o["text"] + (" *" if o["correct"] else "") for o in options or []
    )


def _question_form(question=None, exam=None):
    if question is None:
        return {"kind": "written", "max_score": "5", "rubric": "", "exam_type": exam,
                "text": "", "options": "", "ideal_answer": "", "parts": []}
    options = bank.options(question)
    return {
        "exam_type": question["exam_type"],
        "kind": "choice" if options else "written",
        "text": question["text"],
        "options": _option_lines(options),
        # For a choice question the model answer follows the star.
        "ideal_answer": "" if options else (question["ideal_answer"] or ""),
        "rubric": question["rubric"] or "",
        "max_score": "%g" % question["max_score"],
        "parts": _parts_from_json(question["parts"]),
    }


def _read_question_form():
    """Returns (form for re-display, values to save, errors)."""
    form = {
        "kind": "choice" if request.form.get("kind") == "choice" else "written",
        "exam_type": bank.exam_type(request.form.get("exam_type")),
        "text": (request.form.get("text") or "").strip(),
        "options": (request.form.get("options") or "").strip(),
        "ideal_answer": (request.form.get("ideal_answer") or "").strip(),
        "rubric": (request.form.get("rubric") or "").strip(),
        "max_score": (request.form.get("max_score") or "").strip(),
        "parts": _part_rows(),
    }
    errors = []
    if not form["text"]:
        errors.append(_("Type the question."))

    options = None
    ideal = form["ideal_answer"] or None
    if form["kind"] == "choice":
        arabic = any("؀" <= ch <= "ۿ" for ch in form["text"] + form["options"])
        options = parse_option_lines(form["options"].splitlines(), arabic)
        if len(options) < 2:
            errors.append(_("A multiple-choice question needs at least two choices, one per line."))
        elif not any(o["correct"] for o in options):
            errors.append(_("Put a star (*) after the correct choice."))
        ideal = ideal_from_options(options)

    parts, error = _parts(form["parts"])
    if error:
        errors.append(error)
    if parts:
        max_score = sum(p["marks"] for p in parts)
    else:
        max_score, error = _max_score(form["max_score"])
        if error:
            errors.append(error)

    values = {
        "text": form["text"],
        "options": json.dumps(options, ensure_ascii=False) if options else None,
        "ideal_answer": ideal,
        "rubric": form["rubric"] or None,
        "max_score": max_score,
        "parts": json.dumps(parts, ensure_ascii=False) if parts else None,
    }
    return form, values, errors


def _save_question(subject, question):
    form, values, errors = _read_question_form()
    if errors:
        for message in errors:
            flash(message, "danger")
        return render_template("bank_question.html", subject=subject, question=question,
                               form=form), 400

    db = get_db()
    exam = form["exam_type"]
    if question is None:
        db.execute(
            "INSERT INTO bank_question (subject_id, exam_type, position, text, options, "
            "ideal_answer, rubric, max_score, parts) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (subject["id"], exam, bank.next_position(subject["id"], exam), values["text"],
             values["options"], values["ideal_answer"], values["rubric"],
             values["max_score"], values["parts"]),
        )
        flash(_("Question added."), "success")
    else:
        db.execute(
            "UPDATE bank_question SET text = ?, options = ?, ideal_answer = ?, rubric = ?, "
            "max_score = ?, parts = ? WHERE id = ?",
            (values["text"], values["options"], values["ideal_answer"], values["rubric"],
             values["max_score"], values["parts"], question["id"]),
        )
        if exam != question["exam_type"]:
            # Moved to another exam: it goes last there, and both renumber.
            db.execute("UPDATE bank_question SET exam_type = ?, position = ? WHERE id = ?",
                       (exam, bank.next_position(subject["id"], exam), question["id"]))
            bank.renumber(subject["id"])
        flash(_("Question saved."), "success")
    db.commit()
    return redirect(url_for("subjects.detail", subject_id=subject["id"], exam=exam)
                    + "#questions")


@bp.route("/<int:subject_id>/questions/new", methods=("GET", "POST"))
@login_required
def new_question(subject_id):
    subject = bank.owned_subject(subject_id)
    if request.method == "POST":
        return _save_question(subject, None)
    return render_template("bank_question.html", subject=subject, question=None,
                           form=_question_form(exam=bank.exam_type(request.args.get("exam"))))


@bp.route("/<int:subject_id>/questions/<int:question_id>", methods=("GET", "POST"))
@login_required
def edit_question(subject_id, question_id):
    subject = bank.owned_subject(subject_id)
    question = bank.owned_question(subject_id, question_id)
    if request.method == "POST":
        return _save_question(subject, question)
    return render_template("bank_question.html", subject=subject, question=question,
                           form=_question_form(question))


@bp.route("/<int:subject_id>/questions/<int:question_id>/delete", methods=("POST",))
@login_required
def delete_question(subject_id, question_id):
    bank.owned_subject(subject_id)
    question = bank.owned_question(subject_id, question_id)
    db = get_db()
    db.execute("DELETE FROM bank_question WHERE id = ?", (question_id,))
    bank.renumber(subject_id)
    db.commit()
    flash(_("Question deleted."), "success")
    return redirect(url_for("subjects.detail", subject_id=subject_id,
                            exam=question["exam_type"]) + "#questions")
