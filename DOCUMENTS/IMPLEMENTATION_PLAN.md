# Implementation Plan — Qayyem (قيّم)

AI-Powered Arabic Assignment Grading and Feedback System
Senior Project II (CS489), College of Computing and Informatics
Saudi Electronic University, Dammam

Prepared by Saif Amro Ibrahim, Team Leader
11 October 2026
Submission and defense: Tuesday 1 December 2026

## 1. Current status

The system runs end to end. An instructor logs in, uploads a CSV or Excel file of Arabic short
answers together with an ideal answer and a rubric, watches grading progress, reviews the
scores and Arabic feedback in a right-to-left dashboard, and downloads a formatted Excel
workbook. Grading sits behind a single interface with four providers implemented, responses
are graded ten per API call to stay inside free-tier limits, every returned item is checked
against the student identifiers we sent, and student data is deleted when the session ends.
The test suite is 137 tests and passes without network access.

Seven gaps remain, and they define the work in this plan.

1. No version control. The project is a folder on one machine.
2. Grading accuracy has never been measured against human marks.
3. The target of 100 responses in under two minutes has never been timed.
4. Forms have no CSRF protection and the login route has no rate limiting.
5. No usability testing. No instructor outside the team has used the interface.
6. The Phase 1 report still describes OpenAI GPT-4o as the only model.
7. No user manual, and no deployment beyond a local batch file.

## 2. Approach

The interface we have now is a placeholder. It was written to prove the backend works, not to
be the delivered product. We will finish and harden the backend first, then rebuild the
frontend properly and give it a real visual design. Doing it in this order avoids building the
interface twice and means it is designed against routes and data that are final.

Two dates control the plan. The backend freezes on Thursday 22 October, after which no backend
features are added and anything unfinished moves to Future Work rather than taking time from
the frontend. From Week 9, Meshari moves off the backend and joins the frontend rebuild as a
second developer, which is what makes three weeks enough for seven templates. The frontend
then freezes on Thursday 12 November, because Weeks 12 to 14 are report integration, release
and rehearsal, and a page restyled in Week 13 would invalidate the screenshots in Chapter 5
and the regression run in Week 11.

Usability testing runs on mockups in Week 8, before the rebuild begins, so the findings can
still change the design instead of arriving too late to act on.

Some scope was reduced to fit eight weeks. The accuracy comparison covers two providers rather
than four, the marked evaluation set is 100 answers rather than 120, mobile layout is
best-effort, and deployment is a WSGI configuration with a written guide rather than a hosted
service. All four reductions are recorded in the report's Future Work chapter.

## 3. Team and roles

| Student | ID | Role |
|---|---|---|
| Saif Amro Ibrahim | S220008133 | Team Leader; repository, integration, release |
| Houmood Abdulrahman Algoseyer | S230050613 | AI and grading engine; accuracy evaluation |
| Meshari Abdulrahman Alasmari | S220044964 | Backend, database and security; frontend from Week 9 |
| Salman Ahmed Alharbi | S220042990 | Frontend and Arabic user experience |
| Mohammed Jamman Alomari | S220002979 | Quality assurance, testing and performance |
| Sultan Bander Altowirgi | S220037005 | Documentation and research |

Each member owns their area completely: the code, its tests, the matching report section, and
the defense questions on it. Roles are fixed from Week 7, since there is no longer time for
anyone to change area.

The leader creates and administers the repository, breaks the plan into assigned issues,
reviews and merges every pull request, runs the Thursday meeting, writes the weekly update,
keeps the contribution record, and enforces the two freeze dates.

## 4. Work assignment

**Saif, Team Leader.** Weeks 7 and 8: create the repository, continuous integration and branch
protection, turn this plan into assigned issues, and chair the backend freeze review. Weeks 9
to 11: review and merge all work, prepare the production configuration and deployment guide.
Weeks 12 to 14: assemble the project CD and the slide deck, run the rehearsals, and write
Chapter 7 with Sultan.

**Houmood, AI and grading engine.** Weeks 7 and 8: write the marking guide, collect and
anonymise 100 Arabic answers across three questions, complete the first marking pass, and write
the evaluation script. Weeks 9 to 11: run the accuracy analysis, compare Gemini against Claude
on the same set, review 40 sampled feedback texts for relevance and tone, and test that an
instruction hidden inside a student answer cannot change a grade. Weeks 12 to 14: the
evaluation sections of Chapter 6 and the engine sections of Chapters 4 and 5.

