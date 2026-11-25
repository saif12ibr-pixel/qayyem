"""Sign-up, subjects with question banks imported from Word, and reviewing
grades on the results page."""
import io
import json

import pytest
from openpyxl import load_workbook

from qayyem.db import get_db
from qayyem.question_doc import parse_question_doc
from tests.docx_helper import make_docx

EXAM = [
    "Midterm - Operating Systems",
    "1. What is the capital of Saudi Arabia? (1 mark)",
    "a) Jeddah", "b) Riyadh *", "c) Dammam",
    "2. Define an operating system. [5 marks]",
    "* Software that manages the hardware",
    "and runs programs.",
]


@pytest.fixture
def app(app):  # noqa: F811 - deliberately wraps the conftest fixture
    app.config["GRADING_SYNC"] = True
    return app


def make_subject(client, name="Operating Systems", code="IT241"):
    response = client.post("/subjects/", data={"name": name, "code": code})
    assert response.status_code == 302
    return int(response.headers["Location"].rstrip("/").split("/")[-1])


def import_word(client, subject_id, paragraphs=EXAM, **fields):
    data = {"document": (io.BytesIO(make_docx(paragraphs)), "exam.docx")}
    data.update(fields)
    return client.post("/subjects/" + str(subject_id) + "/import", data=data,
                       content_type="multipart/form-data")


def bank(app, subject_id):
    with app.app_context():
        return [dict(r) for r in get_db().execute(
            "SELECT * FROM bank_question WHERE subject_id = ? ORDER BY position",
            (subject_id,))]


# --- sign up -----------------------------------------------------------------

def signup(client, **overrides):
    data = {"full_name": "Dr. Sara", "email": "sara@seu.edu.sa",
            "password": "long-password", "confirm": "long-password"}
    data.update(overrides)
    return client.post("/signup", data=data)


