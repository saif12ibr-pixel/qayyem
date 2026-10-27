"""CSRF protection and login throttling (qayyem/security.py)."""
import re

import pytest

from tests.conftest import INSTRUCTOR_EMAIL, INSTRUCTOR_PASSWORD

TOKEN_RE = re.compile(rb'name="csrf_token" value="([^"]+)"')


def _token(client, path="/login"):
    match = TOKEN_RE.search(client.get(path).data)
    assert match, "page did not render a CSRF token"
    return match.group(1).decode()


@pytest.fixture
def csrf_app(app):
    app.config["CSRF_ENABLED"] = True
    return app


def test_login_form_carries_a_token(csrf_app, client):
    assert TOKEN_RE.search(client.get("/login").data)


def test_post_without_token_is_rejected(csrf_app, client):
    response = client.post(
        "/login", data={"email": INSTRUCTOR_EMAIL, "password": INSTRUCTOR_PASSWORD}
    )
    assert response.status_code == 400
    with client.session_transaction() as sess:
        assert "instructor_id" not in sess


def test_post_with_wrong_token_is_rejected(csrf_app, client):
    _token(client)
    response = client.post(
        "/login",
        data={"email": INSTRUCTOR_EMAIL, "password": INSTRUCTOR_PASSWORD,
              "csrf_token": "forged"},
    )
    assert response.status_code == 400


def test_post_with_valid_token_signs_in(csrf_app, client):
    token = _token(client)
    response = client.post(
        "/login",
        data={"email": INSTRUCTOR_EMAIL, "password": INSTRUCTOR_PASSWORD,
              "csrf_token": token},
    )
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert "instructor_id" in sess


def test_token_from_another_session_is_rejected(csrf_app, app, client):
    stolen = _token(app.test_client())
    _token(client)
    response = client.post(
        "/login",
        data={"email": INSTRUCTOR_EMAIL, "password": INSTRUCTOR_PASSWORD,
              "csrf_token": stolen},
    )
    assert response.status_code == 400


def test_logout_requires_token(csrf_app, client):
    token = _token(client)
    client.post("/login", data={"email": INSTRUCTOR_EMAIL,
                                "password": INSTRUCTOR_PASSWORD, "csrf_token": token})
    # A forged cross-site logout must not end the session or purge data.
    assert client.post("/logout").status_code == 400
    with client.session_transaction() as sess:
        assert "instructor_id" in sess


def test_every_post_form_includes_a_token(csrf_app, client, auth):
    app_token = _token(client)
    client.post("/login", data={"email": INSTRUCTOR_EMAIL,
                                "password": INSTRUCTOR_PASSWORD, "csrf_token": app_token})
    for path in ("/upload", "/settings/"):
        html = client.get(path).data
        forms = re.findall(rb"<form[^>]*method=\"post\"[^>]*>(.*?)</form>", html, re.S)
        assert forms, path
        for body in forms:
            assert b'name="csrf_token"' in body, path


def _fail(client, n):
    for _ in range(n):
        client.post("/login", data={"email": INSTRUCTOR_EMAIL, "password": "wrong"})


def test_login_locks_out_after_repeated_failures(app, client):
    app.config["LOGIN_MAX_ATTEMPTS"] = 3
    _fail(client, 3)
    response = client.post(
        "/login", data={"email": INSTRUCTOR_EMAIL, "password": INSTRUCTOR_PASSWORD}
    )
    # Even the right password is refused while locked out.
    assert response.status_code == 429
    assert b"Too many failed sign-in attempts" in response.data
    with client.session_transaction() as sess:
        assert "instructor_id" not in sess


def test_failures_below_the_limit_still_allow_sign_in(app, client):
    app.config["LOGIN_MAX_ATTEMPTS"] = 3
    _fail(client, 2)
    response = client.post(
        "/login", data={"email": INSTRUCTOR_EMAIL, "password": INSTRUCTOR_PASSWORD}
    )
    assert response.status_code == 302


def test_successful_sign_in_resets_the_count(app, client, auth):
    app.config["LOGIN_MAX_ATTEMPTS"] = 3
    _fail(client, 2)
    auth.login()
    auth.logout(confirm=True)
    _fail(client, 2)
    assert auth.login().status_code == 302


def test_lockout_expires_after_the_window(app, client, monkeypatch):
    app.config["LOGIN_MAX_ATTEMPTS"] = 2
    _fail(client, 2)
    assert client.post("/login", data={"email": INSTRUCTOR_EMAIL,
                                       "password": INSTRUCTOR_PASSWORD}).status_code == 429

    import qayyem.security as security
    real = security.time.monotonic
    monkeypatch.setattr(security.time, "monotonic", lambda: real() + 16 * 60)
    assert client.post("/login", data={"email": INSTRUCTOR_EMAIL,
                                       "password": INSTRUCTOR_PASSWORD}).status_code == 302
