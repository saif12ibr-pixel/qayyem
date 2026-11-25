"""Builds the downloadable Excel workbook (UC-5).

Excel is the output format because it is what Saudi university administrative
workflows already use, and results must drop into that workflow without a
conversion step (SS 2.24).

The feedback column is written right-to-left with an explicit reading order so
Arabic renders correctly in Excel rather than appearing reversed or
left-aligned (SS 2.23).
"""
import io
import json

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)

RTL = Alignment(horizontal="right", vertical="top", wrap_text=True, readingOrder=2)
LTR = Alignment(horizontal="left", vertical="top", wrap_text=True, readingOrder=1)
CENTER = Alignment(horizontal="center", vertical="top")

COLUMNS = [
    ("Student ID", 18),
    ("Score", 10),
    ("Feedback (Arabic)", 80),
    ("Note", 28),
]


def format_score(value):
    """5.0 -> "5", 2.5 -> "2.5"."""
    return "%g" % value


def format_breakdown(breakdown):
    """"Definition 3/4 · Example 4/6", for the export and the results page."""
    return " · ".join(
        p["name"] + " " + format_score(p["score"]) + "/" + format_score(p["marks"])
        for p in breakdown
    )


def _header(sheet, columns):
    for index, (title, width) in enumerate(columns, start=1):
        cell = sheet.cell(row=1, column=index, value=title)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = CENTER
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.freeze_panes = "A2"


def note_for(row):
    """The Note column: a grading error, or that the instructor changed the
    model's grade (and what the model gave)."""
    if row.get("reviewed_at"):
        ai = row.get("ai_score")
        return "Reviewed by the instructor" + (
            " (AI score " + format_score(ai) + ")" if ai is not None else "")
    return row.get("error") or ""


def _score(cell, value):
    cell.value = value if value is not None else "-"
    cell.alignment = CENTER
    if value is not None:
        cell.number_format = "0.##"


def build_workbook(assignment, results, questions=()):
    """Return the workbook as bytes.

    `assignment` is the assignment row; `results` is a sequence of rows with
    student_id, score, feedback_ar and error. For an exam, `questions` holds
    its question rows and each result also carries question_id.
    """
    if questions:
        return _build_exam_workbook(assignment, results, questions)

    # A "Parts" column only when the question was marked in parts.
    columns = list(COLUMNS)
    in_parts = any(row.get("breakdown") for row in results)
    if in_parts:
        columns.append(("Parts", 40))

    book = Workbook()
    sheet = book.active
    sheet.title = "Results"

    _header(sheet, columns)

    for offset, row in enumerate(results, start=2):
        sheet.cell(row=offset, column=1, value=row["student_id"]).alignment = LTR

        score_cell = sheet.cell(row=offset, column=2)
        score_cell.value = row["score"] if row["score"] is not None else "-"
        score_cell.alignment = CENTER
        if row["score"] is not None:
            score_cell.number_format = "0.##"

        feedback = sheet.cell(row=offset, column=3, value=row["feedback_ar"] or "")
        feedback.alignment = RTL

        note = sheet.cell(row=offset, column=4, value=note_for(dict(row)))
        note.alignment = LTR

        if in_parts:
            sheet.cell(row=offset, column=5,
                       value=format_breakdown(row.get("breakdown") or [])).alignment = LTR

    _add_metadata_sheet(book, assignment, results)

    stream = io.BytesIO()
    book.save(stream)
    return stream.getvalue()