def test_signup_creates_an_account_and_signs_in(client):
    response = signup(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/subjects/")
    assert client.get("/subjects/").status_code == 200

    client.post("/logout")
    response = client.post("/login", data={"email": "sara@seu.edu.sa",
                                           "password": "long-password"})
    assert response.status_code == 302


def test_signup_rejects_a_taken_email(client):
    response = signup(client, email="teacher@seu.edu.sa")
    assert response.status_code == 400
    assert b"already exists" in response.data


@pytest.mark.parametrize("overrides, message", [
    ({"password": "short", "confirm": "short"}, b"at least 8"),
    ({"confirm": "different-password"}, b"do not match"),
    ({"email": "not-an-email"}, b"valid email"),
    ({"full_name": ""}, b"full name"),
])
def test_signup_validation(client, overrides, message):
    response = signup(client, **overrides)
    assert response.status_code == 400
    assert message in response.data


def test_signup_can_be_limited_to_a_domain(client, app):
    app.config["SIGNUP_EMAIL_DOMAINS"] = ["seu.edu.sa"]
    assert signup(client, email="someone@gmail.com").status_code == 400
    assert signup(client).status_code == 302


def test_login_page_links_to_signup(client):
    assert b'href="/signup"' in client.get("/login").data


# --- reading questions from Word -----------------------------------------------

def test_word_questions_with_starred_answers():
    questions, warnings = parse_question_doc("exam.docx", make_docx(EXAM))
    assert warnings == []
    choice, written = questions
    assert choice["text"] == "What is the capital of Saudi Arabia?"
    assert choice["max_score"] == 1
    assert [o["correct"] for o in choice["options"]] == [False, True, False]
    assert choice["ideal_answer"] == "B) Riyadh"
    assert written["options"] is None
    assert written["max_score"] == 5
    assert written["ideal_answer"] == "Software that manages the hardware\nand runs programs."


def test_arabic_word_questions():
    questions, warnings = parse_question_doc("exam.docx", make_docx([
        "١. ما عاصمة المملكة؟ (1 درجة)", "أ- جدة", "ب- الرياض *", "ج- الدمام",
        "السؤال 2: عرّف نظام التشغيل [4 درجات]", "الإجابة: برنامج يدير مكونات الحاسب.",
    ]))
    assert warnings == []
    assert questions[0]["ideal_answer"] == "ب) الرياض"
    assert questions[1]["max_score"] == 4
    assert questions[1]["ideal_answer"] == "برنامج يدير مكونات الحاسب."


def test_word_automatic_numbering():
    questions, _ = parse_question_doc("exam.docx", make_docx([
        ("Capital of Saudi Arabia?", "1", 0), ("Jeddah", "2", 0), ("Riyadh ★", "2", 0),
        ("Define an OS.", "1", 0), "* Software that manages the hardware.",
    ]))
    assert [q["text"] for q in questions] == ["Capital of Saudi Arabia?", "Define an OS."]
    assert questions[0]["ideal_answer"] == "B) Riyadh"
    assert questions[1]["ideal_answer"] == "Software that manages the hardware."


def test_questions_missing_an_answer_are_reported():
    _, warnings = parse_question_doc("exam.docx", make_docx([
        "1. Pick one", "a) x", "b) y", "2. Explain.",
    ]))
    assert warnings == ["Question 1 has choices but none is starred.",
                        "Question 2 has no model answer."]


def test_a_file_without_questions_explains_the_format():
    from qayyem.parsing import ParseError

    with pytest.raises(ParseError, match="star"):
        parse_question_doc("exam.docx", make_docx(["Just a heading"]))
    with pytest.raises(ParseError, match=".docx"):
        parse_question_doc("exam.pdf", b"x")


# --- subjects and their banks -------------------------------------------------

def test_subject_bank_from_word(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    response = import_word(client, subject_id)
    assert response.status_code == 302

    rows = bank(app, subject_id)
    assert [r["position"] for r in rows] == [1, 2]
    assert json.loads(rows[0]["options"])[1] == {"label": "B", "text": "Riyadh", "correct": True}

    page = client.get("/subjects/" + str(subject_id)).data.decode("utf-8")
    assert "option-correct" in page and "&#9733;" in page
    assert "Software that manages the hardware" in page

    # Importing again adds; "replace" starts over.
    import_word(client, subject_id)
    assert len(bank(app, subject_id)) == 4
    import_word(client, subject_id, mode="replace")
    assert len(bank(app, subject_id)) == 2


def test_bank_downloads_as_excel_with_the_correct_answer_starred(client, auth):
    auth.login()
    subject_id = make_subject(client)
    import_word(client, subject_id)
    response = client.get("/subjects/" + str(subject_id) + "/questions.xlsx")
    assert response.status_code == 200
    sheet = load_workbook(io.BytesIO(response.data))["Questions"]
    header = [c.value for c in sheet[1]]
    assert header[:3] == ["No.", "Question", "Type"]
    row = [c.value for c in sheet[2]]
    assert "★ B) Riyadh" in row
    assert row[header.index("Marks")] == 1
    assert sheet[3][header.index("Correct / model answer")].value.startswith("★ Software")


def test_arabic_subject_name_downloads(client, auth):
    auth.login()
    subject_id = make_subject(client, name="نظم التشغيل", code="")
    import_word(client, subject_id)
    response = client.get("/subjects/" + str(subject_id) + "/questions.xlsx")
    assert response.status_code == 200
    assert "filename*=UTF-8''" in response.headers["Content-Disposition"]


def test_add_and_edit_a_question_by_hand(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    url = "/subjects/" + str(subject_id) + "/questions/new"

    response = client.post(url, data={"kind": "choice", "text": "2 + 2?",
                                      "options": "a) 3\nb) 4\nc) 5", "max_score": "1"})
    assert response.status_code == 400
    assert b"star" in response.data

    client.post(url, data={"kind": "choice", "text": "2 + 2?",
                           "options": "3\n4 *\n5", "max_score": "2"})
    [q] = bank(app, subject_id)
    assert q["ideal_answer"] == "B) 4"
    assert q["max_score"] == 2

    edit = "/subjects/" + str(subject_id) + "/questions/" + str(q["id"])
    form = client.get(edit).data.decode("utf-8")
    assert "B) 4 *" in form
    client.post(edit, data={"kind": "written", "text": "Explain addition.",
                            "ideal_answer": "Combining amounts.", "max_score": "3"})
    [q] = bank(app, subject_id)
    assert (q["options"], q["ideal_answer"], q["max_score"]) == (None, "Combining amounts.", 3)

    client.post(edit + "/delete")
    assert bank(app, subject_id) == []


def test_subjects_are_private(client, app, auth):
    auth.login()
    subject_id = make_subject(client, name="Compilers 401")
    client.post("/logout")
    auth.login(email="other@seu.edu.sa")
    assert client.get("/subjects/" + str(subject_id)).status_code == 404
    assert import_word(client, subject_id).status_code == 404
    assert client.get("/subjects/" + str(subject_id) + "/questions.xlsx").status_code == 404
    assert b"Compilers 401" not in client.get("/subjects/").data


def test_subjects_survive_sign_out(client, app, auth):
    """Question banks are teaching material, not student data."""
    auth.login()
    subject_id = make_subject(client)
    import_word(client, subject_id)
    client.post("/logout", data={"confirm": "1"})
    assert len(bank(app, subject_id)) == 2


def test_grading_one_bank_question_prefills_the_upload(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    client.post("/subjects/" + str(subject_id) + "/edit",
                data={"name": "Operating Systems", "rubric": "Accept Arabic or English."})
    import_word(client, subject_id)
    written = bank(app, subject_id)[1]

    page = client.get("/upload?subject=%d&question=%d" % (subject_id, written["id"]))
    html = page.data.decode("utf-8")
    assert "Software that manages the hardware" in html
    assert "Accept Arabic or English." in html
    assert 'value="5"' in html


def test_exam_upload_with_a_subject_fills_each_question_from_the_bank(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    import_word(client, subject_id)

    csv_text = "student_id,answer 1,answer 2\nS001,Riyadh,software that manages hardware\n"
    response = client.post("/upload", data={
        "file": (io.BytesIO(csv_text.encode("utf-8")), "midterm.csv"),
        "subject_id": str(subject_id), "max_score": "10",
    }, content_type="multipart/form-data")
    assert response.status_code == 302
    setup = client.get(response.headers["Location"]).data.decode("utf-8")
    assert "B) Riyadh" in setup
    assert "Software that manages the hardware" in setup
    assert "question bank" in setup

    with app.app_context():
        assignment = get_db().execute("SELECT * FROM assignment ORDER BY id DESC").fetchone()
    assert assignment["subject_id"] == subject_id
    subject_page = client.get("/subjects/" + str(subject_id)).data.decode("utf-8")
    assert "midterm.csv" in subject_page


# --- reviewing grades on the results page -------------------------------------

def graded_assignment(client, app, **fields):
    data = {
        "file": (io.BytesIO(b"student_id,response\nS001,green plants\nS002,light energy\n"),
                 "quiz.csv"),
        "ideal_answer": "Plants turn light energy into chemical energy.",
        "max_score": "10",
    }
    data.update(fields)
    response = client.post("/upload", data=data, content_type="multipart/form-data")
    assignment_id = int(response.headers["Location"].rstrip("/").split("/")[-1])
    with app.app_context():
        rows = get_db().execute(
            """SELECT sr.id, gr.score FROM student_response sr
               JOIN grading_result gr ON gr.response_id = sr.id
               WHERE sr.assignment_id = ? ORDER BY sr.row_number""",
            (assignment_id,)).fetchall()
    return assignment_id, [dict(r) for r in rows]


def test_instructor_changes_a_grade(client, app, auth):
    auth.login()
    assignment_id, rows = graded_assignment(client, app)
    page = client.get("/results/%d" % assignment_id).data.decode("utf-8")
    assert "Review" in page and "green plants" in page  # the student's answer is shown

    client.get("/results/%d/export.xlsx" % assignment_id)
    response = client.post("/results/%d/responses/%d" % (assignment_id, rows[0]["id"]),
                           data={"score": "7.5", "feedback_ar": "إجابة جيدة"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("#r%d" % rows[0]["id"])

    with app.app_context():
        db = get_db()
        result = db.execute("SELECT * FROM grading_result WHERE response_id = ?",
                            (rows[0]["id"],)).fetchone()
        exported = db.execute("SELECT exported_at FROM assignment WHERE id = ?",
                              (assignment_id,)).fetchone()[0]
    assert result["score"] == 7.5
    assert result["feedback_ar"] == "إجابة جيدة"
    assert result["ai_score"] == rows[0]["score"]
    assert result["reviewed_at"]
    assert exported is None  # the earlier download is out of date

    # A second change keeps the model's original score.
    client.post("/results/%d/responses/%d" % (assignment_id, rows[0]["id"]),
                data={"score": "8", "feedback_ar": "ممتاز"})
    with app.app_context():
        ai = get_db().execute("SELECT ai_score FROM grading_result WHERE response_id = ?",
                              (rows[0]["id"],)).fetchone()[0]
    assert ai == rows[0]["score"]

    page = client.get("/results/%d" % assignment_id).data.decode("utf-8")
    assert "1 reviewed" in page

    sheet = load_workbook(io.BytesIO(
        client.get("/results/%d/export.xlsx" % assignment_id).data))["Results"]
    assert sheet["B2"].value == 8
    assert sheet["D2"].value.startswith("Reviewed by the instructor")


def test_a_score_above_the_maximum_is_rejected(client, app, auth):
    auth.login()
    assignment_id, rows = graded_assignment(client, app)
    client.post("/results/%d/responses/%d" % (assignment_id, rows[0]["id"]),
                data={"score": "11"})
    with app.app_context():
        score = get_db().execute("SELECT score FROM grading_result WHERE response_id = ?",
                                 (rows[0]["id"],)).fetchone()[0]
    assert score == rows[0]["score"]


def test_reviewing_a_question_marked_in_parts(client, app, auth):
    auth.login()
    assignment_id, rows = graded_assignment(
        client, app, part_name=["Definition", "Example"], part_marks=["4", "6"])
    url = "/results/%d/responses/%d" % (assignment_id, rows[0]["id"])

    client.post(url, data={"part_score": ["3", "9"]})  # 9 is over the part's 6
    client.post(url, data={"part_score": ["3", "5.5"]})
    with app.app_context():
        result = get_db().execute("SELECT * FROM grading_result WHERE response_id = ?",
                                  (rows[0]["id"],)).fetchone()
    assert json.loads(result["part_scores"]) == [3, 5.5]
    assert result["score"] == 8.5


def test_another_instructor_cannot_change_grades(client, app, auth):
    auth.login()
    assignment_id, rows = graded_assignment(client, app)
    client.post("/logout", data={"confirm": "1"})
    auth.login(email="other@seu.edu.sa")
    response = client.post("/results/%d/responses/%d" % (assignment_id, rows[0]["id"]),
                           data={"score": "0"})
    assert response.status_code == 404


def test_results_list_offers_review(client, app, auth):
    auth.login()
    graded_assignment(client, app)
    page = client.get("/results/").data.decode("utf-8")
    assert ">Review<" in page


# --- reading a Word exam with the AI -------------------------------------------

class StubModel:
    """Stands in for the instructor's AI model and records what it was sent."""

    def __init__(self, reply):
        self.reply = reply
        self.prompts = []

    def complete(self, system, prompt):
        self.prompts.append(prompt)
        return self.reply


AI_REPLY = json.dumps({"questions": [
    {"text": "ما عاصمة المملكة؟", "type": "choice", "model_answer": None, "marks": 2,
     "options": [{"text": "جدة", "correct": False}, {"text": "الرياض", "correct": True}]},
    {"text": "Define an operating system.", "type": "written",
     "options": [], "model_answer": "Software that manages the hardware.", "marks": None},
]}, ensure_ascii=False)

COVER_PAGE = [
    "Saudi Electronic University", "Final exam - read every question carefully",
    "Student name: ________", "Q one) what is the capital (two marks)",
    "Jeddah / Riyadh (correct)", "Explain what an operating system is",
]


def test_the_ai_takes_only_the_questions_from_a_word_file(client, app, auth, monkeypatch):
    model = StubModel(AI_REPLY)
    monkeypatch.setattr("qayyem.subjects.grader_for_instructor", lambda config, row: model)
    auth.login()
    subject_id = make_subject(client)

    response = import_word(client, subject_id, paragraphs=COVER_PAGE)
    assert response.status_code == 302
    assert "Student name" in model.prompts[0]  # the whole file went to the model

    rows = bank(app, subject_id)
    assert [r["text"] for r in rows] == ["ما عاصمة المملكة؟", "Define an operating system."]
    choices = json.loads(rows[0]["options"])
    assert [(o["label"], o["correct"]) for o in choices] == [("أ", False), ("ب", True)]
    assert rows[0]["ideal_answer"] == "ب) الرياض"
    assert rows[0]["max_score"] == 2
    assert rows[1]["options"] is None
    assert rows[1]["ideal_answer"] == "Software that manages the hardware."
    assert rows[1]["max_score"] == 5  # no marks in the file: the written default


def test_without_an_ai_key_the_numbering_is_used(client, app, auth, monkeypatch):
    from qayyem.grading import GraderConfigError

    def no_key(config, row):
        raise GraderConfigError("No key.")

    monkeypatch.setattr("qayyem.subjects.grader_for_instructor", no_key)
    auth.login()
    subject_id = make_subject(client)
    page = import_word(client, subject_id)
    assert page.status_code == 302
    assert len(bank(app, subject_id)) == 2
    html = client.get("/subjects/%d" % subject_id).data.decode("utf-8")
    assert "read by their numbering" in html


def test_a_reply_without_questions_is_reported(client, app, auth, monkeypatch):
    monkeypatch.setattr("qayyem.subjects.grader_for_instructor",
                        lambda config, row: StubModel('{"questions": []}'))
    auth.login()
    subject_id = make_subject(client)
    import_word(client, subject_id, paragraphs=COVER_PAGE)
    assert bank(app, subject_id) == []
    assert "No questions were found" in client.get("/subjects/%d" % subject_id).data.decode()


def test_model_reply_is_checked():
    from qayyem.question_ai import parse_reply

    questions, warnings = parse_reply("```json\n" + json.dumps({"questions": [
        {"text": "Pick one", "type": "choice", "marks": "lots",
         "options": [{"text": "A thing"}, {"text": "Another", "correct": "yes"}]},
        {"text": "  ", "type": "written"},
        {"text": "Only one choice", "type": "choice", "options": [{"text": "x"}]},
    ]}) + "\n```")
    assert [q["text"] for q in questions] == ["Pick one", "Only one choice"]
    assert questions[0]["max_score"] == 1
    assert not any(o["correct"] for o in questions[0]["options"])  # only true counts
    assert questions[1]["options"] is None
    assert len(warnings) == 2


def test_add_question_page_offers_a_word_file(client, auth):
    auth.login()
    subject_id = make_subject(client)
    html = client.get("/subjects/%d/questions/new" % subject_id).data.decode("utf-8")
    assert "Add from a Word file" in html
    assert "/subjects/%d/import" % subject_id in html


# --- the question beside each answer when reviewing ----------------------------

def test_review_shows_the_bank_question_that_was_answered(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    import_word(client, subject_id)
    written = bank(app, subject_id)[1]

    assignment_id, _rows = graded_assignment(
        client, app, subject_id=str(subject_id), bank_question=str(written["id"]),
        ideal_source="text")
    page = client.get("/results/%d" % assignment_id).data.decode("utf-8")
    assert "Define an operating system." in page


def test_review_shows_each_exam_question_and_its_choices(client, app, auth):
    auth.login()
    subject_id = make_subject(client)
    import_word(client, subject_id)

    csv_text = "student_id,answer 1,answer 2\nS001,Riyadh,software that manages hardware\n"
    response = client.post("/upload", data={
        "file": (io.BytesIO(csv_text.encode("utf-8")), "midterm.csv"),
        "subject_id": str(subject_id), "max_score": "10",
    }, content_type="multipart/form-data")
    setup_url = response.headers["Location"]
    with app.app_context():
        ids = [r["id"] for r in get_db().execute(
            "SELECT id FROM question ORDER BY position")]
    data = {}
    for qid, ideal in zip(ids, ("Riyadh", "Software that manages the hardware")):
        data.update({"ideal_answer_%d" % qid: ideal, "ideal_source_%d" % qid: "text",
                     "max_score_%d" % qid: "5"})
    response = client.post(setup_url, data=data, content_type="multipart/form-data")
    page = client.get(response.headers["Location"]).data.decode("utf-8")
    assert "What is the capital of Saudi Arabia?" in page
    assert "B) Riyadh" in page
    assert "Define an operating system." in page
