"""Instructor authentication, session expiry, and the retention purge.

Accounts are created only by the `create-instructor` CLI command; there is no
self-registration route, per SS 4.1.

Three requirements meet in this module:
  SS 4.3.3  passwords are hashed, sessions expire after inactivity
  SS 4.3.4  student data is not retained beyond the active session
  UC-6      logout terminates the session and returns to the login page
"""
import functools
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from . import security
from .db import get_db, purge_instructor_data

bp = Blueprint("auth", __name__)

LAST_SEEN = "last_seen"
USER_ID = "instructor_id"


def _now():
    return datetime.now(timezone.utc)


@bp.before_app_request
def load_instructor():
    """Attach the signed-in instructor to `g`, expiring idle sessions first."""
    g.instructor = None
    instructor_id = session.get(USER_ID)
    if instructor_id is None:
        return

    timeout = int(current_app.config.get("SESSION_TIMEOUT_MINUTES", 30))
    last_seen_raw = session.get(LAST_SEEN)
    if last_seen_raw:
        try:
            last_seen = datetime.fromisoformat(last_seen_raw)
        except ValueError:
            last_seen = None
        if last_seen is not None:
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            if _now() - last_seen > timedelta(minutes=timeout):
                # Idle too long. Purge this instructor's student data before
                # dropping the session, so expiry honours SS 4.3.4 the same way
                # an explicit logout does.
                _purge(instructor_id)
                session.clear()
                flash("Your session expired after inactivity. Please sign in again.", "warning")
                return

    row = get_db().execute(
        "SELECT id, email, full_name FROM instructor WHERE id = ?", (instructor_id,)
    ).fetchone()
    if row is None:
        session.clear()
        return

    g.instructor = row
    session[LAST_SEEN] = _now().isoformat()


def _purge(instructor_id):
    try:
        purge_instructor_data(get_db(), instructor_id)
    except Exception:  # noqa: BLE001 - never block sign-out on a purge failure
        current_app.logger.exception("Purge failed for instructor %s", instructor_id)


def pending_unexported(instructor_id):
    """Count completed result sets the instructor has not downloaded."""
    return get_db().execute(
        "SELECT COUNT(*) AS n FROM assignment "
        "WHERE instructor_id = ? AND status = 'complete' AND exported_at IS NULL",
        (instructor_id,),
    ).fetchone()["n"]


@bp.app_context_processor
def inject_pending():
    """Expose the undownloaded count so the layout can guard the logout button."""
    if g.get("instructor") is None:
        return {"pending_exports": 0}
    try:
        return {"pending_exports": pending_unexported(g.instructor["id"])}
    except Exception:  # noqa: BLE001 - never break rendering over a badge
        return {"pending_exports": 0}


def login_required(view):
    """Redirect anonymous visitors to the login page."""

    @functools.wraps(view)
    def wrapped(**kwargs):
        if g.get("instructor") is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)

    return wrapped


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.get("instructor") is not None:
        return redirect(url_for("upload.new"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        throttle = security.throttle()
        key = security.client_key()
        max_attempts = int(current_app.config.get("LOGIN_MAX_ATTEMPTS", 5))
        window = 60 * int(current_app.config.get("LOGIN_LOCKOUT_MINUTES", 15))
        wait = throttle.retry_after(key, max_attempts, window)
        if wait:
            minutes = (wait + 59) // 60
            flash("Too many failed sign-in attempts. Try again in "
                  + str(minutes) + " minute(s).", "danger")
            return render_template("login.html"), 429

        row = get_db().execute(
            "SELECT * FROM instructor WHERE email = ?", (email,)
        ).fetchone()

        # One message for both branches, so the form cannot be used to discover
        # which email addresses have accounts.
        if row is None or not check_password_hash(row["password_hash"], password):
            throttle.record_failure(key)
            flash("Incorrect email or password.", "danger")
        else:
            throttle.reset(key)
            session.clear()
            session.permanent = True
            session[USER_ID] = row["id"]
            session[LAST_SEEN] = _now().isoformat()
            destination = request.args.get("next") or ""
            if not destination.startswith("/"):
                destination = url_for("upload.new")
            return redirect(destination)

    return render_template("login.html")


@bp.route("/logout", methods=("POST",))
@login_required
def logout():
    """End the session and purge this instructor's student data.

    Because the purge is irreversible, an instructor holding results they never
    downloaded is asked to confirm first -- otherwise a routine logout would
    silently discard a completed grading run.
    """
    instructor_id = g.instructor["id"]
    pending = pending_unexported(instructor_id)

    if pending and not request.form.get("confirm"):
        flash(
            "You have " + str(pending) + " graded result set(s) you have not "
            "downloaded, and signing out deletes them. Download them first, or "
            "use “Sign out and delete” to go ahead.",
            "warning",
        )
        return redirect(url_for("results.index"))

    _purge(instructor_id)
    session.clear()
    flash("You have been signed out and the student data was deleted.", "success")
    return redirect(url_for("auth.login"))
