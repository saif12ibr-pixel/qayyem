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
        raise ParseError(
            "More than one column is named like the answer column ("
            + ", ".join(str(c) for c in exact)
            + "). Rename all but one."
        )
    if len(loose) == 1:
        return loose[0]
    if len(loose) > 1:
        raise ParseError(
            "This file looks like it holds more than one question: "
            + str(len(loose)) + " columns could be answers ("
            + ", ".join(str(c) for c in loose[:4])
            + (", ..." if len(loose) > 4 else "")
            + "). Qayyem grades one question at a time, because each question "
            "needs its own ideal answer and rubric. Upload one question per "
            "file, or rename just the column you want graded to 'response'."
        )
    return None


def _read_dataframe(filename, data):
    """Read bytes into a DataFrame, trying each encoding for CSV."""
    lower = filename.lower()
    if lower.endswith(".xlsx"):
        try:
            return pd.read_excel(io.BytesIO(data), dtype=str)
        except Exception as exc:
            raise ParseError(
                "That .xlsx file could not be read. Re-save it from Excel and "
                "try again. (" + str(exc)[:160] + ")"
            ) from exc

    last = None
    for encoding in ENCODINGS:
        try:
            return pd.read_csv(io.BytesIO(data), dtype=str, encoding=encoding)
        except UnicodeDecodeError as exc:
            last = exc
            continue
        except pd.errors.EmptyDataError as exc:
            raise ParseError("That file is empty.") from exc
        except Exception as exc:
            raise ParseError(
                "That CSV file could not be read. Check it opens in Excel. ("
                + str(exc)[:160] + ")"
            ) from exc
    raise ParseError(
        "The file's text encoding could not be determined. Save it as CSV UTF-8 "
        "and try again. (" + str(last)[:120] + ")"
    )


def parse_responses(filename, data, max_rows=500):
    """Parse an upload into a list of response dicts.

    Returns a list of {"student_id", "response_text", "row_number"} in file
    order. `row_number` is the spreadsheet row the instructor sees, so error
    messages can point at it.
    """
    if not filename:
        raise ParseError("No file was selected.")
    if not filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise ParseError(
            "Only .csv and .xlsx files are supported. You uploaded '"
            + filename + "'."
        )
    if not data:
        raise ParseError("That file is empty.")

    frame = _read_dataframe(filename, data)
    if frame.empty or not len(frame.columns):
        raise ParseError("That file has no rows of data.")

    id_col = _match_column(frame.columns, STUDENT_ID_ALIASES)
    resp_col = _match_column(frame.columns, RESPONSE_ALIASES)

    if id_col is None or resp_col is None:
        found = ", ".join(str(c) for c in frame.columns)
        missing = "student ID" if id_col is None else "response"
        raise ParseError(
            "Could not find a " + missing + " column. Found these columns: "
            + found + ". Name them 'student_id' and 'response' (or the Arabic "
            "equivalents) and try again."
        )
    if id_col == resp_col:
        raise ParseError(
            "The student ID and response columns resolved to the same column ('"
            + str(id_col) + "'). Rename one of them."
        )

    if len(frame) > max_rows:
        raise ParseError(
            "That file has " + str(len(frame)) + " rows, above the limit of "
            + str(max_rows) + ". Split it into smaller files."
        )

    responses = []
    seen = {}
    for position, (_, row) in enumerate(frame.iterrows()):
        spreadsheet_row = position + 2  # +1 for header, +1 for 1-based rows
        raw_id = row[id_col]
        student_id = "" if pd.isna(raw_id) else str(raw_id).strip()
        raw_text = row[resp_col]
        response_text = "" if pd.isna(raw_text) else str(raw_text).strip()

        if not student_id:
            if not response_text:
                continue  # a blank trailing row, not an error
            raise ParseError(
                "Row " + str(spreadsheet_row) + " has a response but no student ID."
            )

        if student_id in seen:
            raise ParseError(
                "Student ID '" + student_id + "' appears twice (rows "
                + str(seen[student_id]) + " and " + str(spreadsheet_row)
                + "). Each student must appear once."
            )
        seen[student_id] = spreadsheet_row

        responses.append(
            {
                "student_id": student_id,
                "response_text": response_text,
                "row_number": spreadsheet_row,
            }
        )

    if not responses:
        raise ParseError("No student responses were found in that file.")

    return responses
