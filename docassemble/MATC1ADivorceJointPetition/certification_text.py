"""Plain text of a generated DOCX, for certification's content assertions.

Only the authenticated combined_certification_snapshot action calls this, so
normal sessions never build or store document text.
"""
import html
import re
import zipfile

__all__ = ["docx_plain_text"]


def docx_plain_text(path: str) -> str:
    """Return the body text of a DOCX file, one line per paragraph."""
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    lines = []
    for paragraph in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        text = "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", paragraph))
        lines.append(html.unescape(text))
    return "\n".join(lines)
