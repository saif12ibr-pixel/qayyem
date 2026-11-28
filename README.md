# Qayyem (قيّم)

**AI-Powered Arabic Assignment Grading and Feedback System**

Senior Project II (CS489) — College of Computing & Informatics, Prince Musaid bin Abdulrahman University.
Supervisor: Dr. Saeed AlQarni.

Instructors upload their students' short Arabic answers together with an ideal answer
and an optional rubric. Qayyem grades each answer with a large language model and
returns a preliminary score and individual feedback in formal Arabic. Results appear
in a class dashboard and can be downloaded as a formatted Excel file. Every grade stays
preliminary: the instructor can review and change any score or feedback.

## Features

**Grading**
- Upload a class file (CSV, Excel, or a Word table) with English or Arabic column headings,
  or one answer paper per student (.docx, .pdf or .txt)
- Single questions or whole exams (one answer column per question, each with its own
  ideal answer and marks)
- Marks split into parts, e.g. 4 for the definition and 6 for an example
- Ideal answer typed in, taken from reference material (book or slides as PDF,
  PowerPoint, Word or text), or both
- Batched, rubric-anchored AI grading (10 answers per request) with validation of every
  returned grade; anything invalid is flagged "Needs attention", never saved silently
- Grading runs in the background with a live progress bar

**Results**
- Class dashboard: class average, top 5 students, highest and lowest, and student groups
  (low below 50%, average 50–79%, high 80% and above) listed lowest first
- Instructor review of any answer: edit the score or feedback; the original AI score is kept
- Student search by ID with total, percentage, group, rank and every answer's feedback
- Excel export for the whole class or for one student

**Subjects and question banks**
- Subjects with their own grading guidelines and a question bank split into
  Assignment, Quiz, Midterm and Final
- Import an existing exam from Word; download the bank as Excel

**Accounts, settings and interface**
- Instructor sign-up (can be limited to the university e-mail domain or turned off)
- Choice of AI provider per instructor: Google Gemini (default, free tier), OpenAI GPT-4o,
  Anthropic Claude, DeepSeek; each instructor can add their own encrypted API key and
  test the connection
- Full Arabic interface (right to left) and English, with a light or dark theme

**Security and privacy**
- CSRF protection on every form, login lockout after 5 failed attempts (15 minutes),
  hashed passwords, Fernet-encrypted API keys, no error details shown to users
- Student answers and grades are deleted at sign-out or session expiry, in line with
  the Saudi PDPL; the Excel download is how results are kept

## Tech stack

Python 3.12–3.14 · Flask 3 · SQLite · pandas · openpyxl · pypdf · cryptography ·
Jinja2 + Bootstrap 5 (LTR and RTL) · pytest

## Repository layout

| Folder | Contents |
|---|---|
| [`SOURCE/`](SOURCE/) | Complete application source code, tests, sample data and benchmark |
| [`DATABASE/`](DATABASE/) | Database schema and description of every table |
| [`DOCUMENTS/`](DOCUMENTS/) | Final report (Word and PDF), final defense presentation, screenshots, progress documents |
| [`PREREQUISITES/`](PREREQUISITES/) | Software and tools needed to run the system |
| [`SETUP/`](SETUP/) | Installation, configuration and setup guide (English and Arabic) |
| [`Group-Description.txt`](Group-Description.txt) | Group members, student IDs, project title and supervisor |

## Getting started

On Windows, double-click [`SOURCE/run.bat`](SOURCE/run.bat). It creates the virtual
environment, installs the dependencies, prepares the database, starts the server and
opens the browser on the sign-up page. For manual setup on any operating system, see
[`SETUP/Setup-EN.txt`](SETUP/Setup-EN.txt) or [`SETUP/Setup-AR.txt`](SETUP/Setup-AR.txt).

An AI key is needed to grade: either put a server-wide key in `SOURCE/.env`
(`GEMINI_API_KEY`, free from https://aistudio.google.com/apikey), or let each instructor
add their own under **Settings** in the app. Never commit `.env`.

## Tests

    cd SOURCE
    python -m pytest

656 automated tests, all passing. They run offline with a test grader and need no API
key and no internet connection.

## Team

| Name | Student ID | Role |
|---|---|---|
| Saif Amro Ibrahim | S220008133 | Team Leader |
| Houmood Abdulrahman Algoseyer | S230050613 | AI & Grading Engine Lead |
| Meshari Abdulrahman Alasmari | S220044964 | Backend, Database & Security Lead |
| Salman Ahmed Alharbi | S220042990 | Frontend & Arabic UX Lead |
| Mohammed Jamman Alomari | S220002979 | QA, Testing & Performance Lead |
| Sultan Bander Altowirgi | S220037005 | Documentation & Research Lead |
