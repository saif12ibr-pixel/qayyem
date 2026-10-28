"""Application entry point.

Run the development server with:

    flask --app app run

Qayyem: AI-powered Arabic assignment grading and feedback system.
College of Computing & Informatics, Saudi Electronic University.
"""
import os
from datetime import timedelta

from flask import Flask, render_template

from config import Config
from qayyem import auth, db, i18n, results, security, settings, upload
from qayyem.i18n import gettext as _


def create_app(test_config=None):
    """Build and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    if not app.config.get("DATABASE"):
        os.makedirs(app.instance_path, exist_ok=True)
        app.config["DATABASE"] = os.path.join(app.instance_path, "qayyem.sqlite3")

    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
    app.permanent_session_lifetime = timedelta(
        minutes=int(app.config.get("SESSION_TIMEOUT_MINUTES", 30))
    )
    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")

    db.register(app)
    security.register(app)
    i18n.register(app)
    db.ensure_schema_current(app.config["DATABASE"])
    app.register_blueprint(auth.bp)
    app.register_blueprint(upload.bp)
    app.register_blueprint(results.bp)
    app.register_blueprint(settings.bp)

    @app.errorhandler(400)
    def bad_request(error):
        return render_template("error.html", code=400,
                               message=_(error.description)), 400

    @app.errorhandler(404)
    def not_found(error):  # noqa: ARG001
        return render_template("error.html", code=404,
                               message=_("That page does not exist.")), 404

    @app.errorhandler(413)
    def too_large(error):  # noqa: ARG001
        return render_template("error.html", code=413,
                               message=_("That upload is larger than 8 MB.")), 413

    @app.errorhandler(500)
    def server_error(error):
        # Never show a traceback to the browser; it can leak configuration.
        app.logger.error("Unhandled error: %s", error)
        return render_template("error.html", code=500,
                               message=_("Something went wrong on the server.")), 500

    return app


app = create_app()
