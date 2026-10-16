# Database

The application uses **SQLite** — a single file created automatically at
`SOURCE/instance/qayyem.sqlite3` on first run. No database server is required.

`schema.sql` here is a copy of `SOURCE/qayyem/schema.sql`, which is the version
the application actually executes. Edit the one in `SOURCE/`.

## Entities

Names follow the Phase 1 ERD (Figure 12).

| Table | Holds |
|---|---|
| `instructor` | Accounts. Passwords stored as salted hashes, never plain text. |
| `assignment` | One grading run: ideal answer, rubric, max score, status, progress. |
| `student_response` | One uploaded answer, with the spreadsheet row it came from. |
| `grading_result` | The score and Arabic feedback for one response, plus the model used. |

## Retention

Every child foreign key is `ON DELETE CASCADE`, so deleting one `assignment`
removes its responses and results with it. That is the mechanism behind the
requirement that student data not be retained beyond the active session: logout
and session expiry both delete the instructor's assignments.

`instructor` rows are never deleted by this mechanism — only the student data
beneath them.

## Recreating it

    flask --app app init-db      # WARNING: drops all existing tables

## Inspecting it

    sqlite3 SOURCE/instance/qayyem.sqlite3 ".schema"
