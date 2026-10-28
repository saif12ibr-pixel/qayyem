"""English/Arabic interface text.

Every interface string is written in English in the code and looked up in
translations_ar.AR when the instructor has chosen Arabic. A missing entry
falls back to the English text rather than failing, so a new string can
never break a page -- tests/test_i18n.py catches the gap instead.

Placeholders use %(name)s, so the Arabic sentence can put them wherever its
word order needs them.

The choice lives in a cookie rather than the session, because signing out
clears the session and the sign-in page should stay in the chosen language.
"""
from urllib.parse import urlparse

from flask import Blueprint, has_request_context, redirect, request, url_for
from markupsafe import Markup

from .translations_ar import AR

LANGUAGES = ("en", "ar")
COOKIE = "qayyem-lang"

bp = Blueprint("i18n", __name__)


def get_locale():
    if not has_request_context():
        return "en"  # the grading worker and the CLI have no instructor to ask
    lang = request.cookies.get(COOKIE)
    return lang if lang in LANGUAGES else "en"


def gettext(text, **values):
    """Translate `text` for the current request and fill its placeholders."""
    if get_locale() == "ar":
        text = AR.get(text, text)
    return text % values if values else text


def _template_gettext(text, **values):
    # Interface strings are ours and may hold markup such as <strong>; the
    # values come from data (file names, student IDs), so Markup's % escapes
    # them while leaving the string's own markup alone.
    if get_locale() == "ar":
        text = AR.get(text, text)
    return Markup(text) % values if values else Markup(text)


@bp.route("/language/<lang>")
def switch(lang):
    target = request.referrer
    # Only bounce back within this site, so the link cannot be used as an
    # open redirect.
    if not target or urlparse(target).netloc != request.host:
        target = url_for("upload.new")
    response = redirect(target)
    if lang in LANGUAGES:
        response.set_cookie(
            COOKIE, lang, max_age=365 * 24 * 3600, samesite="Lax", httponly=True
        )
    return response


def register(app):
    app.jinja_env.globals["_"] = _template_gettext
    # For text that may come from outside, such as a stored error message: it
    # is translated when it is one of ours, and auto-escaped either way.
    app.jinja_env.filters["translate"] = gettext
    app.register_blueprint(bp)

    @app.context_processor
    def language():
        lang = get_locale()
        return {"lang": lang, "text_dir": "rtl" if lang == "ar" else "ltr"}
