# Qayyem (قيّم) — SOURCE

AI-powered Arabic assignment grading and feedback system.
Senior Project II (CS489) — College of Computing & Informatics, Saudi Electronic University.

An instructor uploads a CSV/Excel file of short Arabic student answers plus an
ideal answer, and Qayyem returns a preliminary score and individual Arabic
feedback for every student, viewable in a dashboard and downloadable as Excel.

## Quick start (Windows)

Double-click **`run.bat`**. It creates the virtual environment, installs
dependencies, prepares the database, asks you to create a login, and starts the
server. Run it again after adding your API key.

## Manual setup

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux

pip install -r requirements.txt

copy .env.example .env            # then paste your key into GEMINI_API_KEY
flask --app app init-db
flask --app app create-instructor
flask --app app run
```

Open <http://127.0.0.1:5000>.

Get a free API key at <https://aistudio.google.com/apikey>.

## Commands

| Command | Purpose |
|---|---|
| `flask --app app init-db` | Create the database (**erases existing data**) |
| `flask --app app create-instructor` | Add an instructor account |
| `flask --app app list-instructors` | List accounts |
| `flask --app app run` | Start the server |
| `python -m pytest` | Run the test suite (offline, no API key needed) |

There is deliberately no sign-up page: accounts are created only with
`create-instructor`, per the Product Features section of the Phase 1 report.

## How it works

```
upload  ->  parse/validate  ->  persist  ->  background worker  ->  poll status
                                                  |
                                          batches of 10 responses
                                                  |
                                            Gemini API (JSON)
                                                  |
                                       validate + store per student
                                                  |
                                     dashboard  +  Excel download
```

Responses are graded **10 per API call** rather than one at a time. That keeps
the system inside free-tier rate limits and meets the performance target of 100
responses in under two minutes. Because batching risks the model confusing one
student for another, every returned item must echo back a `student_id` we sent,
carry a score within range, and include non-empty feedback — anything else is
flagged rather than silently accepted.

Grading runs on a worker thread, so a long batch cannot time out the HTTP
request, and the results page polls `/results/<id>/status` to show progress.

## Layout

```
app.py                 Flask application factory and entry point
config.py              Configuration, read from .env
qayyem/
  db.py, schema.sql    SQLite access, schema, admin CLI
  auth.py              Login, session expiry, retention purge
  upload.py            Upload and start grading
  results.py           Dashboard, status polling, Excel download
  parsing.py           CSV/Excel reading, encoding and header handling
  export.py            Excel generation with right-to-left Arabic
  jobs.py              Background grading worker and progress
  grading/
    base.py            The Grader interface
    prompt.py          Prompt construction and reply validation
    gemini.py          Gemini implementation
    fake.py            Offline grader — TESTS ONLY
    factory.py         Chooses the grader from configuration
templates/  static/    Server-rendered UI (Bootstrap 5)
tests/                 pytest suite
sample_data/           Demonstration data
```

## Changing the AI provider

Only `qayyem/grading/` knows a provider exists. To swap models, set
`GEMINI_MODEL` in `.env`; to swap providers, add one file implementing `Grader`
and register it in `factory.py`.

> **`GRADER=fake` performs no AI inference.** It scores by word overlap and
> exists so the test suite runs offline at no cost. Never present its output as
> the system's grading.

## Data retention

Student responses and grades are deleted when the instructor signs out or the
session expires, so student data is not retained beyond the active session. The
Excel download is the means of keeping results. If you sign out with results you
have not downloaded, the app warns you first.

## Tests

```bash
python -m pytest
```

65 tests, all offline — parsing (including UTF-8 BOM and windows-1256 Arabic),
prompt construction, reply validation, authentication, ownership enforcement,
session expiry, the retention purge, Excel output, and the full
upload→grade→download flow.
