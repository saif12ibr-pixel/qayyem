"""Questions marked in parts, and choosing where the ideal answer comes from."""
import io
import json
import sqlite3

import pytest
from openpyxl import load_workbook

from qayyem.db import ensure_schema_current, get_db
from qayyem.grading.base import ResponseItem
from qayyem.grading.prompt import build_prompt, validate_results

IDEAL = "Photosynthesis converts light energy into chemical energy."
PARTS = [{"name": "Definition", "marks": 4}, {"name": "Example", "marks": 6}]


@pytest.fixture
def app(app):  # noqa: F811 - deliberately wraps the conftest fixture
    app.config["GRADING_SYNC"] = True
    return app


def post_upload(client, csv_text="student_id,response\nS001," + IDEAL + "\nS002,green\n",
                **fields):
    data = {
        "file": (io.BytesIO(csv_text.encode("utf-8")), "quiz.csv"),
        "ideal_answer": IDEAL,
        "max_score": "10",
    }
    data.update(fields)
    return client.post("/upload", data=data, content_type="multipart/form-data")


def latest_assignment(app):
    with app.app_context():
        return get_db().execute("SELECT * FROM assignment ORDER BY id DESC").fetchone()


# --- prompt and validation -------------------------------------------------

def test_prompt_carries_the_marking_scheme():
    prompt = build_prompt([ResponseItem("S1", "a")], IDEAL, "", 10, PARTS)
    assert "MARKING SCHEME" in prompt
    assert "1. Definition -- 4 marks" in prompt
    assert "2. Example -- 6 marks" in prompt
    assert "part_scores" in prompt


def test_prompt_without_parts_is_unchanged():
    assert "MARKING SCHEME" not in build_prompt([ResponseItem("S1", "a")], IDEAL, "", 10)


def test_part_scores_are_clamped_and_summed():
    raw = [{"student_id": "S1", "score": 99, "part_scores": [3, 9], "feedback_ar": "x"}]
    [result] = validate_results(raw, ["S1"], 10, PARTS)
    assert result.part_scores == (3.0, 6.0)  # 9 clamped to the part's 6 marks
    assert result.score == 9.0               # the parts win over the stated total
    assert result.error is None


def test_missing_part_scores_are_flagged_not_hidden():
    raw = [{"student_id": "S1", "score": 7, "feedback_ar": "x"}]
    [result] = validate_results(raw, ["S1"], 10, PARTS)
    assert result.score == 7
    assert result.part_scores is None
    assert "per-part" in result.error


def test_wrong_number_of_part_scores_is_rejected():
    raw = [{"student_id": "S1", "score": 7, "part_scores": [3], "feedback_ar": "x"}]
    [result] = validate_results(raw, ["S1"], 10, PARTS)
    assert result.part_scores is None


# --- single question in parts ----------------------------------------------

def test_single_question_in_parts_end_to_end(client, app, auth):
    auth.login()
    response = post_upload(client, max_score="99",
                           part_name=["Definition", "Example"], part_marks=["4", "6"])
    assert response.status_code == 302

    assignment = latest_assignment(app)
    assert assignment["max_score"] == 10  # the parts' sum, not the typed 99
    assert json.loads(assignment["parts"]) == PARTS

    with app.app_context():
        row = get_db().execute(
            """SELECT gr.score, gr.part_scores FROM grading_result gr
               JOIN student_response sr ON sr.id = gr.response_id
               WHERE sr.assignment_id = ? AND sr.student_id = 'S001'""",
            (assignment["id"],),
        ).fetchone()
    assert json.loads(row["part_scores"]) == [4, 6]
    assert row["score"] == 10

    page = client.get("/results/" + str(assignment["id"])).data.decode("utf-8")
    assert "Definition 4/4 · Example 6/6" in page

    book = load_workbook(io.BytesIO(
        client.get("/results/" + str(assignment["id"]) + "/export.xlsx").data))
    sheet = book["Results"]
    assert sheet["E1"].value == "Parts"
    assert sheet["E2"].value == "Definition 4/4 · Example 6/6"