def _build_exam_workbook(assignment, results, questions):
    """One row per student with a score per question and a total, then a
    second sheet with every answer's feedback."""
    from .results import group_by_student

    students = group_by_student(results)
    book = Workbook()

    sheet = book.active
    sheet.title = "Results"
    columns = [("Student ID", 18)]
    columns += [("Q" + str(q["position"]) + " (/" + "%g" % q["max_score"] + ")", 12)
                for q in questions]
    columns.append(("Total (/" + "%g" % assignment["max_score"] + ")", 14))
    _header(sheet, columns)
    for offset, student in enumerate(students, start=2):
        sheet.cell(row=offset, column=1, value=student["student_id"]).alignment = LTR
        for index, answer in enumerate(student["answers"], start=2):
            _score(sheet.cell(row=offset, column=index), answer["score"])
        total = sheet.cell(row=offset, column=len(columns), value=None)
        _score(total, student["total"])
        total.font = Font(bold=True)

    detail = book.create_sheet("Feedback")
    _header(detail, [("Student ID", 18), ("Question", 28), ("Score", 10),
                     ("Feedback (Arabic)", 80), ("Note", 28), ("Parts", 40)])
    offset = 2
    for student in students:
        for question, answer in zip(questions, student["answers"]):
            detail.cell(row=offset, column=1, value=student["student_id"]).alignment = LTR
            detail.cell(row=offset, column=2,
                        value="Q" + str(question["position"]) + " " + question["title"]
                        ).alignment = LTR
            _score(detail.cell(row=offset, column=3), answer["score"])
            detail.cell(row=offset, column=4, value=answer["feedback_ar"] or "").alignment = RTL
            detail.cell(row=offset, column=5, value=note_for(dict(answer))).alignment = LTR
            detail.cell(row=offset, column=6,
                        value=format_breakdown(answer.get("breakdown") or [])).alignment = LTR
            offset += 1

    meta = _add_metadata_sheet(book, assignment, results)
    # Replace the single ideal answer and rubric with one entry per question.
    for row in range(meta.max_row, 0, -1):
        if meta.cell(row=row, column=1).value in ("Ideal answer", "Rubric"):
            meta.delete_rows(row)
    totals = [s["total"] for s in students if s["total"] is not None]
    meta.append(("Students", len(students)))
    meta.append(("Average total", round(sum(totals) / len(totals), 2) if totals else "-"))
    for q in questions:
        label = "Q" + str(q["position"])
        meta.append((label + " column", q["title"]))
        meta.append((label + " marks", q["max_score"]))
        meta.append((label + " ideal answer", q["ideal_answer"]))
        meta.append((label + " rubric", q["rubric"] or "-"))
        if q["parts"]:
            meta.append((label + " parts", "; ".join(
                p["name"] + " (" + format_score(p["marks"]) + ")" for p in json.loads(q["parts"])
            )))
    for row in meta.iter_rows(min_row=1):
        row[0].font = Font(bold=True)
        row[0].alignment = Alignment(vertical="top")
        row[1].alignment = Alignment(wrap_text=True, vertical="top")

    stream = io.BytesIO()
    book.save(stream)
    return stream.getvalue()


def _add_metadata_sheet(book, assignment, results):
    """Record what produced these grades.

    Useful for the instructor, and it is also the provenance the project report
    needs when quoting measured results.
    """
    sheet = book.create_sheet("Assignment")
    scored = [r["score"] for r in results if r["score"] is not None]
    models = sorted({r["model_name"] for r in results if r["model_name"]})

    rows = [
        ("Assignment", assignment["title"]),
        ("Graded on", assignment["created_at"]),
        ("Maximum score", assignment["max_score"]),
        ("Responses", len(results)),
        ("Graded successfully", len(scored)),
        ("Average score", round(sum(scored) / len(scored), 2) if scored else "-"),
        ("Model", ", ".join(models) or "-"),
        ("Ideal answer", assignment["ideal_answer"]),
        ("Rubric", assignment["rubric"] or "-"),
    ]
    if "exam_type" in assignment.keys() and assignment["exam_type"]:
        rows.insert(1, ("Exam", assignment["exam_type"].capitalize()))
    parts = assignment.get("parts") if hasattr(assignment, "get") else assignment["parts"]
    if parts:
        rows.append(("Parts", "; ".join(
            p["name"] + " (" + format_score(p["marks"]) + ")" for p in json.loads(parts)
        )))

    sheet.column_dimensions["A"].width = 22
    sheet.column_dimensions["B"].width = 90
    for index, (label, value) in enumerate(rows, start=1):
        key = sheet.cell(row=index, column=1, value=label)
        key.font = Font(bold=True)
        key.alignment = Alignment(vertical="top")
        sheet.cell(row=index, column=2, value=value).alignment = Alignment(
            wrap_text=True, vertical="top"
        )
    return sheet


