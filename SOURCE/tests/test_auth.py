"""Tests for authentication, ownership, and the retention purge.

Covers UC-1, UC-6, and the controls behind SS 4.3.2, SS 4.3.3 and SS 4.3.4.
"""
from datetime import datetime, timedelta, timezone

from flask import session

from qayyem.db import get_db
from tests.conftest import INSTRUCTOR_EMAIL, INSTRUCTOR_PASSWORD


def seed_assignment(app, instructor_email=INSTRUCTOR_EMAIL, status="complete"):
    """Create an assignment with one graded response and return its id."""
    with app.app_context():
        db = get_db()
        instructor_id = db.execute(
            "SELECT id FROM instructor WHERE email = ?", (instructor_email,)
        ).fetchone()["id"]
        cursor = db.execute(
            "INSERT INTO assignment (instructor_id, title, ideal_answer, max_score, "
            "status, progress_total, progress_done) VALUES (?, ?, ?, ?, ?, 1, 1)",
            (instructor_id, "seed.csv", "ideal", 10, status),
        )
        assignment_id = cursor.lastrowid
        response = db.execute(
            "INSERT INTO student_response (assignment_id, student_id, response_text, row_number) "
            "VALUES (?, 'S001', 'answer', 2)",
            (assignment_id,),
        )
        db.execute(
            "INSERT INTO grading_result (response_id, score, feedback_ar, model_name) "
            "VALUES (?, 8, 'jayyid', 'test')",
            (response.lastrowid,),
        )
        db.commit()
        return assignment_id


def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Instructor sign in" in response.data


def test_no_self_registration_route(client):
    """SS 4.1: accounts are created by an administrator only."""
    assert client.get("/register").status_code == 404
    assert client.post("/register").status_code == 404


def test_successful_login_sets_session(client, app):
    with client:
        response = client.post(
            "/login", data={"email": INSTRUCTOR_EMAIL, "password": INSTRUCTOR_PASSWORD}
        )
        assert response.status_code == 302
        assert session.get("instructor_id") is not None


def test_login_is_case_insensitive_on_email(client):
    response = client.post(
        "/login", data={"email": INSTRUCTOR_EMAIL.upper(), "password": INSTRUCTOR_PASSWORD}
    )
    assert response.status_code == 302


def test_wrong_password_is_rejected(client):
    response = client.post(
        "/login", data={"email": INSTRUCTOR_EMAIL, "password": "wrong"}, follow_redirects=True
    )
    assert b"Incorrect email or password" in response.data


def test_unknown_email_gives_same_message(client):
    """Identical wording, so the form cannot enumerate real accounts."""
    response = client.post(
        "/login", data={"email": "nobody@seu.edu.sa", "password": "x"}, follow_redirects=True
    )
    assert b"Incorrect email or password" in response.data


def test_protected_routes_redirect_anonymous_users(client):
    for path in ("/upload", "/results/", "/results/1", "/results/1/status"):
        response = client.get(path)
        assert response.status_code == 302, path
        assert "/login" in response.headers["Location"], path


def test_instructor_cannot_read_another_instructors_results(client, app, auth):
    """SS 4.3.2: student data must not be exposed to unauthorised users."""
    other_id = seed_assignment(app, instructor_email="other@seu.edu.sa")
    auth.login()
    assert client.get("/results/" + str(other_id)).status_code == 404
    assert client.get("/results/" + str(other_id) + "/status").status_code == 404
    assert client.get("/results/" + str(other_id) + "/export.xlsx").status_code == 404


def test_logout_purges_student_data(client, app, auth):
    """SS 4.3.4: data is not retained beyond the active session."""
    seed_assignment(app)
    auth.login()
    auth.logout(confirm=True)

    with app.app_context():
        db = get_db()
        assert db.execute("SELECT COUNT(*) c FROM assignment").fetchone()["c"] == 0
        assert db.execute("SELECT COUNT(*) c FROM student_response").fetchone()["c"] == 0
        assert db.execute("SELECT COUNT(*) c FROM grading_result").fetchone()["c"] == 0


def test_logout_warns_before_discarding_undownloaded_results(client, app, auth):
    seed_assignment(app)
    auth.login()
    response = auth.logout(confirm=False)

    assert response.status_code == 302
    with app.app_context():
        # Nothing deleted yet: the instructor must confirm first.
        assert get_db().execute("SELECT COUNT(*) c FROM assignment").fetchone()["c"] == 1


def test_logout_without_pending_results_needs_no_confirmation(client, app, auth):
    seed_assignment(app, status="failed")
    auth.login()
    auth.logout(confirm=False)
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) c FROM assignment").fetchone()["c"] == 0


def test_expired_session_is_rejected_and_purged(client, app, auth):
    """SS 4.3.3: sessions expire after inactivity."""
    seed_assignment(app)
    auth.login()

    stale = (datetime.now(timezone.utc) - timedelta(minutes=120)).isoformat()
    with client.session_transaction() as sess:
        sess["last_seen"] = stale

    response = client.get("/upload")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) c FROM assignment").fetchone()["c"] == 0


def test_password_is_not_stored_in_plain_text(app):
    with app.app_context():
        row = get_db().execute(
            "SELECT password_hash FROM instructor WHERE email = ?", (INSTRUCTOR_EMAIL,)
        ).fetchone()
        assert INSTRUCTOR_PASSWORD not in row["password_hash"]
        assert len(row["password_hash"]) > 20
