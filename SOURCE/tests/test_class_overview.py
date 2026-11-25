"""Tests for the class overview (top students, groups) and the student search
with its per-student Excel download on the results page."""
import io

from openpyxl import load_workbook

from qayyem.db import get_db
from tests.conftest import INSTRUCTOR_EMAIL

# Scores out of 10: two high (>= 80%), two average (50-79%), three low (< 50%).
SCORES = {"S1": 9.5, "S2": 8, "S3": 7, "S4": 5, "S5": 4.5, "S6": 2, "S7": 0}


def seed_class(app, scores=SCORES, email=INSTRUCTOR_EMAIL):
    with app.app_context():
        db = get_db()
        instructor_id = db.execute("SELECT id FROM instructor WHERE email = ?",
                                   (email,)).fetchone()["id"]
        assignment_id = db.execute(
            "INSERT INTO assignment (instructor_id, title, ideal_answer, max_score, status, "
            "progress_total, progress_done) VALUES (?, 'quiz.csv', 'ideal', 10, 'complete', ?, ?)",
            (instructor_id, len(scores), len(scores)),
        ).lastrowid
        for row, (student, score) in enumerate(scores.items(), start=2):
            response_id = db.execute(
                "INSERT INTO student_response (assignment_id, student_id, response_text, row_number) "
                "VALUES (?, ?, ?, ?)", (assignment_id, student, "answer of " + student, row),
            ).lastrowid
            db.execute("INSERT INTO grading_result (response_id, score, feedback_ar, model_name) "
                       "VALUES (?, ?, 'jayyid', 'test')", (response_id, score))
        db.commit()
        return assignment_id


def page(client, assignment_id):
    return client.get("/results/" + str(assignment_id)).get_data(as_text=True)


def test_top_five_are_the_highest_scores_in_order(client, app, auth):
    assignment_id = seed_class(app)
    auth.login()
    html = page(client, assignment_id)
    top = html.split("Top 5 students")[1].split("Student groups")[0]
    order = [s for s in ("S1", "S2", "S3", "S4", "S5", "S6", "S7") if 'data-show-student="' + s + '"' in top]
    assert order == ["S1", "S2", "S3", "S4", "S5"]
    assert top.index('"S1"') < top.index('"S2"') < top.index('"S5"')
    assert "95%" in top


def test_groups_count_students_and_list_lowest_first(app):
    from qayyem.results import class_overview, student_summaries
    from qayyem.results import _result_rows, with_breakdown
    assignment_id = seed_class(app)
    with app.app_context():
        assignment = get_db().execute("SELECT * FROM assignment WHERE id = ?", (assignment_id,)).fetchone()
        rows = with_breakdown(_result_rows(assignment_id), assignment, [])
        _, ranked = student_summaries(rows, assignment, [])
    overview = class_overview(ranked)
    bands = {band: [s["student_id"] for s in members] for band, members in overview["bands"]}
    assert bands == {"low": ["S7", "S6", "S5"], "average": ["S4", "S3"], "high": ["S2", "S1"]}
    assert [b for b, _ in overview["bands"]] == ["low", "average", "high"]
    assert overview["highest"]["student_id"] == "S1"
    assert overview["lowest"]["student_id"] == "S7"


def test_search_has_a_panel_per_student_with_their_answer(client, app, auth):
    assignment_id = seed_class(app)
    auth.login()
    html = page(client, assignment_id)
    for student in SCORES:
        assert 'class="student-panel mt-3" data-student="' + student + '"' in html
    assert "answer of S3" in html
    assert '<option value="S7">' in html


def test_student_excel_holds_only_that_student(client, app, auth):
    assignment_id = seed_class(app)
    auth.login()
    response = client.get("/results/%d/student.xlsx?student=S3" % assignment_id)
    assert response.status_code == 200
    assert "quiz-S3.xlsx" in response.headers["Content-Disposition"]
    sheet = load_workbook(io.BytesIO(response.data))["Student"]
    values = [c for row in sheet.iter_rows(values_only=True) for c in row if c is not None]
    assert "S3" in values and "answer of S3" in values
    assert "70%" in values and "Average" in values and "3 of 7" in values
    assert "answer of S1" not in values


def test_student_excel_does_not_count_as_downloading_the_results(client, app, auth):
    assignment_id = seed_class(app)
    auth.login()
    client.get("/results/%d/student.xlsx?student=S3" % assignment_id)
    with app.app_context():
        exported = get_db().execute("SELECT exported_at FROM assignment WHERE id = ?",
                                    (assignment_id,)).fetchone()["exported_at"]
    assert exported is None


def test_unknown_student_is_404(client, app, auth):
    assignment_id = seed_class(app)
    auth.login()
    assert client.get("/results/%d/student.xlsx?student=NOPE" % assignment_id).status_code == 404


def test_another_instructors_student_cannot_be_downloaded(client, app, auth):
    assignment_id = seed_class(app, email="other@seu.edu.sa")
    auth.login()
    assert client.get("/results/%d/student.xlsx?student=S1" % assignment_id).status_code == 404
