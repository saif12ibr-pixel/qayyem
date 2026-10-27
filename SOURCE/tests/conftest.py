"""Shared test fixtures.

Every test runs against a throwaway SQLite file with GRADER=fake, so the whole
suite works offline, costs nothing, and gives identical results on every run.
"""
import os
import sys
import tempfile

import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from qayyem.db import get_db, init_db  # noqa: E402

INSTRUCTOR_EMAIL = "teacher@seu.edu.sa"
INSTRUCTOR_PASSWORD = "password123"


@pytest.fixture
def app():
    handle, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(handle)

    application = create_app(
        {
            "TESTING": True,
            "DATABASE": path,
            "SECRET_KEY": "test-key",
            "GRADER": "fake",
            "GRADING_BATCH_SIZE": 3,
            "MAX_ROWS": 500,
            "SESSION_TIMEOUT_MINUTES": 30,
            # Most tests exercise behaviour, not CSRF; test_security turns it on.
            "CSRF_ENABLED": False,
        }
    )

    with application.app_context():
        init_db()
        db = get_db()
        db.execute(
            "INSERT INTO instructor (email, password_hash, full_name) VALUES (?, ?, ?)",
            (INSTRUCTOR_EMAIL, generate_password_hash(INSTRUCTOR_PASSWORD), "Test Instructor"),
        )
        db.execute(
            "INSERT INTO instructor (email, password_hash, full_name) VALUES (?, ?, ?)",
            ("other@seu.edu.sa", generate_password_hash("password123"), "Other Instructor"),
        )
        db.commit()

    yield application

    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def client(app):
    return app.test_client()


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, email=INSTRUCTOR_EMAIL, password=INSTRUCTOR_PASSWORD):
        return self._client.post(
            "/login", data={"email": email, "password": password}, follow_redirects=False
        )

    def logout(self, confirm=False):
        data = {"confirm": "1"} if confirm else {}
        return self._client.post("/logout", data=data)


@pytest.fixture
def auth(client):
    return AuthActions(client)
