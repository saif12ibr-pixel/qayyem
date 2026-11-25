"""Reads an exam written in Word into questions for a subject's question bank.

Instructors already write their exams in Word, so the bank is filled from
that file rather than retyped. The format is the one they use on paper:

    1. What is the capital of Saudi Arabia? (1 mark)
       a) Jeddah
       b) Riyadh *
       c) Dammam

    2. Define photosynthesis. [5 marks]
       * The process by which plants turn light energy into chemical energy.

A star marks the correct choice, or the line that is the model answer;
"Answer:" (or "الإجابة:") works for the model answer too. Questions and
choices may be typed ("1.", "a)", "أ-") or use Word's automatic numbering.
"""
import io
import re
import zipfile
from xml.etree import ElementTree

from .i18n import gettext as _
from .parsing import ParseError

MAX_QUESTIONS = 200
DEFAULT_MARKS_CHOICE = 1
DEFAULT_MARKS_WRITTEN = 5

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Arabic-Indic and Persian digits, so "١." numbers a question like "1." does.
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

STARS = "*★☆✱✲⭐✓✔"
_STAR_EDGE = re.compile(r"^\s*[" + STARS + r"]+\s*|\s*[" + STARS + r"]+\s*$")

_QUESTION = re.compile(
    r"^\s*(?:(?:Q|Question|السؤال|سؤال|س)\s*)?\(?(\d{1,3})\s*[.)\-:–]\s*(.+)$", re.I
)
_QUESTION_WORD = re.compile(r"^\s*(?:Question|Q|السؤال|سؤال)\s*(\d{1,3})\s*[.)\-:–]?\s*(.*)$", re.I)
_OPTION = re.compile(r"^\s*[(\[]?([A-Ha-h]|[أابجدهو]|هـ)\s*[).\-\]:]\s*(.+)$")
_ANSWER = re.compile(
    r"^\s*(?:Model answer|Ideal answer|Answer|Ans|الإجابة النموذجية|الإجابة|الاجابة|الجواب)"
    r"\s*[:：\-]\s*(.*)$",
    re.I,
)
_MARKS = re.compile(
    r"\s*[(\[]\s*(\d+(?:\.\d+)?)\s*"
    r"(?:marks?|points?|pts?|درجات|درجة|علامات|علامة)?\s*[)\]]\s*$",
    re.I,
)
_HAS_UNIT = re.compile(r"marks?|points?|pts?|درج|علام|\[", re.I)
_ARABIC = re.compile(r"[؀-ۿ]")

LATIN_LABELS = "ABCDEFGH"
ARABIC_LABELS = ["أ", "ب", "ج", "د", "هـ", "و", "ز", "ح"]


