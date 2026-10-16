"""Tests for upload parsing (SS 3.3 Sprint 2, UC-2 alternate flows)."""
import io

import pytest
from openpyxl import Workbook

from qayyem.parsing import ParseError, parse_responses

ARABIC_ANSWER = "التمويل هو عملية"
ARABIC_ID_HEADER = "الرقم الجامعي"
ARABIC_RESP_HEADER = "الإجابة"


def csv_bytes(text, encoding="utf-8"):
    return text.encode(encoding)


def test_parses_english_headers():
    data = csv_bytes("student_id,response\nS001,Hello world\nS002,Another answer\n")
    rows = parse_responses("a.csv", data)
    assert [r["student_id"] for r in rows] == ["S001", "S002"]
    assert rows[0]["response_text"] == "Hello world"
    assert rows[0]["row_number"] == 2


def test_parses_arabic_headers_and_content():
    text = ARABIC_ID_HEADER + "," + ARABIC_RESP_HEADER + "\nS001," + ARABIC_ANSWER + "\n"
    rows = parse_responses("a.csv", csv_bytes(text))
    assert rows[0]["student_id"] == "S001"
    assert rows[0]["response_text"] == ARABIC_ANSWER


def test_handles_utf8_bom():
    text = "student_id,response\nS001," + ARABIC_ANSWER + "\n"
    rows = parse_responses("a.csv", csv_bytes(text, "utf-8-sig"))
    assert rows[0]["response_text"] == ARABIC_ANSWER
    # A BOM left in place would corrupt the first header and lose the column.
    assert rows[0]["student_id"] == "S001"


def test_handles_windows_1256_arabic():
    """Excel on Windows still writes Arabic CSVs in cp1256."""
    text = "student_id,response\nS001," + ARABIC_ANSWER + "\n"
    rows = parse_responses("a.csv", csv_bytes(text, "cp1256"))
    assert rows[0]["response_text"] == ARABIC_ANSWER


def test_header_aliases_are_case_and_space_insensitive():
    data = csv_bytes("Student ID,Student Answer\nS001,Text\n")
    rows = parse_responses("a.csv", data)
    assert rows[0]["student_id"] == "S001"
    assert rows[0]["response_text"] == "Text"


def test_reads_xlsx():
    book = Workbook()
    sheet = book.active
    sheet.append(["student_id", "response"])
    sheet.append(["S001", ARABIC_ANSWER])
    stream = io.BytesIO()
    book.save(stream)

    rows = parse_responses("a.xlsx", stream.getvalue())
    assert rows[0]["response_text"] == ARABIC_ANSWER


def test_rejects_unsupported_extension():
    with pytest.raises(ParseError, match="Only .csv and .xlsx"):
        parse_responses("a.txt", b"student_id,response\nS1,x\n")


def test_rejects_empty_file():
    with pytest.raises(ParseError, match="empty"):
        parse_responses("a.csv", b"")


def test_rejects_missing_response_column():
    with pytest.raises(ParseError, match="response column"):
        parse_responses("a.csv", csv_bytes("student_id,grade\nS001,5\n"))


def test_rejects_missing_id_column():
    with pytest.raises(ParseError, match="student ID column"):
        parse_responses("a.csv", csv_bytes("name,response\nAli,text\n"))


def test_rejects_duplicate_student_ids():
    data = csv_bytes("student_id,response\nS001,a\nS001,b\n")
    with pytest.raises(ParseError, match="appears twice"):
        parse_responses("a.csv", data)


def test_rejects_file_over_row_limit():
    body = "".join("S{0},answer\n".format(i) for i in range(5))
    with pytest.raises(ParseError, match="above the limit"):
        parse_responses("a.csv", csv_bytes("student_id,response\n" + body), max_rows=3)


def test_rejects_response_with_no_student_id():
    data = csv_bytes("student_id,response\n,orphan answer\n")
    with pytest.raises(ParseError, match="no student ID"):
        parse_responses("a.csv", data)


def test_keeps_empty_responses_for_zero_scoring():
    """An empty answer is valid input: UC-3 scores it zero rather than rejecting."""
    data = csv_bytes("student_id,response\nS001,\nS002,real answer\n")
    rows = parse_responses("a.csv", data)
    assert len(rows) == 2
    assert rows[0]["response_text"] == ""


def test_skips_fully_blank_trailing_rows():
    data = csv_bytes("student_id,response\nS001,answer\n,\n,\n")
    rows = parse_responses("a.csv", data)
    assert len(rows) == 1


# --- multi-question exam files ----------------------------------------------
#
# Silently grading one column out of twenty and reporting success is the worst
# failure mode this tool can have, so these tests pin the refusal.

def multi_question_csv(headers):
    body = ",".join(headers) + "\n"
    body += "S001," + ",".join("answer {0}".format(i) for i in range(1, len(headers))) + "\n"
    return body.encode("utf-8")


def test_rejects_exam_file_with_many_answer_columns():
    headers = ["student_id"] + ["answer {0}".format(i) for i in range(1, 21)]
    with pytest.raises(ParseError, match="more than one question"):
        parse_responses("exam.csv", multi_question_csv(headers))


def test_rejects_exam_file_with_numbered_response_columns():
    headers = ["student_id"] + ["response {0}".format(i) for i in range(1, 21)]
    with pytest.raises(ParseError, match="more than one question"):
        parse_responses("exam.csv", multi_question_csv(headers))


def test_rejects_arabic_exam_file():
    headers = ["\u0627\u0644\u0631\u0642\u0645 \u0627\u0644\u062c\u0627\u0645\u0639\u064a"] + [
        "\u0627\u0644\u0625\u062c\u0627\u0628\u0629 {0}".format(i) for i in range(1, 21)
    ]
    with pytest.raises(ParseError, match="more than one question"):
        parse_responses("exam.csv", multi_question_csv(headers))


def test_error_names_the_columns_and_says_what_to_do():
    headers = ["student_id"] + ["answer {0}".format(i) for i in range(1, 21)]
    with pytest.raises(ParseError) as caught:
        parse_responses("exam.csv", multi_question_csv(headers))
    message = str(caught.value)
    assert "20 columns" in message
    assert "one question per" in message
    assert "'response'" in message


def test_an_explicit_response_column_resolves_the_ambiguity():
    """Naming one column exactly 'response' is a clear statement of intent."""
    headers = ["student_id", "response"] + ["answer {0}".format(i) for i in range(1, 5)]
    rows = parse_responses("exam.csv", multi_question_csv(headers))
    assert len(rows) == 1
    assert rows[0]["response_text"] == "answer 1"


def test_two_exact_answer_columns_are_rejected():
    data = b"student_id,response,answer\nS001,first,second\n"
    with pytest.raises(ParseError, match="More than one column"):
        parse_responses("a.csv", data)


def test_ordinary_extra_columns_are_still_fine():
    """Name, section and grade columns must not look like a second question."""
    data = ("student_id,name,section,response,grade\n"
            "S001,Ali,A,my answer,\n").encode("utf-8")
    rows = parse_responses("a.csv", data)
    assert rows[0]["response_text"] == "my answer"
    assert rows[0]["student_id"] == "S001"
