"""SQLite access, schema setup, and the admin CLI commands.

Instructor accounts are created only through the `create-instructor` CLI
command. There is no self-registration route, per SS 4.1 (Product Features,
Instructor Authentication).
"""
import pathlib
import sqlite3

import click
from flask import current_app, g


def open_connection(database_path):
    """Open a connection with foreign keys on and rows as mappings.

    The grading worker runs on its own thread and SQLite connections cannot be
    shared across threads, so the worker calls this directly rather than using
    the request-scoped `get_db`.
    """
    conn = sqlite3.connect(database_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    """Return the connection for the current request, opening it if needed."""
    if "db" not in g:
        g.db = open_connection(current_app.config["DATABASE"])
    return g.db


def close_db(exception=None):  # noqa: ARG001 - Flask passes the exception
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    """Create all tables, dropping any that already exist."""
    db = get_db()
    sql = (pathlib.Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    db.executescript(sql)
    db.commit()


def ensure_schema_current(database_path):
    """Add columns introduced after a database was first created.

    Without this, adding a column would force `init-db`, which drops every
    table -- losing the instructor accounts someone already made. Each ALTER is
    guarded by a check, so this is safe to run on every start.
    """
    conn = open_connection(database_path)
    try:
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(instructor)")}
        if not existing:
            return  # database not initialised yet; init-db will create it
        for column, ddl in (
            ("ai_provider", "ALTER TABLE instructor ADD COLUMN ai_provider TEXT"),
            ("ai_model", "ALTER TABLE instructor ADD COLUMN ai_model TEXT"),
            ("api_key_enc", "ALTER TABLE instructor ADD COLUMN api_key_enc TEXT"),
        ):
            if column not in existing:
                conn.execute(ddl)
        conn.commit()
    finally:
        conn.close()


def purge_instructor_data(conn, instructor_id):
    """Delete every assignment owned by an instructor.

    ON DELETE CASCADE removes the student responses and grading results beneath
    them, which is how SS 4.3.4 ("must not be retained beyond the active
    session") is enforced at logout and at session expiry.

    Returns the number of assignments removed.
    """
    cur = conn.execute("DELETE FROM assignment WHERE instructor_id = ?", (instructor_id,))
    conn.commit()
    return cur.rowcount


@click.command("init-db")
def init_db_command():
    """Initialise the database (destroys existing data)."""
    init_db()
    click.echo("Database initialised.")


@click.command("create-instructor")
@click.option("--email", prompt=True)
@click.option("--name", prompt="Full name", default="", show_default=False)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
def create_instructor_command(email, name, password):
    """Create an instructor account."""
    from werkzeug.security import generate_password_hash

    email = email.strip().lower()
    if len(password) < 8:
        raise click.ClickException("Password must be at least 8 characters.")

    db = get_db()
    try:
        db.execute(
            "INSERT INTO instructor (email, password_hash, full_name) VALUES (?, ?, ?)",
            (email, generate_password_hash(password), name or None),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise click.ClickException(f"An account already exists for {email}.")
    except sqlite3.OperationalError as exc:
        raise click.ClickException(
            f"{exc}. Run 'flask --app app init-db' first."
        )
    click.echo(f"Instructor account created for {email}.")


@click.command("list-instructors")
def list_instructors_command():
    """List instructor accounts."""
    rows = get_db().execute(
        "SELECT id, email, full_name, created_at FROM instructor ORDER BY id"
    ).fetchall()
    if not rows:
        click.echo("No instructor accounts yet.")
        return
    for r in rows:
        click.echo(f"{r['id']:>3}  {r['email']:<32} {r['full_name'] or '-'}")


def register(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_instructor_command)
    app.cli.add_command(list_instructors_command)
