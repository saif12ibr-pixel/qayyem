"""Cross-site request forgery protection and login throttling.

Two gaps from the implementation plan are closed here:
  CSRF   every state-changing request must carry a per-session token that a
         page on another site cannot read, so it cannot submit our forms
  Login  repeated failed sign-ins from one address are locked out for a
         while, so passwords cannot be guessed at speed

Both are kept in-process with no extra dependency. The throttle lives in memory,
which suits the single-process deployment this project targets; a multi-worker
deployment would move it to a shared store.
"""
import hmac
import secrets
import threading
import time

from flask import abort, current_app, request, session

CSRF_KEY = "_csrf_token"
CSRF_FIELD = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def csrf_token():
    """Return this session's token, creating it on first use."""
    token = session.get(CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_KEY] = token
    return token


def _check_csrf():
    if request.method not in UNSAFE_METHODS:
        return
    if not current_app.config.get("CSRF_ENABLED", True):
        return
    expected = session.get(CSRF_KEY)
    sent = request.form.get(CSRF_FIELD) or request.headers.get(CSRF_HEADER) or ""
    # compare_digest so the check takes the same time however much matches.
    if not expected or not hmac.compare_digest(expected, sent):
        abort(400, description="The form expired or did not come from this site. "
                               "Reload the page and try again.")


class LoginThrottle:
    """Count failed sign-ins per client address within a sliding window."""

    def __init__(self):
        self._failures = {}
        self._lock = threading.Lock()

    def _recent(self, key, window, now):
        stamps = [t for t in self._failures.get(key, []) if now - t < window]
        if stamps:
            self._failures[key] = stamps
        else:
            self._failures.pop(key, None)
        return stamps

    def retry_after(self, key, max_attempts, window):
        """Seconds until `key` may try again, or 0 if it is not locked out."""
        now = time.monotonic()
        with self._lock:
            stamps = self._recent(key, window, now)
            if len(stamps) < max_attempts:
                return 0
            return max(1, int(window - (now - stamps[0])))

    def record_failure(self, key):
        with self._lock:
            self._failures.setdefault(key, []).append(time.monotonic())

    def reset(self, key):
        with self._lock:
            self._failures.pop(key, None)


def throttle():
    return current_app.extensions["qayyem_login_throttle"]


def client_key():
    return request.remote_addr or "unknown"


def register(app):
    app.extensions["qayyem_login_throttle"] = LoginThrottle()
    app.before_request(_check_csrf)
    app.jinja_env.globals["csrf_token"] = csrf_token
