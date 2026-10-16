# Qayyem (قيّم)

**AI-Powered Arabic Assignment Grading and Feedback System**

Senior Project II (CS489) — College of Computing & Informatics, Saudi Electronic University, Riyadh.
Supervisor: Dr. Saeed AlQarni.

Instructors upload a CSV or Excel file of short Arabic student answers along with an
ideal answer and an optional rubric. Qayyem grades each response with a large language
model and returns a preliminary score and individual feedback in formal Arabic. Results
appear in a right-to-left dashboard and can be downloaded as a formatted Excel file.
Grades remain preliminary and open to instructor revision.

## Features

- Instructor login (accounts created by an administrator, no public sign-up)
- CSV / Excel upload with English or Arabic column headings
- Batched, rubric-anchored AI grading with validation of every result
- Pluggable AI providers: Google Gemini (default, free tier), OpenAI, Anthropic Claude, DeepSeek
- Live grading progress and an Arabic RTL results dashboard
- Excel export with per-student results and assignment metadata
- Session-scoped data retention, in line with the Saudi PDPL

## Tech stack

Python 3.12 · Flask 3 · pandas · openpyxl · SQLite · Jinja2 + Bootstrap 5 · pytest

## Repository layout

| Folder | Contents |
|---|---|
| [`SOURCE/`](SOURCE/) | Application source code and tests |
| [`DATABASE/`](DATABASE/) | Schema and data model |
| [`DOCUMENTS/`](DOCUMENTS/) | Project description, implementation plan, weekly updates |
| [`PREREQUISITES/`](PREREQUISITES/) | Required tools and dependencies |
| [`SETUP/`](SETUP/) | Setup instructions (English and Arabic) |

## Getting started

On Windows, double-click [`SOURCE/run.bat`](SOURCE/run.bat). It sets up the environment,
prepares the database, and starts the server. To set it up by hand, see
[`SOURCE/README.md`](SOURCE/README.md) or [`SETUP/Setup-EN.txt`](SETUP/Setup-EN.txt) /
[`SETUP/Setup-AR.txt`](SETUP/Setup-AR.txt).

Copy `SOURCE/.env.example` to `SOURCE/.env` and add your API key. Never commit `.env`.

## Team

| Name | Role |
|---|---|
| Saif Amro Ibrahim | Team Leader |
| Houmood Abdulrahman Algoseyer | AI & Grading Engine Lead |
| Meshari Abdulrahman Alasmari | Backend, Database & Security Lead |
| Salman Ahmed Alharbi | Frontend & Arabic UX Lead |
| Mohammed Jamman Alomari | QA, Testing & Performance Lead |
| Sultan Bander Altowirgi | Documentation & Research Lead |