**Meshari, backend and security.** Weeks 7 and 8: add CSRF protection and login rate limiting,
review the password policy, prove the stored API key is encrypted at rest, audit the retention
purge for orphaned rows, make sure no stack trace or key can reach the user, regenerate the
entity-relationship diagram from the live schema, and write the mapping from each Personal Data
Protection Law obligation to the mechanism that satisfies it. Weeks 9 to 11: second frontend
developer, taking the results pages, login, settings and error pages. Weeks 12 to 14: Chapter 3
with Sultan and the data model section of Chapter 4.

**Salman, frontend and Arabic user experience.** Weeks 7 and 8: audit the placeholder and record
what is wrong with it, define an Arabic-first design system, mock up every screen including
empty and failure states, recruit three to five instructors and run the usability test on the
mockups, and agree the build order. He is also the second independent marker on the evaluation
set, which needs two markers. Weeks 9 to 11: build the new page shell and stylesheet, rebuild
every template, carry out the visual design pass, audit right-to-left and mixed Arabic and
Latin text, and check accessibility and layout at desktop and tablet widths. Weeks 12 to 14:
the interface design section and all screenshots.

**Mohammed, testing and performance.** Weeks 7 and 8: write the test plan with a traceability
matrix back to the Phase 1 requirements, add a test for every security feature as it lands, and
extend the suite to malformed files, wrong encodings, empty answers, duplicate identifiers and
oversized uploads. Weeks 9 to 11: build the rendering tests before the rebuild starts so a
replaced template cannot break quietly, inject API failures including timeouts and rate limits,
run the performance benchmark at 10, 50, 100 and 200 responses, and drive the bug list down to
zero high-severity items. Weeks 12 to 14: the testing sections of Chapter 6 and a final
regression on a clean machine.

**Sultan, documentation and research.** Weeks 7 and 8: agree the report structure, open the
shared reference sheet, and rewrite Chapter 1. Weeks 9 to 11: the literature review with at
least twelve new sources, then Chapters 2 and 3, and first drafts of Chapters 4 to 6. Weeks 12
to 14: integrate the whole report, write the Arabic and English user manuals, regenerate the
diagrams, run the consistency pass, and finalise the references.

Every item above becomes an issue in the repository with an owner and a target week, and closes
with a reviewed pull request. A task counts as finished when it can be demonstrated, not when
the code is written.

## 5. Schedule

The working week is Sunday to Thursday.

| Week | Dates | Main work | Gate |
|---|---|---|---|
| 7 | 11–15 Oct | Repository and CI. Security work begins. Answers collected and marking starts. UI audit, instructors booked. Test plan. Chapter 1. | Repository live, all six have committed |
| 8 | 18–22 Oct | Marking finished, evaluation script written. Retention audit, ER diagram, PDPL mapping. Mockups and usability test. Edge-case tests. | Backend freeze. Evaluation set committed |
| 9 | 25–29 Oct | New page shell and stylesheet, upload page and progress view. First accuracy run. Rendering and failure tests. Literature review. | First accuracy results |
| 10 | 1–5 Nov | Remaining pages rebuilt. Provider comparison and feedback review. Performance benchmark. Chapters 2 and 3. | Performance target measured |
| 11 | 8–12 Nov | Visual design pass, RTL audit, accessibility. Regression and bug burn-down. Deployment setup. Chapters 4 to 6 drafted. | Frontend freeze, no high-severity bugs |
| 12 | 15–19 Nov | Report integration, screenshots, diagrams, manuals, Chapter 7. Project CD. Slide deck. Clean-machine regression. | Full draft to the supervisor |
| 13 | 22–26 Nov | Supervisor feedback applied. Consistency pass and references. Two rehearsals, the second with cross-examination. | Final report and release candidate |
| 14 | 29 Nov–1 Dec | Final run-through, then submission and defense on Tuesday 1 December. | Submitted and defended |

Two items are most likely to delay everything else: the hand-marking in Weeks 7 and 8, which
needs two people working to a written guide, and the backend landing by 22 October. Both are
checked daily rather than weekly.

## 6. Repository and working rules

A private repository named `qayyem`, with all six members as collaborators and the supervisor as
a reader. The layout follows the course deliverable structure, with the evaluation set and its
scripts under `SOURCE/evaluation` and the weekly updates under `DOCUMENTS/weekly`.

