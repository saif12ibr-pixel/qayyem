"""Reads the questions out of a Word exam with the instructor's AI model.

The rule-based reader in question_doc.py needs the file laid out its way:
numbered questions, lettered choices, a star on the answer. Real exams come in
every layout, with cover pages, instructions and name boxes around the
questions, so the model reads the file and returns the questions alone. It
copies them; it never writes a question or an answer of its own.

When no model is available (no key, or the offline test grader) or the model
fails, the rule-based reader takes over, with a note saying so.
"""
import json

from .grading import GraderConfigError, GraderError, GraderTransientError
from .i18n import gettext as _
from .parsing import ParseError
from .question_doc import (
    DEFAULT_MARKS_CHOICE,
    DEFAULT_MARKS_WRITTEN,
    MAX_QUESTIONS,
    document_lines,
    ideal_from_options,
    option_label,
    parse_question_doc,
)

# About 15,000 words: a long exam with its answer key. Longer files are cut,
# and the instructor is told.
MAX_DOCUMENT_CHARS = 60000

SYSTEM = (
    "You copy exam questions out of a document, exactly as written. "
    "Reply with a JSON object only, no commentary and no code fences."
)

INSTRUCTIONS = """Below is the text of an exam document, one paragraph per line. Besides the
questions it may hold a cover page, instructions, boxes for the student's name
and ID, headers, footers and page numbers. Ignore all of that and return only
the questions, in the order they appear.

Rules:
- Copy each question's wording exactly, in its original language. Do not
  translate, reword, correct, merge or add questions.
- Leave the question number and the marks out of the question text.
- Automatically classify each question. A question answered by selecting from
  given choices (multiple choice or multiple select, including true/false) has
  type "choice" with its choices in "options", without their letters. Mark
  every correct choice when more than one applies. Every question answered in
  the student's own words is an open question: use type "written" and no
  options. A written question with subparts remains one open question.
- Set "correct" on a choice only when the document marks it as the answer (a
  star, a tick, bold "Answer:", "الإجابة", an answer key). Never guess.
- "model_answer" is the answer the document gives for a written question,
  copied exactly; null when it gives none. Never write one yourself.
- "marks" is the number of marks the document gives the question; null when it
  does not say.
- A written question in several parts (a, b, c) stays one question, with all
  of its parts in the text.

Reply with:
{"questions": [{"text": "...", "type": "written", "options": [], "model_answer": null, "marks": null}]}
where each choice in "options" is {"text": "...", "correct": false}.
If the document holds no questions, reply {"questions": []}.

Document:
<<<
%s
>>>"""


def build_prompt(lines):
    return INSTRUCTIONS % "\n".join(lines)


def _marks(value, default):
    try:
        marks = float(value)
    except (TypeError, ValueError):
        return default
    return marks if 0 < marks <= 1000 else default


def _clean(value):
    return value.strip() if isinstance(value, str) else ""


def parse_reply(text):
    """The model's reply as (questions, warnings), in parse_question_doc's shape."""
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rstrip().removesuffix("```")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GraderError("Model did not return valid JSON: " + str(exc)) from exc
    items = payload.get("questions") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise GraderError("Model reply has no list of questions.")

    result, warnings = [], []
    for item in items[:MAX_QUESTIONS]:
        if not isinstance(item, dict) or not _clean(item.get("text")):
            continue
        number = len(result) + 1
        text = _clean(item["text"])
        arabic = any("؀" <= ch <= "ۿ" for ch in text)

        choices = [o for o in item.get("options") or []
                   if isinstance(o, dict) and _clean(o.get("text"))]
        options = None
        if item.get("type") == "choice" and len(choices) >= 2:
            options = [{"label": option_label(i, arabic), "text": _clean(o["text"]),
                        "correct": o.get("correct") is True}
                       for i, o in enumerate(choices)]

        if options is not None:
            ideal = ideal_from_options(options)
            if ideal is None:
                warnings.append(_("Question %(number)s has choices but none is starred.",
                                  number=number))
            default = DEFAULT_MARKS_CHOICE
        else:
            ideal = _clean(item.get("model_answer")) or None
            if ideal is None:
                warnings.append(_("Question %(number)s has no model answer.", number=number))
            default = DEFAULT_MARKS_WRITTEN

        result.append({"text": text, "options": options, "ideal_answer": ideal,
                       "max_score": _marks(item.get("marks"), default)})
    return result, warnings


def read_questions(filename, data, make_grader):
    """Return (questions, warnings) for a Word exam.

    `make_grader` builds the instructor's grader; it is called here so that a
    missing key falls back to the rule-based reader instead of failing.
    """
    lines = document_lines(filename, data)
    if not lines:
        raise ParseError(_("The Word file is empty."))

    notes = []
    text = "\n".join(lines)
    if len(text) > MAX_DOCUMENT_CHARS:
        lines = text[:MAX_DOCUMENT_CHARS].splitlines()
        notes.append(_("The Word file is long, so only its first part was read. "
                       "Check that the last questions were imported."))

    try:
        reply = make_grader().complete(SYSTEM, build_prompt(lines))
        questions, warnings = parse_reply(reply)
    except NotImplementedError:
        # The offline test grader: no model, so the layout rules do the work.
        return parse_question_doc(filename, data)
    except GraderConfigError:
        fallback = _("No AI provider is set up on the Settings page, so the questions "
                     "were read by their numbering instead.")
    except (GraderError, GraderTransientError) as exc:
        fallback = _("The AI could not read the file (%(error)s), so the questions "
                     "were read by their numbering instead.", error=str(exc)[:200])
    else:
        if not questions:
            raise ParseError(_("No questions were found in '%(name)s'.", name=filename))
        return questions, notes + warnings

    try:
        questions, warnings = parse_question_doc(filename, data)
    except ParseError as exc:
        raise ParseError(fallback + " " + str(exc)) from exc
    return questions, [fallback] + warnings
