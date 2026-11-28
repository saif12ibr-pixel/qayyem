# Database

The application uses **SQLite**: a single file created automatically at
`SOURCE/instance/qayyem.sqlite3` on first run. No database server is required.

`schema.sql` in this folder is a copy of `SOURCE/qayyem/schema.sql`, which is the
version the application actually executes. Edit the one in `SOURCE/` and copy it here.

## Tables

The core names (`instructor`, `assignment`, `student_response`, `grading_result`)
follow the Senior Project I ERD (Figure 12 of the report). `subject`, `bank_question`
and `question` were added in Senior Project II for subjects, question banks and
multi-question exams.

| Table | Holds | Kept after sign-out? |
|---|---|---|
| `instructor` | Accounts: e-mail, salted password hash, full name, chosen AI provider and model, and the instructor's own API key (encrypted with Fernet). | Yes |
| `subject` | A course the instructor teaches, with its code and grading guidelines. | Yes |
| `bank_question` | A subject's question bank: question text, exam type (assignment, quiz, midterm, final), choices for multiple-choice questions, model answer, rubric, marks and mark parts. | Yes |
| `assignment` | One grading session: ideal answer, rubric, maximum score, mark parts, status (pending, grading, complete, failed), progress, and when it was exported. | No |
| `question` | One question of a multi-question exam upload, with its own ideal answer, rubric and marks. Single-question uploads have none. | No |
| `student_response` | One student's answer, with the row of the uploaded file it came from. | No |
| `grading_result` | The score and Arabic feedback for one answer, the model used, per-part scores, any error, and — if the instructor reviewed it — the review time and the original AI score. | No |

## Relationships

```
instructor 1 ──< subject 1 ──< bank_question
     │               │
     │               └ (optional) ┐
     └──────────────< assignment >┘
                         │
                         ├──< question
                         └──< student_response 1 ── 1 grading_result
                                   (optionally linked to a question)
```

- An instructor has many subjects and many assignments.
- A subject has many bank questions. An assignment may belong to a subject
  (`ON DELETE SET NULL`, so deleting a subject keeps its sessions).
- An assignment has many questions (multi-question exams) and many student responses.
- Each student response has exactly one grading result.

## Retention (Saudi PDPL)

Every table below `assignment` uses `ON DELETE CASCADE`, so deleting one
`assignment` removes its questions, responses and results with it. Sign-out and
session expiry delete the instructor's assignments, which is how student data is
not kept beyond the active session.

`instructor`, `subject` and `bank_question` are never deleted by this mechanism:
they hold accounts and teaching material, not student data.

## Creating and upgrading

    flask --app app init-db      # creates every table — WARNING: drops existing data

When the application starts on an existing database it adds any columns introduced
by newer versions, keeping all accounts, subjects and question banks. `run.bat` relies
on this, so `init-db` is only needed once.

## Inspecting it

    sqlite3 SOURCE/instance/qayyem.sqlite3 ".schema"
