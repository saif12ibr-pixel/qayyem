-- Qayyem schema. Entity names follow the Phase 1 ERD (Figure 12).
--
-- Retention (SS 4.3.4 / SS 2.22, PDPL): student data is session-scoped.
-- Deleting an `assignment` row cascades to every student response and grading
-- result beneath it, which is how logout and session expiry purge student data.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS grading_result;
DROP TABLE IF EXISTS student_response;
DROP TABLE IF EXISTS assignment;
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

CREATE TABLE assignment (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    instructor_id  INTEGER NOT NULL REFERENCES instructor(id) ON DELETE CASCADE,
    title          TEXT NOT NULL,
    ideal_answer   TEXT NOT NULL,
    rubric         TEXT,
    max_score      REAL NOT NULL DEFAULT 10,
    status         TEXT NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending','grading','complete','failed')),
    progress_done  INTEGER NOT NULL DEFAULT 0,
    progress_total INTEGER NOT NULL DEFAULT 0,
    error_message  TEXT,
    exported_at    TEXT,
    created_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE student_response (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER NOT NULL REFERENCES assignment(id) ON DELETE CASCADE,
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
    graded_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assignment_instructor ON assignment(instructor_id);
CREATE INDEX idx_response_assignment   ON student_response(assignment_id);
