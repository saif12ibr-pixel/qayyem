"""Per-instructor AI provider and API key (Settings page).

Instructors can grade with their own account rather than the server's. The key
is encrypted before storage and is never sent back to the browser -- the page
shows a masked form of it, which is enough to recognise which key is saved
without disclosing it.

Leaving the key blank keeps whatever the server was configured with, so the
application still works for an instructor who never opens this page.
"""
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

from .auth import login_required
from .crypto import decrypt_key, encrypt_key, mask_key
from .db import get_db
from .grading import GraderConfigError, GraderTransientError, ResponseItem
from .grading.factory import (
    DEFAULT_MODELS,
    KNOWN_MODELS,
    SELECTABLE_PROVIDERS,
    build_grader,
    list_models,
)

bp = Blueprint("settings", __name__, url_prefix="/settings")


def grader_for_instructor(config, instructor_row):
    """Build the grader an instructor's settings call for.

    Falls back to the server's configuration for anything the instructor has
    not set, so a half-configured account still grades rather than failing.
    """
    provider = (instructor_row["ai_provider"] or "").strip() or None
    model = (instructor_row["ai_model"] or "").strip() or None
    api_key = decrypt_key(config.get("SECRET_KEY"), instructor_row["api_key_enc"])
    return build_grader(config, provider=provider, api_key=api_key, model=model)


def grading_readiness(config, instructor_row):
    """Report whether this instructor can grade right now, and with what.

    Without this, a missing key is only discovered after an upload has been
    parsed and the background job has failed -- which for a full class means
    waiting through a batch to be told nothing worked. Checking up front turns
    that into a message before any work is wasted.

    Returns a dict the upload page renders directly.
    """
    provider = (instructor_row["ai_provider"] or config.get("GRADER") or "gemini").lower()

    # The offline stub needs no key, so it is "ready" -- but it performs no
    # inference, and someone running it should be told plainly rather than
    # seeing a reassuring green message and assuming they are grading with AI.
    if provider == "fake":
        return {
            "ok": True,
            "provider": "the offline test grader (no AI, for testing only)",
            "note": "",
            "source": "no key -- it scores by word overlap",
        }

    entry = next((p for p in SELECTABLE_PROVIDERS if p["name"] == provider), None)
    title = entry["title"] if entry else provider
    note = entry["note"] if entry else ""

    # A one-line version of the provider warning, so the constraint is visible
    # on the page where a class is about to be uploaded.
    caution = None
    if provider == "gemini":
        caution = ("Free tier: a large class may reach the request limit and stop "
                   "part way. Your responses are kept, so you can grade again "
                   "once the limit resets.")
    elif provider == "openai":
        caution = "Usage is charged to the OpenAI account this key belongs to."
    elif provider == "claude":
        caution = "Usage is charged to the Anthropic account this key belongs to."
    elif provider == "deepseek":
        caution = ("Usage is charged to the DeepSeek account this key belongs to, "
                   "and requests are processed on servers in China.")

    own_key = decrypt_key(config.get("SECRET_KEY"), instructor_row["api_key_enc"])
    if own_key:
        return {"ok": True, "provider": title, "note": note,
                "source": "your own key", "caution": caution}

    if _server_key_available(config, provider):
        return {"ok": True, "provider": title, "note": note,
                "source": "the key this server is configured with",
                "caution": caution}

    return {
        "ok": False,
        "provider": title,
        "note": note,
        "source": None,
        "message": "No API key is available for " + title + ", so grading cannot run yet.",
    }


SERVER_KEY_NAMES = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}


def _server_key(config, provider):
    """The key the server itself was configured with for this provider."""
    return config.get(SERVER_KEY_NAMES.get(provider, ""), "")


def _server_key_available(config, provider):
    return bool(_server_key(config, provider))


