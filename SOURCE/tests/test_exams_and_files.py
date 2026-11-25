"""A subject's question bank kept per exam (assignment, quiz, midterm, final),
and grading from several files at once, including Word, PDF and text papers."""
import io
import sqlite3
import zipfile

import pytest
from openpyxl import load_workbook

from qayyem.db import ensure_schema_current, get_db
from qayyem.parsing import ParseError, parse_submissions
from tests.docx_helper import make_docx

IDEAL = "Photosynthesis converts light energy into chemical energy."
EXAM = [
    "1. What is the capital of Saudi Arabia? (1 mark)",
    "a) Jeddah", "b) Riyadh *", "c) Dammam",
    "2. Define an operating system. [5 marks]",
    "* Software that manages the hardware",
]
_W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


@pytest.fixture
def app(app):  # noqa: F811 - deliberately wraps the conftest fixture
    app.config["GRADING_SYNC"] = True
    return app


def make_subject(client):
    response = client.post("/subjects/", data={"name": "Biology", "code": "BIO101"})
    return int(response.headers["Location"].rstrip("/").split("/")[-1])


def bank(app, subject_id):
    with app.app_context():
        return [dict(r) for r in get_db().execute(
            "SELECT * FROM bank_question WHERE subject_id = ? ORDER BY exam_type, position",
            (subject_id,))]


def add_question(client, subject_id, text, exam, answer="An answer."):
    return client.post("/subjects/%d/questions/new" % subject_id, data={
        "kind": "written", "text": text, "ideal_answer": answer, "max_score": "5",
        "exam_type": exam})


def latest_assignment(app):
    with app.app_context():
        return get_db().execute("SELECT * FROM assignment ORDER BY id DESC").fetchone()


def docx_table(rows):
    """A Word file holding one table."""
    cells = "".join(
        "<w:tr>" + "".join("<w:tc><w:p><w:r><w:t>%s</w:t></w:r></w:p></w:tc>" % c for c in row)
        + "</w:tr>" for row in rows)
    xml = "<w:document %s><w:body><w:tbl>%s</w:tbl></w:body></w:document>" % (_W, cells)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return stream.getvalue()


# --- the question bank, per exam --------------------------------------------