BAND_NAMES = {"low": "Low", "average": "Average", "high": "High"}


def build_student_workbook(assignment, student, ranked_count):
    """One student's results as a workbook: a summary, then every answer with
    its score, the student's own text and the feedback."""
    book = Workbook()
    sheet = book.active
    sheet.title = "Student"

    def pct(value):
        return format_score(value) + "%" if value is not None else "-"

    summary = [
        ("Student ID", student["student_id"]),
        ("Assignment", assignment["title"]),
        ("Graded on", assignment["created_at"]),
        ("Total", (format_score(student["total"]) if student["total"] is not None else "-")
         + " / " + format_score(student["max_score"])),
        ("Percentage", pct(student["percent"])),
        ("Average per question", pct(student["average_percent"])),
        ("Rank", "%s of %s" % (student["rank"], ranked_count) if student["rank"] else "-"),
        ("Group", BAND_NAMES.get(student["band"], "-")),
    ]
    if student["best"]:
        best = student["best"]
        summary.append(("Highest question", "%s: %s / %s (%s)" % (
            best["label"], format_score(best["score"]), format_score(best["max_score"]),
            pct(best["percent"]))))
    for index, (label, value) in enumerate(summary, start=1):
        key = sheet.cell(row=index, column=1, value=label)
        key.font = Font(bold=True)
        sheet.cell(row=index, column=2, value=value).alignment = LTR

    columns = [("Question", 22), ("Score", 10), ("Out of", 10), ("Percentage", 12),
               ("Student answer", 60), ("Feedback (Arabic)", 70), ("Note", 28)]
    top = len(summary) + 2
    for index, (title, width) in enumerate(columns, start=1):
        cell = sheet.cell(row=top, column=index, value=title)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = CENTER
        sheet.column_dimensions[get_column_letter(index)].width = max(
            width, sheet.column_dimensions[get_column_letter(index)].width or 0)
    for offset, answer in enumerate(student["answers"], start=top + 1):
        sheet.cell(row=offset, column=1, value=answer["label"]).alignment = LTR
        _score(sheet.cell(row=offset, column=2), answer["score"])
        _score(sheet.cell(row=offset, column=3), answer["max_score"])
        sheet.cell(row=offset, column=4, value=pct(answer["percent"])).alignment = CENTER
        sheet.cell(row=offset, column=5, value=answer["response_text"] or "").alignment = Alignment(
            vertical="top", wrap_text=True)
        sheet.cell(row=offset, column=6, value=answer["feedback_ar"] or "").alignment = RTL
        sheet.cell(row=offset, column=7, value=note_for(dict(answer))).alignment = LTR
    sheet.column_dimensions["A"].width = 24
    sheet.column_dimensions["B"].width = 40

    stream = io.BytesIO()
    book.save(stream)
    return stream.getvalue()


def student_filename_for(assignment, student_id):
    """"qayyem-midterm-441001234.xlsx"."""
    safe = "".join(ch if (ch.isalnum() or ch in "-_") else "_" for ch in student_id)[:40] or "student"
    return filename_for(assignment)[: -len(".xlsx")] + "-" + safe + ".xlsx"


def filename_for(assignment):
    """A safe download filename derived from the assignment title.

    The uploaded file's own extension is dropped first, so "midterm.csv" yields
    "qayyem-midterm.xlsx" rather than "qayyem-midterm_csv.xlsx".
    """
    title = assignment["title"] or "results"
    for extension in (".csv", ".xlsx"):
        if title.lower().endswith(extension):
            title = title[: -len(extension)]
            break

    base = "".join(
        ch if (ch.isalnum() or ch in " -_") else "_" for ch in title
    ).strip("_ ") or "results"
    return "qayyem-" + base.replace(" ", "-")[:60] + ".xlsx"


