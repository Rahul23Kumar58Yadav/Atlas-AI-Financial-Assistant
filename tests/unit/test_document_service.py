from src.services.document_service import document_service
from tests.fixtures.loader import load_text


def test_extract_text_from_txt():
    text = load_text("sample_document.txt")
    extracted = document_service.extract_text(text.encode("utf-8"), "sample_document.txt")
    assert "Q3 2026" in extracted
    assert "$4.2 billion" in extracted


def test_extract_text_unsupported_type_returns_empty():
    result = document_service.extract_text(b"whatever", "archive.zip")
    assert result == ""


def test_extract_pdf_text_from_generated_pdf(tmp_path):
    """Generates a real PDF at test time (no binary fixture checked in) and verifies real extraction."""
    from reportlab.pdfgen import canvas

    pdf_path = tmp_path / "test.pdf"
    c = canvas.Canvas(str(pdf_path))
    c.drawString(100, 750, "Sample Corp Q3 Filing")
    c.drawString(100, 720, "Revenue: $4.2 billion")
    c.save()

    pdf_bytes = pdf_path.read_bytes()
    extracted = document_service.extract_text(pdf_bytes, "test.pdf")

    assert "Sample Corp Q3 Filing" in extracted
    assert "$4.2 billion" in extracted


def test_extract_pdf_text_malformed_pdf_returns_empty():
    extracted = document_service.extract_text(b"not a real pdf", "broken.pdf")
    assert extracted == ""