@bp.route("/", methods=("GET", "POST"))
@login_required
def index():
    db = get_db()
    row = db.execute(
        "SELECT * FROM instructor WHERE id = ?", (g.instructor["id"],)
    ).fetchone()
    secret = current_app.config.get("SECRET_KEY")

    if request.method == "POST":
        action = request.form.get("action", "save")

        if action == "refresh_models":
            # Prefer a key just typed into the form over the saved one, so the
            # list can be checked before committing to saving the key.
            provider = (request.form.get("provider") or row["ai_provider"]
                        or current_app.config.get("GRADER") or "gemini").lower()
            typed = (request.form.get("api_key") or "").strip()
            key = typed or decrypt_key(secret, row["api_key_enc"]) or _server_key(
                current_app.config, provider
            )
            try:
                found = list_models(provider, key)
            except Exception as exc:  # noqa: BLE001 - reported to the instructor
                flash("Could not fetch the model list: " + str(exc)[:200], "warning")
            else:
                if found:
                    session["model_list"] = {"provider": provider, "models": found}
                    flash(
                        "Found {0} model(s) your key can use.".format(len(found)),
                        "success",
                    )
                else:
                    flash("That key returned no usable grading models.", "warning")
            return redirect(url_for("settings.index"))

        if action == "clear_key":
            db.execute(
                "UPDATE instructor SET api_key_enc = NULL WHERE id = ?",
                (g.instructor["id"],),
            )
            db.commit()
            flash("Your API key was removed. Grading will use the server's key.", "success")
            return redirect(url_for("settings.index"))

        provider = (request.form.get("provider") or "").strip().lower()
        valid = {p["name"] for p in SELECTABLE_PROVIDERS}
        if provider not in valid:
            flash("Choose a provider from the list.", "danger")
            return redirect(url_for("settings.index"))

        model = (request.form.get("model") or "").strip() or DEFAULT_MODELS[provider]
        submitted_key = (request.form.get("api_key") or "").strip()

        # A blank key field means "leave what is stored alone", so an instructor
        # can change model or provider without re-typing their key.
        if submitted_key:
            db.execute(
                "UPDATE instructor SET ai_provider = ?, ai_model = ?, api_key_enc = ? "
                "WHERE id = ?",
                (provider, model, encrypt_key(secret, submitted_key), g.instructor["id"]),
            )
        else:
            db.execute(
                "UPDATE instructor SET ai_provider = ?, ai_model = ? WHERE id = ?",
                (provider, model, g.instructor["id"]),
            )
        db.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("settings.index"))

    # A list fetched from the account wins over the curated starting list, but
    # only for the provider it was fetched for.
    fetched = session.get("model_list") or {}

    stored_key = decrypt_key(secret, row["api_key_enc"])
    key_unreadable = bool(row["api_key_enc"]) and stored_key is None
    active_provider = (row["ai_provider"] or current_app.config.get("GRADER") or "gemini")

    model_choices = dict(KNOWN_MODELS)
    if fetched.get("provider") in model_choices and fetched.get("models"):
        model_choices[fetched["provider"]] = fetched["models"]

    return render_template(
        "settings.html",
        providers=SELECTABLE_PROVIDERS,
        default_models=DEFAULT_MODELS,
        model_choices=model_choices,
        models_are_live=bool(fetched.get("models")
                             and fetched.get("provider") == active_provider),
        current_provider=active_provider,
        current_model=row["ai_model"] or DEFAULT_MODELS.get(active_provider, ""),
        masked_key=mask_key(stored_key),
        has_own_key=bool(stored_key),
        key_unreadable=key_unreadable,
        server_key_available=_server_key_available(current_app.config, active_provider),
    )


@bp.route("/test", methods=("POST",))
@login_required
def test_connection():
    """Grade one throwaway response to prove the key and model work.

    Finding out your key is wrong while a class's worth of responses is being
    graded is a bad time to find out, so this offers a one-call check.
    """
    row = get_db().execute(
        "SELECT * FROM instructor WHERE id = ?", (g.instructor["id"],)
    ).fetchone()

    try:
        grader = grader_for_instructor(current_app.config, row)
        results = grader.grade_batch(
            [ResponseItem("TEST-1", "الماء سائل.")],
            "الماء سائل شفاف "
            "لا لون له.",
            "Award marks for accuracy.",
            10,
        )
    except GraderConfigError as exc:
        flash("Configuration problem: " + str(exc), "danger")
    except GraderTransientError as exc:
        flash("Could not reach the provider: " + str(exc), "warning")
    except Exception as exc:  # noqa: BLE001 - surface anything else as a message
        flash("Test failed: " + str(exc)[:300], "danger")
    else:
        if results and results[0].score is not None:
            flash(
                "Connection works. {0} returned a score of {1} and Arabic feedback.".format(
                    grader.name, results[0].score
                ),
                "success",
            )
        else:
            note = results[0].error if results else "no result returned"
            flash("The provider responded, but the reply was unusable: " + str(note), "warning")

    return redirect(url_for("settings.index"))
