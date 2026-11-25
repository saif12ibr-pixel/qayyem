"""Instructor authentication, session expiry, and the retention purge.

Instructors create their own account on the sign-up page, which can be
switched off or limited to the university's email domain in config.py; the
`create-instructor` CLI command remains for administrators.

Three requirements meet in this module:
  SS 4.3.3  passwords are hashed, sessions expire after inactivity
  SS 4.3.4  student data is not retained beyond the active session
  UC-6      logout terminates the session and returns to the login page
"""
import functools
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
import re
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from . import security
from .db import get_db, purge_instructor_data
from .i18n import gettext as _

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
                flash(_("Your session expired after inactivity. Please sign in again."), "warning")
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
            flash(_("Too many failed sign-in attempts. Try again in %(minutes)s minute(s).",
                    minutes=minutes), "danger")
            return render_template("login.html"), 429

        row = get_db().execute(
            "SELECT * FROM instructor WHERE email = ?", (email,)
        ).fetchone()

        # One message for both branches, so the form cannot be used to discover
        # which email addresses have accounts.
        if row is None or not check_password_hash(row["password_hash"], password):
            throttle.record_failure(key)
            flash(_("Incorrect email or password."), "danger")
        else:
            throttle.reset(key)
            _sign_in(row["id"])
            destination = request.args.get("next") or ""
            if not destination.startswith("/"):
                destination = url_for("upload.new")
            return redirect(destination)

    return render_template("login.html")


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 8


def _sign_in(instructor_id):
    session.clear()
    session.permanent = True
    session[USER_ID] = instructor_id
    session[LAST_SEEN] = _now().isoformat()


def _signup_errors(name, email, password, confirm):
    errors = []
    if not name:
        errors.append(_("Enter your full name."))
    if not EMAIL_RE.match(email):
        errors.append(_("Enter a valid email address."))
    else:
        domains = current_app.config.get("SIGNUP_EMAIL_DOMAINS") or []
        if domains and email.rsplit("@", 1)[1] not in domains:
            errors.append(_("Sign up with your university email (%(domains)s).",
                            domains=", ".join("@" + d for d in domains)))
    if len(password) < MIN_PASSWORD:
        errors.append(_("The password must be at least %(count)s characters.",
                        count=MIN_PASSWORD))
    elif password != confirm:
        errors.append(_("The two passwords do not match."))
    return errors


@bp.route("/signup", methods=("GET", "POST"))
def signup():
    if not current_app.config.get("SIGNUP_ENABLED", True):
        abort(404)
    if g.get("instructor") is not None:
        return redirect(url_for("upload.new"))

    form = {"full_name": "", "email": ""}
    if request.method == "POST":
        form = {
            "full_name": (request.form.get("full_name") or "").strip(),
            "email": (request.form.get("email") or "").strip().lower(),
        }
        password = request.form.get("password") or ""

        # Shares the sign-in throttle, so the form cannot be used to create
        # accounts, or probe for existing ones, at speed.
        throttle = security.throttle()
        key = security.client_key()
        max_attempts = int(current_app.config.get("LOGIN_MAX_ATTEMPTS", 5))
        window = 60 * int(current_app.config.get("LOGIN_LOCKOUT_MINUTES", 15))
        if throttle.retry_after(key, max_attempts, window):
            flash(_("Too many attempts. Try again later."), "danger")
            return render_template("signup.html", form=form), 429

        errors = _signup_errors(form["full_name"], form["email"], password,
                                request.form.get("confirm") or "")
        if not errors:
            db = get_db()
            try:
                instructor_id = db.execute(
                    "INSERT INTO instructor (email, password_hash, full_name) VALUES (?, ?, ?)",
                    (form["email"], generate_password_hash(password), form["full_name"]),
                ).lastrowid
                db.commit()
            except sqlite3.IntegrityError:
                throttle.record_failure(key)
                errors.append(_("An account already exists for that email. Sign in instead."))
            else:
                _sign_in(instructor_id)
                flash(_("Welcome to Qayyem, %(name)s. Your account is ready.",
                        name=form["full_name"]), "success")
                return redirect(url_for("subjects.index"))

        for message in errors:
            flash(message, "danger")
        return render_template("signup.html", form=form), 400

    return render_template("signup.html", form=form)


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
            _("You have %(count)s graded result set(s) you have not downloaded, and "
              "signing out deletes them. Download them first, or use “Sign out and "
              "delete” to go ahead.", count=pending),
            "warning",
        )
        return redirect(url_for("results.index"))

    _purge(instructor_id)
    session.clear()
    flash(_("You have been signed out and the student data was deleted."), "success")
    return redirect(url_for("auth.login"))
