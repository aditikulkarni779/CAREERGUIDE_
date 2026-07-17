"""Extract plain text from an uploaded resume (PDF / DOCX / TXT)."""
from __future__ import annotations

import io


class ResumeParseError(Exception):
    """Unsupported or unreadable resume file."""


def parse_resume(filename: str, data: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        return _parse_pdf(data)
    if ext == "docx":
        return _parse_docx(data)
    if ext in ("txt", "md"):
        return data.decode("utf-8", errors="ignore")
    raise ResumeParseError(f"unsupported file type: .{ext}")


def _parse_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


def _parse_docx(data: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs).strip()
