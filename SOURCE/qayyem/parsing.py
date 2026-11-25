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


# --- several files at once, and answer papers --------------------------------

# A paper is one student's answer sheet; its whole text is their answer.
PAPER_EXTENSIONS = (".docx", ".pdf", ".txt")
SUBMISSION_EXTENSIONS = ALLOWED_EXTENSIONS + PAPER_EXTENSIONS
MAX_FILES = 200

_W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# "Student ID: 441001234" or "الرقم الجامعي: 441001234" near the top of a paper.
_PAPER_ID = re.compile(
    r"^\s*(?:student\s*(?:id|number|no\.?)|university\s*id|id|"
    r"الرقم الجامعي|رقم الطالب|معرف الطالب)\s*[:：\-]\s*(\S+)",
    re.IGNORECASE,
)


# Where a paper's answer to each question starts. Explicit labels ("Q2",
# "Question 2", "السؤال الثاني", "س2", "ج2") are trusted first; a bare
# "2." or "2)" is used only on papers that have no labels, since inside an
# answer it is just as likely to be a numbered point.
_ORDINALS = {
    "الأول": 1, "الاول": 1, "الثاني": 2, "الثالث": 3, "الرابع": 4, "الخامس": 5,
    "السادس": 6, "السابع": 7, "الثامن": 8, "التاسع": 9, "العاشر": 10,
}
_NUMBER = r"(\d+|[٠-٩]+|" + "|".join(_ORDINALS) + ")"
_LABELLED = re.compile(
    r"^\s*(?:(?:q|question|ans|answer)\s*\.?\s*(?:no\.?\s*)?"
    r"|(?:السؤال|سؤال|الإجابة|الاجابة|إجابة|اجابة|الجواب|جواب|س|ج)\s*(?:رقم\s*)?)"
    + _NUMBER + r"\s*[.):\-–]?\s*",
    re.IGNORECASE,
)
_BARE = re.compile(r"^\s*(\d+|[٠-٩]+)\s*[.):\-–]\s*")


def _marker_number(match):
    raw = match.group(1)
    if raw in _ORDINALS:
        return _ORDINALS[raw]
    return int(raw.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))


def _paper_answers(text, limit=MAX_QUESTIONS):
    """The paper's answers in question order, split where each numbered
    answer starts: answer 1, then 2, and so on. Returns [] when no numbering
    is found. Text before the first answer (a name, a heading) is dropped."""
    lines = text.splitlines()
    for pattern in (_LABELLED, _BARE):
        answers = []
        for line in lines:
            match = pattern.match(line)
            if match and _marker_number(match) == len(answers) + 1 \
                    and len(answers) < limit:
                answers.append([line[match.end():]])
            elif answers:
                answers[-1].append(line)
        if answers:
            return ["\n".join(a).strip() for a in answers]
    return []

def _docx_table(data):
    """The first table of a Word file as a DataFrame, or None if it has none."""
    import zipfile
    from xml.etree import ElementTree

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
    except Exception:
        return None
    table = root.find(".//" + _W_NS + "tbl")
    if table is None:
        return None
    rows = []
    for tr in table.iter(_W_NS + "tr"):
        rows.append([
            "\n".join(
                "".join(t.text or "" for t in p.iter(_W_NS + "t"))
                for p in tc.iter(_W_NS + "p")
            ).strip()
            for tc in tr.iter(_W_NS + "tc")
        ])
    if len(rows) < 2:
        return None
    width = len(rows[0])
    return pd.DataFrame([r[:width] + [""] * (width - len(r)) for r in rows[1:]],
                        columns=rows[0], dtype=str)


def _exam_from_frame(frame, max_rows):
    """parse_exam's work on an already-read table."""
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


def _read_paper(filename, data):
    """One student's answer paper: (student ID, answer text)."""
    from .reference import _read_docx, _read_pdf, _read_txt

    lower = filename.lower()
    reader = _read_pdf if lower.endswith(".pdf") else (
        _read_docx if lower.endswith(".docx") else _read_txt)
    try:
        text = re.sub(r"\n{3,}", "\n\n", reader(data)).strip()
    except Exception as exc:
        raise ParseError(_(
            "'%(name)s' could not be read. Re-save it and try again. (%(detail)s)",
            name=filename, detail=str(exc)[:160],
        )) from exc
    if not text:
        raise ParseError(_(
            "No text was found in '%(name)s'. A scanned paper is an image; type "
            "the answer into a .docx or .txt file instead.", name=filename,
        ))
    lines = text.splitlines()
    for number, line in enumerate(lines[:10]):
        match = _PAPER_ID.match(line)
        if match:
            del lines[number]
            return match.group(1).strip(), "\n".join(lines).strip()
    # No ID line: the file is named after the student, e.g. "441001234.docx".
    return filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].rsplit(".", 1)[0].strip(), text


