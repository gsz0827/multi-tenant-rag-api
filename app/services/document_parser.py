from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


def parse_txt_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_pdf_file(path: Path) -> str:
    reader = PdfReader(str(path))

    texts: list[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            texts.append(page_text)

    return "\n\n".join(texts)


def parse_docx_file(path: Path) -> str:
    document = DocxDocument(str(path))

    paragraphs: list[str] = []

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)

    return "\n\n".join(paragraphs)


def parse_document_file(path: str, content_type: str | None) -> str:
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = file_path.suffix.lower()

    if content_type == "text/plain" or suffix == ".txt":
        return parse_txt_file(file_path)

    if content_type == "application/pdf" or suffix == ".pdf":
        return parse_pdf_file(file_path)

    if (
        content_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or suffix == ".docx"
    ):
        return parse_docx_file(file_path)

    raise ValueError("Unsupported file type")