def test_a_single_part_is_rejected(client, auth):
    auth.login()
    response = post_upload(client, part_name=["Definition"], part_marks=["4"])
    assert response.status_code == 400
    assert b"at least two parts" in response.data


def test_a_part_without_a_name_is_rejected(client, auth):
    auth.login()
    response = post_upload(client, part_name=["Definition", ""], part_marks=["4", "6"])
    assert response.status_code == 400
    assert b"needs a name" in response.data


def test_blank_part_rows_are_ignored(client, auth):
    auth.login()
    response = post_upload(client, part_name=["", ""], part_marks=["", ""])
    assert response.status_code == 302


# --- exam question in parts ------------------------------------------------

def test_one_exam_question_in_parts(client, app, auth):
    auth.login()
    csv_text = "student_id,answer 1,answer 2\nS001," + IDEAL + ",water\n"
    response = client.post(
        "/upload",
        data={"file": (io.BytesIO(csv_text.encode("utf-8")), "exam.csv"), "max_score": "5"},
        content_type="multipart/form-data",
    )
    assignment_id = int(response.headers["Location"].split("/")[-2])
    with app.app_context():
        q1, q2 = [r["id"] for r in get_db().execute(
            "SELECT id FROM question WHERE assignment_id = ? ORDER BY position",
            (assignment_id,))]

    response = client.post(
        "/upload/" + str(assignment_id) + "/questions",
        data={
            "ideal_answer_" + str(q1): IDEAL, "max_score_" + str(q1): "1",
            "part_name_" + str(q1): ["Definition", "Example"],
            "part_marks_" + str(q1): ["4", "6"],
            "ideal_answer_" + str(q2): "water", "max_score_" + str(q2): "5",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 302

    with app.app_context():
        db = get_db()
        assert db.execute("SELECT max_score FROM assignment WHERE id = ?",
                          (assignment_id,)).fetchone()[0] == 15  # 10 + 5
        q2_parts = db.execute("SELECT parts FROM question WHERE id = ?", (q2,)).fetchone()[0]
    assert q2_parts is None

    page = client.get("/results/" + str(assignment_id)).data.decode("utf-8")
    assert "Definition 4/4 · Example 6/6" in page


# --- choosing the ideal answer's source -------------------------------------

def reference_file(text="Light energy becomes chemical energy in the chloroplast."):
    return (io.BytesIO(text.encode("utf-8")), "chapter.txt")


def test_typed_source_ignores_a_selected_file(client, app, auth):
    auth.login()
    post_upload(client, ideal_source="text", reference=reference_file())
    assert latest_assignment(app)["ideal_answer"] == IDEAL


def test_file_source_ignores_the_typed_answer(client, app, auth):
    auth.login()
    post_upload(client, ideal_source="file", reference=reference_file())
    ideal = latest_assignment(app)["ideal_answer"]
    assert "chloroplast" in ideal
    assert IDEAL not in ideal


def test_file_source_requires_a_file(client, auth):
    auth.login()
    response = post_upload(client, ideal_source="file")
    assert response.status_code == 400
    assert b"Choose a book or slides file" in response.data


def test_both_sources_are_combined(client, app, auth):
    auth.login()
    post_upload(client, ideal_source="both", reference=reference_file())
    ideal = latest_assignment(app)["ideal_answer"]
    assert ideal.startswith(IDEAL)
    assert "chloroplast" in ideal


def test_both_requires_both(client, auth):
    auth.login()
    response = post_upload(client, ideal_source="both")
    assert response.status_code == 400
    assert b"You chose both" in response.data


# --- upgrade of an existing database ---------------------------------------

def test_existing_database_gains_parts_columns(tmp_path):
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
    ensure_schema_current(path)

    conn = sqlite3.connect(path)
    def columns(table):
        return {r[1] for r in conn.execute("PRAGMA table_info(" + table + ")")}
    assert "parts" in columns("assignment")
    assert "parts" in columns("question")
    assert "part_scores" in columns("grading_result")
    conn.close()
