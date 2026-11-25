"""Subjects and their question banks: the lookups the subject pages and the
upload pages share."""
import json

from flask import abort, g

from .db import get_db

# A subject's question bank holds one exam of each type.
EXAM_TYPES = ("assignment", "quiz", "midterm", "final")


def exam_type(raw):
    """`raw` if it names an exam type, otherwise the first one."""
    return raw if raw in EXAM_TYPES else EXAM_TYPES[0]


def subjects():
    """The signed-in instructor's subjects, with how many questions each has."""
    return get_db().execute(
        """SELECT s.*,
                  (SELECT COUNT(*) FROM bank_question b WHERE b.subject_id = s.id)
                      AS question_count,
                  (SELECT COALESCE(SUM(b.max_score), 0) FROM bank_question b
                    WHERE b.subject_id = s.id) AS total_marks
           FROM subject s
           WHERE s.instructor_id = ?
           ORDER BY s.name COLLATE NOCASE""",
        (g.instructor["id"],),
    ).fetchall()


def owned_subject(subject_id, missing=404):
    """A subject of the signed-in instructor; 404 for anyone else's, so ids
    cannot be probed. With missing=None, returns None instead."""
    row = None
    if subject_id:
        row = get_db().execute(
            "SELECT * FROM subject WHERE id = ? AND instructor_id = ?",
            (subject_id, g.instructor["id"]),
        ).fetchone()
    if row is None and missing:
        abort(missing)
    return row


def questions(subject_id, exam=None):
    """A subject's questions, or with `exam` just that exam's, in order."""
    if exam is None:
        return get_db().execute(
            "SELECT * FROM bank_question WHERE subject_id = ? "
            "ORDER BY exam_type, position, id",
            (subject_id,),
        ).fetchall()
    return get_db().execute(
        "SELECT * FROM bank_question WHERE subject_id = ? AND exam_type = ? "
        "ORDER BY position, id",
        (subject_id, exam),
    ).fetchall()


def exam_counts(subject_id):
    """How many questions each of the subject's exams has, by exam type."""
    counts = dict.fromkeys(EXAM_TYPES, 0)
    for row in get_db().execute(
        "SELECT exam_type, COUNT(*) AS n FROM bank_question WHERE subject_id = ? "
        "GROUP BY exam_type",
        (subject_id,),
    ):
        counts[row["exam_type"]] = row["n"]
    return counts


def next_position(subject_id, exam):
    return get_db().execute(
        "SELECT COALESCE(MAX(position), 0) + 1 FROM bank_question "
        "WHERE subject_id = ? AND exam_type = ?",
        (subject_id, exam),
    ).fetchone()[0]


def owned_question(subject_id, question_id):
    row = get_db().execute(
        "SELECT * FROM bank_question WHERE id = ? AND subject_id = ?",
        (question_id, subject_id),
    ).fetchone()
    if row is None:
        abort(404)
    return row


def options(question):
    return json.loads(question["options"]) if question["options"] else None


def renumber(subject_id):
    """Close the gaps a deleted or moved question leaves, so each exam's
    numbers stay 1, 2, 3..."""
    db = get_db()
    for exam in EXAM_TYPES:
        ids = [r["id"] for r in questions(subject_id, exam)]
        db.executemany("UPDATE bank_question SET position = ? WHERE id = ?",
                       [(n, qid) for n, qid in enumerate(ids, start=1)])