CORRECT_FILL = PatternFill("solid", fgColor="D1F2E0")
CORRECT_FONT = Font(bold=True, color="0F5132")
STAR = "★"


def _arabic_share(texts):
    letters = "".join(texts)
    arabic = sum(1 for ch in letters if "؀" <= ch <= "ۿ")
    latin = sum(1 for ch in letters if ch.isascii() and ch.isalpha())
    return arabic > latin


def build_bank_workbook(subject, questions):
    """A subject's question bank as a sheet: one row per question, a column
    per choice, and a star beside the correct one."""
    book = Workbook()
    sheet = book.active
    sheet.title = "Questions"

    parsed = [json.loads(q["options"]) if q["options"] else None for q in questions]
    choice_count = max((len(o) for o in parsed if o), default=0)
    columns = [("No.", 6), ("Question", 50), ("Type", 14)]
    columns += [("Choice " + str(i + 1), 22) for i in range(choice_count)]
    columns += [("Correct / model answer", 50), ("Marks", 8), ("Rubric", 40)]
    _header(sheet, columns)

    arabic = _arabic_share([q["text"] for q in questions])
    text_align = RTL if arabic else LTR
    if arabic:
        sheet.sheet_view.rightToLeft = True

    for offset, (q, options) in enumerate(zip(questions, parsed), start=2):
        sheet.cell(row=offset, column=1, value=q["position"]).alignment = CENTER
        sheet.cell(row=offset, column=2, value=q["text"]).alignment = text_align
        sheet.cell(row=offset, column=3,
                   value="MSQ" if options else "Open question").alignment = LTR
        for index, option in enumerate(options or [], start=4):
            label = option["label"] + ") " + option["text"]
            cell = sheet.cell(row=offset, column=index,
                              value=(STAR + " " + label) if option["correct"] else label)
            cell.alignment = text_align
            if option["correct"]:
                cell.fill = CORRECT_FILL
                cell.font = CORRECT_FONT
        answer_column = 4 + choice_count
        answer = sheet.cell(row=offset, column=answer_column,
                            value=(STAR + " " + q["ideal_answer"]) if q["ideal_answer"] else "-")
        answer.alignment = text_align
        if q["ideal_answer"]:
            answer.font = CORRECT_FONT
        _score(sheet.cell(row=offset, column=answer_column + 1), q["max_score"])
        sheet.cell(row=offset, column=answer_column + 2,
                   value=q["rubric"] or "").alignment = text_align

    info = book.create_sheet("Subject")
    info.column_dimensions["A"].width = 18
    info.column_dimensions["B"].width = 60
    total = sum(q["max_score"] for q in questions)
    for index, (label, value) in enumerate((
        ("Subject", subject["name"]),
        ("Code", subject["code"] or "-"),
        ("Questions", len(questions)),
        ("Total marks", total),
        ("Grading guidelines", subject["rubric"] or "-"),
    ), start=1):
        info.cell(row=index, column=1, value=label).font = Font(bold=True)
        info.cell(row=index, column=2, value=value).alignment = Alignment(
            wrap_text=True, vertical="top")

    stream = io.BytesIO()
    book.save(stream)
    return stream.getvalue()


def safe_filename(prefix, title, extension):
    base = "".join(ch if (ch.isalnum() or ch in " -_") else "_" for ch in title or "")
    base = base.strip("_ ") or "export"
    return prefix + base.replace(" ", "-")[:60] + extension


def attachment_header(filename):
    """Content-Disposition for a download whose name may be Arabic: an ASCII
    fallback plus the UTF-8 name (RFC 6266), since the header is latin-1."""
    from urllib.parse import quote

    fallback = "".join(ch if ch.isascii() and (ch.isalnum() or ch in "-_.") else "_"
                       for ch in filename)
    return 'attachment; filename="%s"; filename*=UTF-8\'\'%s' % (fallback, quote(filename))
