"""Builds small Word files for tests, without needing python-docx."""
import io
import zipfile
from xml.sax.saxutils import escape

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def make_docx(paragraphs):
    """Each paragraph is its text, or (text, list id, list level) for a line
    that uses Word's automatic numbering."""
    body = []
    for para in paragraphs:
        text, num_id, level = (para, None, None) if isinstance(para, str) else para
        props = ""
        if num_id is not None:
            props = ('<w:pPr><w:numPr><w:ilvl w:val="%d"/><w:numId w:val="%s"/>'
                     "</w:numPr></w:pPr>" % (level or 0, num_id))
        body.append('<w:p>%s<w:r><w:t xml:space="preserve">%s</w:t></w:r></w:p>'
                    % (props, escape(text)))
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="%s"><w:body>%s</w:body></w:document>'
                % (W, "".join(body)))
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", document)
    return stream.getvalue()