def parse_submissions(files, max_rows=500, question_count=None):
    """Parse one or more uploaded files of student answers into one exam.

    `files` is a list of (filename, bytes). Each file is either a table of
    students (.csv, .xlsx, or a Word file holding a table) or one student's
    answer paper (.docx, .pdf, .txt). All the tables must hold the same
    questions.

    A paper is split into one answer per question where its numbered answers
    start (see _paper_answers). How many questions there are comes from the
    tables, else `question_count` (the exam chosen from the bank), else the
    highest numbering found on the papers.

    Returns what parse_exam returns, with every file's students together.
    """
    files = [(name, data) for name, data in files if name]
    if not files:
        raise ParseError(_("No file was selected."))
    if len(files) > MAX_FILES:
        raise ParseError(_(
            "That is %(count)s files, above the limit of %(limit)s. Upload them in "
            "smaller groups.", count=len(files), limit=MAX_FILES,
        ))

    # First read every file, so the papers can be split to the exam's size.
    questions = None
    read = []  # (filename, exam from a table) or (filename, (student id, text))
    for filename, data in files:
        lower = filename.lower()
        if not lower.endswith(SUBMISSION_EXTENSIONS):
            raise ParseError(_(
                "'%(name)s' is not a supported file. Upload .csv or .xlsx tables, "
                "or .docx, .pdf or .txt answer papers.", name=filename,
            ))
        if not data:
            raise ParseError(_("'%(name)s' is empty.", name=filename))

        table = None
        if lower.endswith(ALLOWED_EXTENSIONS):
            table = _check_upload(filename, data)
        elif lower.endswith(".docx"):
            table = _docx_table(data)
            if table is not None and _match_column(table.columns, STUDENT_ID_ALIASES) is None:
                table = None  # a table inside an answer paper, not a class list

        if table is None:
            student_id, text = _read_paper(filename, data)
            if not student_id:
                raise ParseError(_(
                    "No student ID was found in '%(name)s'. Name the file after the "
                    "student, or start the paper with a line like 'Student ID: 441001234'.",
                    name=filename,
                ))
            read.append((filename, None, (student_id, text)))
            continue

        try:
            exam = _exam_from_frame(table, max_rows)
        except ParseError as exc:
            if len(files) == 1:
                raise
            raise ParseError(_("%(name)s: %(error)s", name=filename, error=str(exc))) from exc
        if questions is None:
            questions = exam["questions"]
        elif len(exam["questions"]) != len(questions):
            raise ParseError(_(
                "'%(name)s' has %(count)s questions but the first file has %(first)s. "
                "Every file must hold the same exam.",
                name=filename, count=len(exam["questions"]), first=len(questions),
            ))
        read.append((filename, exam, None))

    papers = [(name, paper) for name, exam, paper in read if paper]
    if questions is None:
        count = question_count or max(
            [len(_paper_answers(text)) for _name, (_sid, text) in papers] + [1])
        questions = [_("Q%(n)s", n=n) for n in range(1, count + 1)] if count > 1 \
            else [papers[0][0]]

    students = []
    seen = {}
    offset = 0
    for filename, exam, paper in read:
        if paper:
            student_id, text = paper
            answers = [text]
            if len(questions) > 1:
                answers = _paper_answers(text, len(questions))
                if not answers:
                    raise ParseError(_(
                        "The answers in '%(name)s' are not numbered, so they cannot be "
                        "matched to the %(count)s questions. Start each answer on its own "
                        "line with its number, like 'Q1', '1.' or 'س1'.",
                        name=filename, count=len(questions),
                    ))
                # A question the student skipped is an empty answer, scored 0.
                answers += [""] * (len(questions) - len(answers))
            exam = {"students": [
                {"student_id": student_id, "row_number": 1, "answers": answers}]}

        for student in exam["students"]:
            if student["student_id"] in seen:
                raise ParseError(_(
                    "Student ID '%(id)s' appears in both '%(first)s' and '%(second)s'. "
                    "Each student must appear once.",
                    id=student["student_id"], first=seen[student["student_id"]],
                    second=filename,
                ))
            seen[student["student_id"]] = filename
            # Row numbers only order the results, so each file follows the last.
            students.append(dict(student, row_number=student["row_number"] + offset))
        offset = max(s["row_number"] for s in students)

    if len(students) > max_rows:
        raise ParseError(_(
            "These files have %(rows)s students together, above the limit of "
            "%(limit)s. Upload them in smaller groups.", rows=len(students), limit=max_rows,
        ))
    return {"questions": questions, "students": students}


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
