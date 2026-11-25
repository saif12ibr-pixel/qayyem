-- Qayyem schema. Entity names follow the Phase 1 ERD (Figure 12).
--
-- Retention (SS 4.3.4 / SS 2.22, PDPL): student data is session-scoped.
-- Deleting an `assignment` row cascades to every student response and grading
-- result beneath it, which is how logout and session expiry purge student data.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS grading_result;
DROP TABLE IF EXISTS student_response;
DROP TABLE IF EXISTS question;
DROP TABLE IF EXISTS assignment;
DROP TABLE IF EXISTS bank_question;
DROP TABLE IF EXISTS subject;
DROP TABLE IF EXISTS instructor;

CREATE TABLE instructor (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT,
    -- Which AI provider this instructor grades with, and their own API key.
    -- The key is encrypted (see qayyem/crypto.py); NULL means "use the key the
    -- server was configured with".
    ai_provider   TEXT,
    ai_model      TEXT,
    api_key_enc   TEXT,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- A course the instructor teaches. Subjects and their question banks are the
-- instructor's own teaching material, not student data, so unlike assignments
-- they are kept across sessions.
CREATE TABLE subject (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    instructor_id INTEGER NOT NULL REFERENCES instructor(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    code          TEXT,
    -- Grading guidelines every question of the subject starts from.
    rubric        TEXT,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- A subject's question bank, typed in or imported from a Word file.
CREATE TABLE bank_question (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id   INTEGER NOT NULL REFERENCES subject(id) ON DELETE CASCADE,
    position     INTEGER NOT NULL,
    text         TEXT NOT NULL,
    -- Multiple choice: JSON [{"label", "text", "correct"}]; NULL when written.
    options      TEXT,
    ideal_answer TEXT,
    rubric       TEXT,
    max_score    REAL NOT NULL DEFAULT 1,
    parts        TEXT
);

CREATE TABLE assignment (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    instructor_id  INTEGER NOT NULL REFERENCES instructor(id) ON DELETE CASCADE,
    subject_id     INTEGER REFERENCES subject(id) ON DELETE SET NULL,
    title          TEXT NOT NULL,
    ideal_answer   TEXT NOT NULL,
    rubric         TEXT,
    max_score      REAL NOT NULL DEFAULT 10,
    -- Marking scheme as JSON [{"name", "marks"}], when marked in parts.
    parts          TEXT,
    -- The question itself, copied from the bank question it was graded
    -- from, so reviewers see what was asked. Choices as in bank_question.
    question_text    TEXT,
    question_options TEXT,
    status        TEXT NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending','grading','complete','failed')),
    progress_done  INTEGER NOT NULL DEFAULT 0,
    progress_total INTEGER NOT NULL DEFAULT 0,
    error_message  TEXT,
    exported_at    TEXT,
    created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- One row per answer column of a multi-question file. A single-question
-- upload has none and keeps its ideal answer, rubric and max score on
-- `assignment`. ideal_answer stays NULL until the instructor fills it in.
CREATE TABLE question (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL REFERENCES assignment(id) ON DELETE CASCADE,
    position      INTEGER NOT NULL,
    title         TEXT NOT NULL,
    ideal_answer  TEXT,
    rubric        TEXT,
    max_score     REAL NOT NULL DEFAULT 10,
    parts         TEXT,
    question_text    TEXT,
    question_options TEXT
);

CREATE TABLE student_response (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL REFERENCES assignment(id) ON DELETE CASCADE,
    question_id   INTEGER REFERENCES question(id) ON DELETE CASCADE,
    student_id    TEXT NOT NULL,
    response_text TEXT,
    row_number    INTEGER NOT NULL
);

CREATE TABLE grading_result (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id INTEGER NOT NULL UNIQUE
                REFERENCES student_response(id) ON DELETE CASCADE,
    score       REAL,
    feedback_ar TEXT,
    model_name  TEXT,
    error       TEXT,
    -- JSON list of per-part scores, in the marking scheme's order.
    part_scores TEXT,
    -- Set when the instructor changes the grade on the results page; ai_score
    -- keeps what the model gave, for the record.
    reviewed_at TEXT,
    ai_score    REAL,
    graded_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assignment_instructor ON assignment(instructor_id);
CREATE INDEX idx_response_assignment   ON student_response(assignment_id);
CREATE INDEX idx_question_assignment   ON question(assignment_id);
CREATE INDEX idx_subject_instructor    ON subject(instructor_id);
CREATE INDEX idx_bank_subject          ON bank_question(subject_id);
