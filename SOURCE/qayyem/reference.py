"""Reads a book chapter or lecture slides into text for the ideal answer.

Instructors often have the model answer already written down in a textbook
PDF or their slides, so they can upload that instead of (or alongside) typing
it. Slides and Word files are zipped XML, so they are read with the standard
library; only PDF needs a dependency.
"""
import io
import re
import zipfile
from xml.etree import ElementTree

from .i18n import gettext as _
from .parsing import ParseError

ALLOWED_EXTENSIONS = (".pdf", ".pptx", ".docx", ".txt")

# The whole text goes into every grading call, so an entire textbook would
# blow through the model's context and the instructor's budget.
MAX_CHARS = 30000

_A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _paragraphs(xml_bytes, para_tag, text_tag):
    root = ElementTree.fromstring(xml_bytes)
    lines = []
    for para in root.iter(para_tag):
        line = "".join(t.text or "" for t in para.iter(text_tag)).strip()
        if line:
            lines.append(line)
    return lines


def _read_pdf(data):
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n\n".join((page.extract_text() or "").strip() for page in reader.pages)


def _read_pptx(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        slides = [
            name for name in archive.namelist()
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        ]
        # slide10 must follow slide9, not slide1.
        slides.sort(key=lambda name: int(re.search(r"\d+", name.rsplit("/", 1)[1]).group()))
        parts = []
        for number, name in enumerate(slides, start=1):
            lines = _paragraphs(archive.read(name), _A_NS + "p", _A_NS + "t")
            if lines:
                parts.append("Slide " + str(number) + ":\n" + "\n".join(lines))
        return "\n\n".join(parts)


def _read_docx(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        lines = _paragraphs(archive.read("word/document.xml"), _W_NS + "p", _W_NS + "t")
    return "\n".join(lines)


def _read_txt(data):
    for encoding in ("utf-8-sig", "cp1256"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ParseError(_("The reference text file's encoding could not be read. Save it as UTF-8."))


def extract_reference_text(filename, data):
    """Return the text of an uploaded book or slides file, trimmed to MAX_CHARS."""
    lower = filename.lower()
    if not lower.endswith(ALLOWED_EXTENSIONS):
        raise ParseError(_(
            "Reference material must be a .pdf, .pptx, .docx or .txt file. "
            "You uploaded '%(name)s'.",
            name=filename,
        ))
    if not data:
        raise ParseError(_("The reference material file is empty."))

    try:
        if lower.endswith(".pdf"):
            text = _read_pdf(data)
        elif lower.endswith(".pptx"):
            text = _read_pptx(data)
        elif lower.endswith(".docx"):
            text = _read_docx(data)
        else:
            text = _read_txt(data)
    except ParseError:
        raise
    except Exception as exc:
        raise ParseError(_(
            "'%(name)s' could not be read. Re-save it and try again. (%(detail)s)",
            name=filename, detail=str(exc)[:160],
        )) from exc

    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise ParseError(_(
            "No text was found in '%(name)s'. If it is a scanned PDF, paste the "
            "answer into the box instead.",
            name=filename,
        ))
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n[...trimmed]"
    return text
