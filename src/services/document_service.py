"""
Feature-oriented facade for financial document intelligence: summarize,
compare, and extract key points from uploaded reports/decks/filings.

Text extraction is real (pypdf) — this isn't a stub. What's NOT built yet
is the RAG pipeline (chunking + embeddings + vector search) for
"ask arbitrary questions across a long document" — see the note on
answer_question() below. For a hackathon-scale document (a single
report/deck), stuffing the extracted text directly into the prompt is
simpler and works fine within Claude's context window.
"""
from __future__ import annotations

import io

from pypdf import PdfReader

from src.config.logging import get_logger
from src.services.ai.llm_client import LLMClient

logger = get_logger(__name__)
llm = LLMClient()

MAX_DOCUMENT_CHARS = 100_000  # keep well within context window; truncate very long filings


class DocumentService:
    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """
        Extracts plain text from a document. PDF is fully implemented;
        .txt/.md pass through as-is. Add python-docx/python-pptx branches
        here for Word/PowerPoint uploads if the hackathon demo needs them.
        """
        if filename.lower().endswith(".pdf"):
            return self._extract_pdf_text(file_bytes)

        if filename.lower().endswith((".txt", ".md")):
            return file_bytes.decode("utf-8", errors="replace")

        logger.warning("document_unsupported_type", filename=filename)
        return ""

    def _extract_pdf_text(self, file_bytes: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
        except Exception as exc:  # noqa: BLE001 — malformed/encrypted PDFs shouldn't crash the bot
            logger.error("pdf_read_failed", error=str(exc))
            return ""

        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception as exc:  # noqa: BLE001 — some pages can fail extraction individually
                logger.warning("pdf_page_extract_failed", error=str(exc))

        text = "\n\n".join(pages)
        if len(text) > MAX_DOCUMENT_CHARS:
            logger.info("pdf_truncated", original_length=len(text), truncated_to=MAX_DOCUMENT_CHARS)
            text = text[:MAX_DOCUMENT_CHARS]
        return text

    async def summarize(self, document_text: str, focus: str | None = None) -> str:
        instruction = (
            f"Summarize this financial document, focusing especially on: {focus}."
            if focus
            else "Write an executive summary of this financial document: key figures, notable changes, and risks."
        )
        return await self._ask(document_text, instruction)

    async def extract_key_points(self, document_text: str, n: int = 5) -> str:
        return await self._ask(
            document_text,
            f"Extract the {n} most important takeaways from this document as short bullet points, "
            "each explaining why it matters to an investor or analyst.",
        )

    async def compare(self, document_a: str, document_b: str, criteria: str) -> str:
        combined = f"DOCUMENT A:\n{document_a}\n\n---\n\nDOCUMENT B:\n{document_b}"
        return await self._ask(
            combined,
            f"Compare Document A and Document B based on: {criteria}. "
            "Be specific about what differs and what it implies, not just what each document says.",
        )

    async def answer_question(self, document_text: str, question: str) -> str:
        """
        Direct Q&A against the full extracted text. Works well for a single
        document within context limits. For multi-document or very long
        filing collections, this should be replaced by real RAG
        (chunking + embeddings + retrieval) rather than growing this prompt indefinitely.
        """
        return await self._ask(document_text, f"Answer this question based only on the document: {question}")

    async def _ask(self, document_text: str, instruction: str) -> str:
        if not document_text.strip():
            return "I couldn't extract any readable text from that document — is it a scanned image or encrypted PDF?"

        response = await llm.complete(
            system=(
                "You are a financial analyst assistant reading a document for a finance professional. "
                "Be concise, specific, and cite concrete figures/facts from the text rather than vague summaries."
            ),
            messages=[{"role": "user", "content": f"{instruction}\n\nDocument:\n{document_text}"}],
            max_tokens=800,
        )
        return response.text


document_service = DocumentService()