The `main` branch stays working and is protected. Work happens on feature branches and arrives
as a pull request with one review from another member; continuous integration runs the test
suite and a failure blocks the merge. Reviews are returned within a day, because on an
eight-week schedule a pull request left for three days costs a week somewhere else. API keys,
environment files, database files and real student data are never committed, and a key that
reaches a commit is revoked the same day. Everyone commits under their own account, since the
history is the main record of who did what.

## 7. Weekly follow-up

The team meets every Thursday for half an hour. Each member says what they finished, what they
will do next, and what is blocking them. The leader writes the update into `DOCUMENTS/weekly`
and posts it to Blackboard the same day. Each update lists the week's completed work with links
to the pull requests that prove it, next week's assignments by member, current blockers,
progress against the next gate, and any questions for the supervisor.

## 8. Report

The Phase 1 report describes a single-provider OpenAI system and no longer matches what was
built, so it is being rewritten rather than patched. Each chapter has one owner, who also
answers for it in the defense.

| Chapter | Owner | Due |
|---|---|---|
| 1. Introduction | Sultan | Week 8 |
| 2. Literature review and related work | Sultan | Week 10 |
| 3. Requirements and analysis | Meshari, Sultan | Week 10 |
| 4. System design and architecture | Houmood, Meshari; interface section by Salman | Week 11 |
| 5. Implementation | Houmood, Meshari; frontend and screenshots by Salman | Week 11 |
| 6. Testing and evaluation | Mohammed, Houmood | Week 11 |
| 7. Conclusion and future work | Sultan, Saif | Week 12 |
| Abstract, references, appendices, user manual | Sultan | Week 12 |

Chapters are written continuously from Week 7. Week 12 integrates chapters that already exist;
it is not the week the report gets written. The consistency pass in Week 13 settles one voice,
one set of Arabic and English terms, uniform numbering of figures and tables, and checks that
every number in Chapters 6 and 7 traces back to a committed experiment.

## 9. Studies and references

Sultan will add at least twelve new peer-reviewed sources published between 2022 and 2026,
alongside the Phase 1 references that remain valid. The review needs to cover automated
short-answer grading and how closely it has been shown to agree with human markers, large
language models used as graders including their known reliability and bias problems, Arabic
natural language processing, Arabic automated grading in particular, the effect of timely
individual feedback on learning, and ethics and privacy in educational technology including the
Saudi Personal Data Protection Law.

Sources come from IEEE Xplore, the ACM Digital Library, the ACL Anthology, SpringerLink,
ScienceDirect and Scopus-indexed journals. Preprints are cited only where no peer-reviewed
equivalent exists and are labelled as preprints. Each source is logged with a one-paragraph
summary and the place in the report it supports before it is cited, and a source that supports
nothing is removed.

## 10. Main risks

1. *The backend runs past 22 October and compresses the rebuild.* The freeze is a date, not a
   condition; unfinished work moves to Future Work. Progress is measured against the freeze from
   Week 7, so a delay is visible in Week 7 rather than Week 8.
2. *Marking the evaluation set slips, leaving no accuracy results.* It starts on the first day of
   Week 7 with two named markers and a written guide, and was reduced to 100 answers so that it
   fits two weeks.
3. *Measured accuracy turns out poor against human marks.* We report it with the analysis.
   Agreement between the two human markers is reported first, so disagreement among people is
   visible before the model is judged. A measured limitation is a better result than an
   unverified claim.
4. *The rebuild does not finish, or breaks working behaviour.* Two developers from Week 9, pages
   rebuilt in priority order with the demonstration path first, the design system in the shared
   page shell so an unfinished page still inherits the new design, and rendering tests written
   before the rebuild starts.
5. *A member falls behind.* Weekly activity is visible in the repository. The leader raises it
   the same week and reassigns if needed, rather than at the end of the semester.

## 11. Record of individual work

Senior Project II is assessed individually, so each member's contribution has to be visible
without anyone having to vouch for it. Three records are kept in the repository: the commit
history under each member's own account, the issues and pull requests assigned to and reviewed
by named members, and a contribution log that the leader updates every Thursday from actual
repository activity rather than from self-report.

For the defense, each member writes a one-page brief on their area in Week 12 covering what it
does, why it was built that way, what the alternatives were, and where its limits are. The
second rehearsal in Week 13 is deliberately adversarial: members question each other's work, and
anyone who cannot answer a question about a part they did not build learns it before the day.
Every member is expected to explain the system as a whole at a high level and their own part in
depth. The demonstration has a recorded fallback in case the network fails in the room.
