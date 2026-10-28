"""Reads an uploaded CSV/Excel file into student responses.

Two practical problems this solves, both of which produce unusable results if
ignored:

1. Encoding. Instructor spreadsheets containing Arabic arrive as UTF-8, UTF-8
   with a BOM, or windows-1256 (the Arabic code page Excel on Windows still
   writes). Assuming UTF-8 turns Arabic into mojibake, so each candidate
   encoding is tried in turn.

2. Headers. Instructors label their columns in either language, so headers are
   matched against English and Arabic aliases after normalisation rather than
   requiring exact names.

Every rejection raises ParseError with a message written for the instructor,
satisfying the Sprint 2 requirement that malformed files are rejected with
descriptive errors (SS 3.3).
"""
import io
import re
import unicodedata

import pandas as pd

from .i18n import gettext as _

ALLOWED_EXTENSIONS = (".csv", ".xlsx")
ENCODINGS = ("utf-8-sig", "utf-8", "cp1256")

_RAW_STUDENT_ID_ALIASES = {
    "student_id", "studentid", "student", "id", "sid", "student_number",
    "university_id", "academic_number", "no", "number",
    # Arabic: university number / student number / student id / the number
    "الرقم الجامعي",
    "رقم الطالب",
    "معرف الطالب",
    "الرقم",
    "الطالب",
}

_RAW_RESPONSE_ALIASES = {
    "response", "answer", "text", "student_response", "submission",
    "response_text", "student_answer", "reply", "content",
    # Arabic: the answer / student answer / the response / the text
    "الاجابة",
    "اجابة الطالب",
    "الرد",
    "النص",
    "المحتوى",
}


class ParseError(Exception):
    """A problem with the uploaded file that the instructor must fix."""


def _normalise_header(value):
    """Lowercase, strip punctuation, and fold Arabic letter variants.

    Arabic has several orthographic variants that instructors mix freely -- the
    alef forms, final yeh, and teh marbuta. Folding them means a header of
    "الإجابة" matches an alias written
    "الاجابة".
    """
    text = unicodedata.normalize("NFKC", str(value)).strip().lower()
    text = text.replace("أ", "ا").replace("إ", "ا")
    text = text.replace("آ", "ا").replace("ى", "ي")
    text = text.replace("ة", "ه")
    text = re.sub(r"[ً-ْ]", "", text)          # Arabic diacritics
    text = re.sub(r"[^\w\s؀-ۿ]", " ", text)     # punctuation
    text = re.sub(r"[\s_]+", " ", text).strip()
    return text


# The aliases must go through the same folding as the headers they are compared
# against, or an alias written with hamza or teh marbuta ("الإجابة")
# can never match its own normalised form.
STUDENT_ID_ALIASES = frozenset(_normalise_header(a) for a in _RAW_STUDENT_ID_ALIASES)
RESPONSE_ALIASES = frozenset(_normalise_header(a) for a in _RAW_RESPONSE_ALIASES)


def _match_columns(columns, aliases):
    """Find every column matching `aliases`, separating exact from loose matches.

    Returning all of them rather than the first is what lets the caller notice an
    exam paper. A file headed "answer 1 ... answer 20" matches the response
    aliases twenty times over, and quietly taking the first would grade one
    question and discard nineteen while reporting success.
    """
    normalised = {col: _normalise_header(col) for col in columns}

    exact = [col for col, norm in normalised.items() if norm in aliases]

    # Token matching, so "student id (required)" still resolves. Whole tokens
    # rather than substrings keeps a short alias like "id" from binding to an
    # unrelated column that merely contains those letters.
    loose = []
    for col, norm in normalised.items():
        if col in exact:
            continue
        header_tokens = set(norm.split())
        for alias in aliases:
            alias_tokens = set(alias.split())
            if alias_tokens and alias_tokens <= header_tokens:
                loose.append(col)
                break

    return exact, loose


def _match_column(columns, aliases):
    """The single best match, or None. Raises on genuine ambiguity."""
    exact, loose = _match_columns(columns, aliases)

    # One exact match settles it, even alongside looser ones: an explicit
    # "response" column is a clear statement of intent.
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise ParseError(_(
            "More than one column is named like the answer column (%(columns)s). "
            "Rename all but one.",
            columns=", ".join(str(c) for c in exact),
        ))
    if len(loose) == 1:
        return loose[0]
    if len(loose) > 1:
        raise ParseError(_(
            "This file looks like it holds more than one question: %(count)s "
            "columns could be answers (%(columns)s). Qayyem grades one question "
            "at a time, because each question needs its own ideal answer and "
            "rubric. Upload one question per file, or rename just the column you "
            "want graded to 'response'.",
            count=len(loose),
            columns=", ".join(str(c) for c in loose[:4]) + (", ..." if len(loose) > 4 else ""),
        ))
    return None


def _read_dataframe(filename, data):
    """Read bytes into a DataFrame, trying each encoding for CSV."""
    lower = filename.lower()
    if lower.endswith(".xlsx"):
        try:
            return pd.read_excel(io.BytesIO(data), dtype=str)
        except Exception as exc:
            raise ParseError(_(
                "That .xlsx file could not be read. Re-save it from Excel and "
                "try again. (%(detail)s)",
                detail=str(exc)[:160],
            )) from exc

    last = None
    for encoding in ENCODINGS:
        try:
            return pd.read_csv(io.BytesIO(data), dtype=str, encoding=encoding)
        except UnicodeDecodeError as exc:
            last = exc
            continue
        except pd.errors.EmptyDataError as exc:
            raise ParseError(_("That file is empty.")) from exc
        except Exception as exc:
            raise ParseError(_(
                "That CSV file could not be read. Check it opens in Excel. (%(detail)s)",
                detail=str(exc)[:160],
            )) from exc
    raise ParseError(_(
        "The file's text encoding could not be determined. Save it as CSV UTF-8 "
        "and try again. (%(detail)s)",
        detail=str(last)[:120],
    ))