def _paragraphs(data):
    """(text, list id, list level) per non-empty paragraph, in document order."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc:
        raise ParseError(_("That file could not be read as a Word document. Save it as .docx and try again.")) from exc

    for para in root.iter(_W + "p"):
        text = "".join(t.text or "" for t in para.iter(_W + "t")).strip()
        if not text:
            continue
        num_id = level = None
        numbering = para.find(_W + "pPr/" + _W + "numPr")
        if numbering is not None:
            ilvl = numbering.find(_W + "ilvl")
            num = numbering.find(_W + "numId")
            num_id = num.get(_W + "val") if num is not None else None
            level = int(ilvl.get(_W + "val", "0")) if ilvl is not None else 0
            if num_id == "0":  # numbering explicitly removed
                num_id = level = None
        yield text.translate(_DIGITS), num_id, level


def _unstar(text):
    """(text without its star, whether it had one)."""
    clean = _STAR_EDGE.sub("", text)
    return clean.strip(), clean != text


def _marks(text):
    """(question text without a trailing "(5 marks)", the marks or None)."""
    match = _MARKS.search(text)
    if not match or not _HAS_UNIT.search(match.group(0)):
        return text, None
    return text[: match.start()].strip(), float(match.group(1))


def option_label(index, arabic):
    labels = ARABIC_LABELS if arabic else LATIN_LABELS
    return labels[index] if index < len(labels) else str(index + 1)


def ideal_from_options(options):
    """The model answer of a multiple-choice question: its starred choice(s)."""
    return "\n".join(o["label"] + ") " + o["text"] for o in options if o["correct"]) or None


def parse_option_lines(lines, arabic=False):
    """Choices typed one per line with the correct one starred, as on the
    question form. Returns [{"label", "text", "correct"}]."""
    options = []
    for raw in lines:
        text, starred = _unstar(raw)
        if not text:
            continue
        match = _OPTION.match(text)
        label = match.group(1) if match else option_label(len(options), arabic)
        text, more = _unstar(match.group(2) if match else text)
        options.append({"label": label.upper() if label.isascii() else label,
                        "text": text, "correct": starred or more})
    return options


def _new(text, num_id, level):
    text, marks = _marks(text)
    return {"text": text, "marks": marks, "options": [], "answer": [],
            "num_id": num_id, "level": level}


def _check(filename, data):
    if not filename.lower().endswith(".docx"):
        raise ParseError(_("Questions must be a Word file (.docx). You uploaded '%(name)s'.",
                           name=filename))
    if not data:
        raise ParseError(_("The Word file is empty."))


def document_lines(filename, data):
    """The text of every non-empty paragraph, tables included, in order."""
    _check(filename, data)
    return [text for text, _num_id, _level in _paragraphs(data)]


def parse_question_doc(filename, data):
    """Return (questions, warnings).

    Each question is {"text", "options", "ideal_answer", "max_score"}; options
    is None for a written question. Warnings name questions that still need
    something from the instructor, such as a correct answer.
    """
    _check(filename, data)

    questions = []
    current = None
    for raw, num_id, level in _paragraphs(data):
        text, starred = _unstar(raw)

        answer = _ANSWER.match(text)
        if answer and current is not None:
            if answer.group(1).strip():
                current["answer"].append(_unstar(answer.group(1))[0])
            current["answer_open"] = True
            continue

        if current is not None:
            option = _OPTION.match(text)
            # Auto-numbered choices sit one level below the question, or in a
            # list of their own; typed ones carry a letter.
            auto_option = num_id is not None and (
                num_id != current["num_id"] or (level or 0) > (current["level"] or 0)
            )
            if (option or auto_option) and not current["answer"]:
                body = option.group(2) if option else text
                body, more = _unstar(body)
                current["options"].append({
                    "label": option.group(1) if option else None,
                    "text": body,
                    "correct": starred or more,
                })
                continue

        question = _QUESTION.match(text) or _QUESTION_WORD.match(text)
        if question and not starred:
            current = _new(question.group(2).strip() or text, num_id, level)
            questions.append(current)
            continue
        if num_id is not None and not starred and (
            current is None or num_id == current["num_id"]
        ):
            current = _new(text, num_id, level)
            questions.append(current)
            continue

        if current is None:
            continue  # a title or instructions above the first question
        if starred or current.get("answer_open") or current["answer"]:
            current["answer"].append(text)
        elif current["options"]:
            # A wrapped choice continues the one above it.
            current["options"][-1]["text"] += " " + text
        else:
            current["text"] += "\n" + text

        if len(questions) > MAX_QUESTIONS:
            break

    if not questions:
        raise ParseError(_(
            "No questions were found in '%(name)s'. Number each question (1. 2. 3.), "
            "put a letter before each choice (a) b) c)), and mark the correct choice "
            "or the model answer with a star (*).",
            name=filename,
        ))
    if len(questions) > MAX_QUESTIONS:
        raise ParseError(_("A Word file can hold at most %(count)s questions.",
                           count=MAX_QUESTIONS))

    result, warnings = [], []
    for number, q in enumerate(questions, start=1):
        arabic = bool(_ARABIC.search(q["text"]))
        options = None
        if len(q["options"]) >= 2:
            options = []
            for i, o in enumerate(q["options"]):
                label = o["label"] or option_label(i, arabic)
                options.append({"label": label.upper() if label.isascii() else label,
                                "text": o["text"], "correct": o["correct"]})
        elif q["options"]:
            # A lone "choice" is really the start of the answer or the text.
            q["answer"] = [o["text"] for o in q["options"]] + q["answer"]

        if options is not None:
            ideal = ideal_from_options(options)
            if ideal is None:
                warnings.append(_("Question %(number)s has choices but none is starred.",
                                  number=number))
            default = DEFAULT_MARKS_CHOICE
        else:
            ideal = "\n".join(q["answer"]).strip() or None
            if ideal is None:
                warnings.append(_("Question %(number)s has no model answer.", number=number))
            default = DEFAULT_MARKS_WRITTEN

        result.append({
            "text": q["text"].strip(),
            "options": options,
            "ideal_answer": ideal,
            "max_score": q["marks"] or default,
        })
    return result, warnings
