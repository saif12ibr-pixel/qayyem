# Qayyem (قيّم) — SOURCE

AI-powered Arabic assignment grading and feedback system.
Senior Project II (CS489) — College of Computing & Informatics, Prince Musaid bin Abdulrahman University.

An instructor uploads a CSV/Excel file of short Arabic student answers plus an
ideal answer, and Qayyem returns a preliminary score and individual Arabic
feedback for every student, viewable in a dashboard and downloadable as Excel.

## Quick start (Windows)

Double-click **`run.bat`**. It creates the virtual environment, installs
dependencies, prepares the database, starts the server and opens the browser on
the sign-up page, where you create your instructor account. Add an AI key
either in `.env` or under **Settings** in the app. Running it again later
installs any new dependencies and upgrades the database, keeping accounts,
subjects and question banks.

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

Instructors can also create their own account at `/signup`. Set
`SIGNUP_EMAIL_DOMAINS=seu.edu.sa` in `.env` to accept university addresses
only, or `SIGNUP_ENABLED=0` to turn sign-up off and use `create-instructor`.

## Subjects and question banks

Each instructor adds their subjects under **Subjects**. A subject keeps its
own question bank, grading guidelines and grading sessions. Questions are
typed in, or imported from the Word file the exam was written in:

```
1. Which of these schedules processes? (1 mark)
   a) The compiler
   b) The kernel *
   c) The BIOS

2. Define an operating system. [5 marks]
   * Software that manages the computer hardware.
```

A star (`*`) marks the correct choice, or the model answer of a written
question (`Answer:` / `الإجابة:` works too). Arabic numbering and letters
(`١.`, `أ-`) and Word's automatic numbering are understood. The bank downloads
as Excel with the correct answers starred. When grading, choosing the subject
fills each question's model answer, rubric and marks from the bank.

Question banks are teaching material, not student data, so they are kept
across sessions.

## Reviewing grades

On the results page, **Review** opens an answer: the student's text, its
score (or each part's score) and the feedback, all editable. A changed grade
is marked "Reviewed", keeps the AI's original score for the record, and is
noted in the Excel download.

## How it works

```
upload  ->  parse/validate  ->  persist  ->  background worker  ->  poll status
                                                  |
                                          batches of 10 responses
                                                  |
                         AI provider (Gemini, OpenAI, Claude or DeepSeek)
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
run.bat                One-click Windows launcher
qayyem/
  db.py, schema.sql    SQLite access, schema, upgrades, admin CLI
  auth.py              Sign-up, login, session expiry, retention purge
  security.py          CSRF protection and login lockout
  crypto.py            Fernet encryption of instructors' API keys
  settings.py          Provider, model and API key settings, connection test
  upload.py            Upload and start grading
  parsing.py           CSV/Excel/Word tables and answer papers, encodings, headers
  reference.py         Ideal answer from books and slides (PDF, PowerPoint, Word, text)
  results.py           Dashboard, class overview, student search, review, Excel download
  export.py            Excel generation with right-to-left Arabic
  jobs.py              Background grading worker and progress
  subjects.py, bank.py Subjects and their question banks
  question_doc.py      Reads questions and starred answers from Word
  question_ai.py       AI reading of exam Word files for the question bank
  i18n.py,
  translations_ar.py   Arabic / English interface
  grading/
    base.py            The Grader interface
    prompt.py          Prompt construction and reply validation
    gemini.py          Google Gemini (default)
    openai.py          OpenAI GPT-4o
    claude.py          Anthropic Claude
    deepseek.py        DeepSeek
    fake.py            Offline grader — TESTS ONLY
    factory.py         Chooses the grader from settings and configuration
templates/  static/    Server-rendered UI (Bootstrap 5, LTR and RTL, bundled locally)
tests/                 pytest suite
benchmark/             Performance benchmark and its recorded results
sample_data/           Demonstration data
```

## Changing the AI provider

Each instructor chooses the provider and model under **Settings** and can add
their own API key, which is stored encrypted and never sent back to the
browser. **Test connection** grades one sample answer and **Refresh** lists the
models the key can use. Without a personal key, the server-wide key from
`.env` is used.

Only `qayyem/grading/` knows a provider exists. To add a new provider, add one
file implementing `Grader` and register it in `factory.py`.

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

656 tests, all offline — parsing (including UTF-8 BOM and windows-1256 Arabic),
answer papers and exam files, prompt construction, reply validation, all four
providers, encrypted keys, authentication, CSRF and login lockout, ownership
enforcement, session expiry, the retention purge, subjects and question banks,
the Arabic interface, Excel output, and the full upload→grade→download flow.
