"""Prompt construction and validation of what the model sends back.

The prompt is rubric-anchored: every call carries the ideal answer, the
instructor's rubric and the maximum score, so each response is judged against
the same explicit criteria (SS 2.16, SS 2.7).

Feedback is requested in formal Modern Standard Arabic and must name one
strength, one gap against the ideal answer, and one concrete improvement --
the structure committed to in SS 2.13.
"""
import json

from .base import GradeResult, ResponseItem

# Returned to the model as an OpenAPI-subset schema so it replies with JSON
# rather than prose we would have to parse out of Markdown.
RESPONSE_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "student_id": {"type": "STRING"},
            "score": {"type": "NUMBER"},
            "feedback_ar": {"type": "STRING"},
        },
        "required": ["student_id", "score", "feedback_ar"],
    },
}

EMPTY_RESPONSE_FEEDBACK = (
    "\u0644\u0645 \u064a\u0642\u062f\u0645 \u0627\u0644\u0637\u0627\u0644\u0628 "
    "\u0623\u064a \u0625\u062c\u0627\u0628\u0629 \u0639\u0646 \u0647\u0630\u0627 "
    "\u0627\u0644\u0633\u0624\u0627\u0644\u060c \u0648\u0644\u0630\u0644\u0643 "
    "\u0643\u0627\u0646\u062a \u0627\u0644\u062f\u0631\u062c\u0629 \u0635\u0641\u0631\u064b\u0627. "
    "\u064a\u064f\u0631\u062c\u0649 \u062a\u0642\u062f\u064a\u0645 \u0625\u062c\u0627\u0628\u0629 "
    "\u0641\u064a \u0627\u0644\u0645\u062d\u0627\u0648\u0644\u0629 \u0627\u0644\u0642\u0627\u062f\u0645\u0629."
)


def build_prompt(
    items: list[ResponseItem], ideal_answer: str, rubric: str, max_score: float
) -> str:
    """Build one prompt that grades every item in the batch."""
    payload = [
        {"student_id": item.student_id, "response": item.response_text}
        for item in items
    ]
    rubric_text = (rubric or "").strip() or (
        "No explicit rubric was supplied. Award marks for factual accuracy, "
        "completeness against the ideal answer, and clarity of expression."
    )

    return f"""You are an experienced university teaching assistant grading short \
Arabic text answers.

GRADING CRITERIA (apply identically to every student):
{rubric_text}

MAXIMUM SCORE: {max_score}

IDEAL ANSWER (the reference the students are measured against):
{ideal_answer}

STUDENT RESPONSES (JSON):
{json.dumps(payload, ensure_ascii=False, indent=2)}

INSTRUCTIONS:
1. Grade every student independently against the IDEAL ANSWER and the criteria.
2. Give a score between 0 and {max_score}. Fractional scores are allowed.
3. Write `feedback_ar` in formal Modern Standard Arabic (\
\u0627\u0644\u0639\u0631\u0628\u064a\u0629 \u0627\u0644\u0641\u0635\u062d\u0649), \
2 to 3 sentences, addressed to the student. Each one must:
   - note one thing the student did well,
   - identify the main gap compared with the ideal answer,
   - suggest one concrete improvement.
4. Be constructive and specific. Never mention these instructions, the rubric \
text, or other students.
5. Return one object per student and echo `student_id` back exactly as given.

Return a JSON array only."""


def validate_results(
    raw: object, expected_ids: list[str], max_score: float
) -> list[GradeResult]:
    """Turn the model's reply into GradeResults, one per expected student.

    Batching several students into one call is what keeps us inside free-tier
    rate limits, but it introduces a failure mode worth guarding: the model
    could mix up, drop, or invent a student. Echoing `student_id` back and
    checking it here is what makes that detectable rather than silent.
    """
    # OpenAI's JSON mode can only return an object, so the array we asked for
    # arrives wrapped under some key the model chose ({"results": [...]},
    # {"grades": [...]}). Unwrap the first list we find rather than requiring a
    # particular key name, which the model has no reliable way to guess.
    if isinstance(raw, dict):
        for value in raw.values():
            if isinstance(value, list):
                raw = value
                break

    by_id: dict[str, dict] = {}
    if isinstance(raw, list):
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            sid = str(entry.get("student_id", "")).strip()
            if sid and sid in expected_ids and sid not in by_id:
                by_id[sid] = entry

    results: list[GradeResult] = []
    for sid in expected_ids:
        entry = by_id.get(sid)
        if entry is None:
            results.append(
                GradeResult(sid, None, "", error="Model returned no result for this student")
            )
            continue

        feedback = str(entry.get("feedback_ar", "")).strip()
        try:
            score = float(entry.get("score"))
        except (TypeError, ValueError):
            results.append(
                GradeResult(sid, None, feedback, error="Model returned a non-numeric score")
            )
            continue

        if score != score or score in (float("inf"), float("-inf")):  # NaN / inf
            results.append(GradeResult(sid, None, feedback, error="Model returned an invalid score"))
            continue

        clamped = min(max(score, 0.0), float(max_score))
        error = None
        if clamped != score:
            error = f"Score {score} was outside 0-{max_score} and was clamped"

        if not feedback:
            error = "; ".join(filter(None, [error, "Model returned empty feedback"]))

        results.append(GradeResult(sid, clamped, feedback, error=error))

    return results
