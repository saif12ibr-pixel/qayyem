"""Builds the downloadable Excel workbook (UC-5).

Excel is the output format because it is what Saudi university administrative
workflows already use, and results must drop into that workflow without a
conversion step (SS 2.24).

The feedback column is written right-to-left with an explicit reading order so
Arabic renders correctly in Excel rather than appearing reversed or
left-aligned (SS 2.23).
"""
import io

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


def build_workbook(assignment, results):
    """Return the workbook as bytes.

    `assignment` is the assignment row; `results` is a sequence of rows with
    student_id, score, feedback_ar and error.
    """
    book = Workbook()
    sheet = book.active
    sheet.title = "Results"

    for index, (title, width) in enumerate(COLUMNS, start=1):
        cell = sheet.cell(row=1, column=index, value=title)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = CENTER
        sheet.column_dimensions[get_column_letter(index)].width = width

    sheet.freeze_panes = "A2"

    for offset, row in enumerate(results, start=2):
        sheet.cell(row=offset, column=1, value=row["student_id"]).alignment = LTR

        score_cell = sheet.cell(row=offset, column=2)
        score_cell.value = row["score"] if row["score"] is not None else "-"
        score_cell.alignment = CENTER
        if row["score"] is not None:
            score_cell.number_format = "0.##"

        feedback = sheet.cell(row=offset, column=3, value=row["feedback_ar"] or "")
        feedback.alignment = RTL

        note = sheet.cell(row=offset, column=4, value=row["error"] or "")
        note.alignment = LTR

    _add_metadata_sheet(book, assignment, results)

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
