# Qayyem (قيّم) — Project Description

**AI-Powered Arabic Assignment Grading and Feedback System**

Senior Project II (CS489) — continuation of Senior Project I (CS479)
College of Computing & Informatics, Saudi Electronic University, Riyadh

## Team

| Student ID | Name | Role |
|---|---|---|
| S220008133 | Saif Amro Ibrahim | Team Leader — project management, repository & release |
| S230050613 | Houmood Abdulrahman Algoseyer | AI & Grading Engine Lead |
| S220044964 | Meshari Abdulrahman Alasmari | Backend, Database & Security Lead |
| S220042990 | Salman Ahmed Alharbi | Frontend & Arabic UX Lead |
| S220002979 | Mohammed Jamman Alomari | QA, Testing & Performance Lead |
| S220037005 | Sultan Bander Altowirgi | Documentation & Research Lead |

Work distribution, schedule and acceptance criteria are in
[`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md).

**Project Supervisor:** Dr. Saeed AlQarni

## Overview

Instructors in Saudi universities spend substantial time grading short Arabic
text assignments. The delay pushes feedback past the point where it is useful,
and manual marking at volume produces inconsistency between students.

Qayyem is a web application that automates this work. An instructor uploads a
CSV or Excel file of student responses together with an ideal answer and an
optional grading rubric. The system evaluates each response against that
reference using a large language model, then returns a preliminary score and
individual feedback written in formal Arabic. Results appear in a dashboard and
download as a formatted Excel file that drops straight into existing university
workflows.

Grades are presented as preliminary and remain open to instructor revision. The
intent is to remove repetitive work, not to remove academic judgement.

## Objectives

- **Reduce grading time** — target: 100 responses graded in under two minutes
- **Improve consistency** — every response judged against the same rubric-anchored criteria
- **Increase accessibility** — usable by instructors with no technical background
- **Protect student data** — comply with the Saudi Personal Data Protection Law (PDPL)

## Features

1. **Instructor authentication** — session-based login; accounts are created by an administrator, with no public sign-up
2. **Assignment upload** — CSV and Excel, with English or Arabic column headings
3. **AI-powered grading** — batched, rubric-anchored evaluation with validation of every returned result
4. **Results dashboard** — scores and Arabic feedback in a right-to-left table, with live progress while grading runs
5. **Excel export** — formatted workbook with a per-student results sheet and an assignment metadata sheet

## Technology

| Layer | Choice |
|---|---|
| Backend | Python 3.12, Flask 3.0 |
| AI model | Google Gemini via REST (swappable behind one interface) |
| Data processing | pandas |
| Excel output | openpyxl |
| Database | SQLite |
| Frontend | Server-rendered Jinja2 templates, Bootstrap 5 |
| Testing | pytest — 65 tests, fully offline |

### Change from Phase 1

Phase 1 specified the OpenAI GPT-4o API. Implementation moved to Google Gemini,
which offers a free tier adequate for this project's volume while providing
comparable Arabic capability. The grading layer is isolated behind a single
`Grader` interface, so the provider is a configuration change rather than a code
change. Chapter 2 and the Chapter 5 diagrams require updating to reflect this.

## Engineering decisions worth noting

**Batched grading.** Responses are sent 10 per API call rather than one at a
time. This keeps the system inside free-tier rate limits and is what makes the
two-minute target achievable. Because batching introduces the risk of the model
attributing one student's grade to another, every returned item must echo back a
student ID that was sent, carry a score within range, and include non-empty
feedback; anything else is flagged rather than accepted.

**Background grading with polled progress.** A batch takes longer than an HTTP
request should be held open, and the interface is required to show a processing
indicator. Grading therefore runs on a worker thread while the page polls a
status endpoint.

**Session-scoped retention.** Phase 1 required that student data not be retained
beyond the active session, while also defining persistent tables. These are
reconciled by scoping every record to a grading session and cascading deletion on
logout or session expiry. The Excel download is the means of retention, and the
application warns before discarding results that were never downloaded.

## Folder layout

- `DATABASE/` — schema and data model documentation
- `DOCUMENTS/` — project documentation and deliverables
- `PREREQUISITES/` — required tools and dependencies
- `SETUP/` — setup instructions (English and Arabic)
- `SOURCE/` — application source code

## Running it

See `SETUP/Setup-EN.txt` or `SETUP/Setup-AR.txt`. On Windows, double-click
`SOURCE/run.bat`.