def test_questions_are_saved_to_the_chosen_exam(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    add_question(client, subject_id, "Quiz question one", "quiz")
    add_question(client, subject_id, "Final question one", "final")
    add_question(client, subject_id, "Quiz question two", "quiz")

    rows = bank(app, subject_id)
    assert [(r["exam_type"], r["position"], r["text"]) for r in rows] == [
        ("final", 1, "Final question one"),
        ("quiz", 1, "Quiz question one"),
        ("quiz", 2, "Quiz question two"),
    ]


def test_subject_page_shows_one_exam_at_a_time(client, auth):
    auth.login()
    subject_id = make_subject(client)
    add_question(client, subject_id, "Quiz question", "quiz")
    add_question(client, subject_id, "Midterm question", "midterm")

    quiz = client.get("/subjects/%d?exam=quiz" % subject_id).data.decode("utf-8")
    assert "Quiz question" in quiz and "Midterm question" not in quiz
    midterm = client.get("/subjects/%d?exam=midterm" % subject_id).data.decode("utf-8")
    assert "Midterm question" in midterm and "Quiz question" not in midterm


def test_bank_can_be_searched(client, auth):
    auth.login()
    subject_id = make_subject(client)
    add_question(client, subject_id, "Explain photosynthesis", "final")
    add_question(client, subject_id, "Explain respiration", "final")

    page = client.get("/subjects/%d?exam=final&q=PHOTO" % subject_id).data.decode("utf-8")
    assert "Explain photosynthesis" in page and "Explain respiration" not in page


def test_word_import_goes_to_the_exam_it_was_sent_from(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    client.post("/subjects/%d/import" % subject_id, content_type="multipart/form-data",
                data={"document": (io.BytesIO(make_docx(EXAM)), "mid.docx"),
                      "exam_type": "midterm"})
    rows = bank(app, subject_id)
    assert len(rows) == 2 and {r["exam_type"] for r in rows} == {"midterm"}


def test_replacing_on_import_keeps_the_other_exams(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    add_question(client, subject_id, "Quiz question", "quiz")
    add_question(client, subject_id, "Old final question", "final")
    client.post("/subjects/%d/import" % subject_id, content_type="multipart/form-data",
                data={"document": (io.BytesIO(make_docx(EXAM)), "final.docx"),
                      "exam_type": "final", "mode": "replace"})
    texts = [r["text"] for r in bank(app, subject_id)]
    assert "Quiz question" in texts and "Old final question" not in texts


def test_moving_a_question_renumbers_both_exams(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    add_question(client, subject_id, "First", "quiz")
    add_question(client, subject_id, "Second", "quiz")
    add_question(client, subject_id, "Third", "midterm")
    first = bank(app, subject_id)[1]  # ordered midterm, quiz, quiz
    assert first["text"] == "First"

    client.post("/subjects/%d/questions/%d" % (subject_id, first["id"]), data={
        "kind": "written", "text": "First", "ideal_answer": "An answer.",
        "max_score": "5", "exam_type": "midterm"})
    rows = bank(app, subject_id)
    assert [(r["exam_type"], r["position"], r["text"]) for r in rows] == [
        ("midterm", 1, "Third"), ("midterm", 2, "First"), ("quiz", 1, "Second")]


def test_existing_database_gains_the_exam_columns(tmp_path):
    path = str(tmp_path / "old.sqlite")
    conn = sqlite3.connect(path)
    conn.executescript(
        """CREATE TABLE instructor (id INTEGER PRIMARY KEY, email TEXT,
                                    password_hash TEXT, full_name TEXT);
           CREATE TABLE assignment (id INTEGER PRIMARY KEY);
           CREATE TABLE student_response (id INTEGER PRIMARY KEY);
           CREATE TABLE grading_result (id INTEGER PRIMARY KEY);"""
    )
    conn.close()

    ensure_schema_current(path)

    conn = sqlite3.connect(path)
    assert "exam_type" in {r[1] for r in conn.execute("PRAGMA table_info(bank_question)")}
    assert "exam_type" in {r[1] for r in conn.execute("PRAGMA table_info(assignment)")}
    conn.close()


# --- grading against one exam of the bank -----------------------------------

def test_upload_page_lists_only_the_chosen_exam(client, auth):
    auth.login()
    subject_id = make_subject(client)
    add_question(client, subject_id, "Quiz question", "quiz")
    add_question(client, subject_id, "Final question", "final")

    page = client.get("/upload?subject=%d&exam=final" % subject_id).data.decode("utf-8")
    assert "Final question" in page and "Quiz question" not in page


def test_exam_file_is_filled_from_that_exam(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    add_question(client, subject_id, "Quiz Q1", "quiz", answer="quiz answer")
    add_question(client, subject_id, "Final Q1", "final", answer="final answer one")
    add_question(client, subject_id, "Final Q2", "final", answer="final answer two")

    csv = "student_id,answer 1,answer 2\nS1,a,b\n"
    response = client.post("/upload", content_type="multipart/form-data", data={
        "file": (io.BytesIO(csv.encode()), "final.csv"), "subject_id": str(subject_id),
        "exam_type": "final", "max_score": "10"})
    assert latest_assignment(app)["exam_type"] == "final"
    page = client.get(response.headers["Location"]).data.decode("utf-8")
    assert "final answer one" in page and "final answer two" in page
    assert "quiz answer" not in page


def test_results_and_export_name_the_exam(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    response = client.post("/upload", content_type="multipart/form-data", data={
        "file": (io.BytesIO(("student_id,response\nS1," + IDEAL + "\n").encode()), "q.csv"),
        "subject_id": str(subject_id), "exam_type": "quiz",
        "ideal_answer": IDEAL, "max_score": "10"})
    assert "Quiz" in client.get(response.headers["Location"]).data.decode("utf-8")

    export = client.get("/results/%d/export.xlsx" % latest_assignment(app)["id"])
    sheet = load_workbook(io.BytesIO(export.data))["Assignment"]
    assert {row[0]: row[1] for row in sheet.iter_rows(values_only=True)}["Exam"] == "Quiz"


# --- several files, and Word / PDF / text papers ----------------------------

def test_two_class_lists_are_graded_together():
    exam = parse_submissions([
        ("section1.csv", b"student_id,response\nS1,one\nS2,two\n"),
        ("section2.csv", b"student_id,response\nS3,three\n"),
    ])
    assert [s["student_id"] for s in exam["students"]] == ["S1", "S2", "S3"]
    rows = [s["row_number"] for s in exam["students"]]
    assert rows == sorted(rows) and len(set(rows)) == 3


def test_a_student_in_two_files_is_rejected():
    with pytest.raises(ParseError, match="appears in both"):
        parse_submissions([("a.csv", b"student_id,response\nS1,x\n"),
                           ("b.csv", b"student_id,response\nS1,y\n")])


def test_word_table_is_read_as_a_class_list():
    data = docx_table([["Student ID", "Answer"], ["S1", "first answer"], ["S2", "second"]])
    exam = parse_submissions([("class.docx", data)])
    assert [(s["student_id"], s["answers"][0]) for s in exam["students"]] == [
        ("S1", "first answer"), ("S2", "second")]


def test_word_papers_one_per_student():
    exam = parse_submissions([
        ("paper1.docx", make_docx(["Student ID: 441001", IDEAL])),
        ("441002.docx", make_docx(["Light becomes chemical energy."])),
    ])
    assert [(s["student_id"], s["answers"][0]) for s in exam["students"]] == [
        ("441001", IDEAL), ("441002", "Light becomes chemical energy.")]


def test_arabic_id_line_on_a_text_paper():
    paper = "الرقم الجامعي: 441003\nالإجابة هنا".encode("utf-8")
    [student] = parse_submissions([("x.txt", paper)])["students"]
    assert student["student_id"] == "441003"
    assert student["answers"][0] == "الإجابة هنا"


def test_a_paper_holding_the_whole_exam_is_split_by_question():
    paper = "Student ID: S1\nQ1: first answer\nmore of it\nQ2) second\n1. a point\nQ3 third"
    exam = parse_submissions([("s1.txt", paper.encode())])
    assert exam["questions"] == ["Q1", "Q2", "Q3"]
    assert exam["students"][0]["answers"] == [
        "first answer\nmore of it", "second\n1. a point", "third"]


def test_arabic_numbering_splits_a_paper():
    paper = "السؤال الأول\nإجابة أ\nالسؤال الثاني\nإجابة ب".encode("utf-8")
    exam = parse_submissions([("441001.txt", paper)])
    assert exam["students"][0]["answers"] == ["إجابة أ", "إجابة ب"]
    paper = "س١: أ\nس٢: ب".encode("utf-8")
    assert parse_submissions([("441002.txt", paper)])["students"][0]["answers"] == ["أ", "ب"]


def test_papers_follow_the_class_list_questions():
    exam = parse_submissions([
        ("exam.csv", b"student_id,answer 1,answer 2\nS1,a,b\n"),
        ("S2.txt", b"1. first\n2. second"),
        ("S3.txt", b"1. only the first"),
    ])
    assert [s["answers"] for s in exam["students"]] == [
        ["a", "b"], ["first", "second"], ["only the first", ""]]


def test_unnumbered_paper_in_a_whole_exam_is_rejected():
    with pytest.raises(ParseError, match="not numbered"):
        parse_submissions([("S1.txt", b"just one block of text")], question_count=3)


def test_unsupported_file_is_named():
    with pytest.raises(ParseError, match="photo.png"):
        parse_submissions([("photo.png", b"\x89PNG")])


def test_an_empty_paper_is_rejected():
    with pytest.raises(ParseError, match="No text"):
        parse_submissions([("S1.txt", b"   \n  ")])


def test_papers_are_split_to_the_chosen_bank_exam(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    add_question(client, subject_id, "Final Q1", "final", answer="final answer one")
    add_question(client, subject_id, "Final Q2", "final", answer="final answer two")

    response = client.post("/upload", content_type="multipart/form-data", data={
        "file": [(io.BytesIO(b"Q1 photosynthesis\nQ2 respiration"), "A1.txt"),
                 (io.BytesIO(b"Q1 light"), "A2.txt")],
        "subject_id": str(subject_id), "exam_type": "final", "max_score": "10"})
    assert "/questions" in response.headers["Location"]
    row = latest_assignment(app)
    with app.app_context():
        answers = [r["response_text"] for r in get_db().execute(
            "SELECT response_text FROM student_response WHERE assignment_id = ? "
            "ORDER BY row_number, question_id", (row["id"],))]
    assert answers == ["photosynthesis", "respiration", "light", ""]


def test_upload_grades_several_papers(client, app, auth):
    auth.login()
    response = client.post("/upload", content_type="multipart/form-data", data={
        "file": [(io.BytesIO(make_docx(["Student ID: A1", IDEAL])), "a.docx"),
                 (io.BytesIO(b"Light energy only."), "A2.txt")],
        "ideal_answer": IDEAL, "max_score": "10"})
    assert response.status_code == 302
    row = latest_assignment(app)
    assert row["title"] == "a.docx and 1 more"
    with app.app_context():
        students = [r["student_id"] for r in get_db().execute(
            "SELECT student_id FROM student_response WHERE assignment_id = ? "
            "ORDER BY row_number", (row["id"],))]
    assert students == ["A1", "A2"]