MAX_QUESTIONS = 20


def _answer_columns(columns):
    """Every answer column, for a file that may hold a whole exam.

    One exact match still settles it, as in _match_column, but several loose
    matches ("answer 1", "answer 2", ...) are read as separate questions
    rather than rejected.
    """
    exact, loose = _match_columns(columns, RESPONSE_ALIASES)
    if len(exact) == 1:
        return exact
    if len(exact) > 1:
        raise ParseError(_(
            "More than one column is named like the answer column (%(columns)s). "
            "Rename all but one.",
            columns=", ".join(str(c) for c in exact),
        ))
    return loose


def _check_upload(filename, data):
    if not filename:
        raise ParseError(_("No file was selected."))
    if not filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise ParseError(_(
            "Only .csv and .xlsx files are supported. You uploaded '%(name)s'.",
            name=filename,
        ))
    if not data:
        raise ParseError(_("That file is empty."))

    frame = _read_dataframe(filename, data)
    if frame.empty or not len(frame.columns):
        raise ParseError(_("That file has no rows of data."))
    return frame


def _missing_column_error(frame, missing_id):
    found = ", ".join(str(c) for c in frame.columns)
    if missing_id:
        message = _(
            "Could not find a student ID column. Found these columns: %(found)s. "
            "Name them 'student_id' and 'response' (or the Arabic equivalents) "
            "and try again.",
            found=found,
        )
    else:
        message = _(
            "Could not find a response column. Found these columns: %(found)s. "
            "Name them 'student_id' and 'response' (or the Arabic equivalents) "
            "and try again.",
            found=found,
        )
    return ParseError(message)


def _read_students(frame, id_col, answer_cols, max_rows):
    """Rows as {"student_id", "row_number", "answers"}, one answer per column."""
    if len(frame) > max_rows:
        raise ParseError(_(
            "That file has %(rows)s rows, above the limit of %(limit)s. "
            "Split it into smaller files.",
            rows=len(frame), limit=max_rows,
        ))

    def text(value):
        return "" if pd.isna(value) else str(value).strip()

    students = []
    seen = {}
    for position, (_index, row) in enumerate(frame.iterrows()):
        spreadsheet_row = position + 2  # +1 for header, +1 for 1-based rows
        student_id = text(row[id_col])
        answers = [text(row[col]) for col in answer_cols]

        if not student_id:
            if not any(answers):
                continue  # a blank trailing row, not an error
            raise ParseError(_(
                "Row %(row)s has a response but no student ID.", row=spreadsheet_row
            ))

        if student_id in seen:
            raise ParseError(_(
                "Student ID '%(id)s' appears twice (rows %(first)s and %(second)s). "
                "Each student must appear once.",
                id=student_id, first=seen[student_id], second=spreadsheet_row,
            ))
        seen[student_id] = spreadsheet_row

        students.append(
            {"student_id": student_id, "row_number": spreadsheet_row, "answers": answers}
        )

    if not students:
        raise ParseError(_("No student responses were found in that file."))
    return students


def parse_exam(filename, data, max_rows=500):
    """Parse an upload that may hold one question or several.

    Returns {"questions": [column header, ...], "students": [...]}, where each
    student's "answers" lines up with "questions".
    """
    frame = _check_upload(filename, data)

    id_col = _match_column(frame.columns, STUDENT_ID_ALIASES)
    if id_col is None:
        raise _missing_column_error(frame, missing_id=True)
    answer_cols = [col for col in _answer_columns(frame.columns) if col != id_col]
    if not answer_cols:
        raise _missing_column_error(frame, missing_id=False)
    if len(answer_cols) > MAX_QUESTIONS:
        raise ParseError(_(
            "That file has %(count)s answer columns, above the limit of %(limit)s "
            "questions. Split it into smaller files.",
            count=len(answer_cols), limit=MAX_QUESTIONS,
        ))

    return {
        "questions": [str(col) for col in answer_cols],
        "students": _read_students(frame, id_col, answer_cols, max_rows),
    }


def parse_responses(filename, data, max_rows=500):
    """Parse a single-question upload into a list of response dicts.

    Returns a list of {"student_id", "response_text", "row_number"} in file
    order. `row_number` is the spreadsheet row the instructor sees, so error
    messages can point at it.
    """
    frame = _check_upload(filename, data)

    id_col = _match_column(frame.columns, STUDENT_ID_ALIASES)
    resp_col = _match_column(frame.columns, RESPONSE_ALIASES)

    if id_col is None or resp_col is None:
        raise _missing_column_error(frame, missing_id=id_col is None)
    if id_col == resp_col:
        raise ParseError(_(
            "The student ID and response columns resolved to the same column "
            "('%(column)s'). Rename one of them.",
            column=id_col,
        ))

    return [
        {
            "student_id": s["student_id"],
            "response_text": s["answers"][0],
            "row_number": s["row_number"],
        }
        for s in _read_students(frame, id_col, [resp_col], max_rows)
    ]
