"""PDF processing utilities voor Kwaliteitszorg AI.

Deze module biedt functionaliteit voor het verwerken van PDF documenten
die scholen kunnen uploaden als context voor de AI-assistent.

Features:
- PDF tekst extractie via PyMuPDF
- Automatische truncatie bij limieten
- Page boundary tracking voor bronvermelding
- Tekst cleaning en normalisatie
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from config import settings
from config.settings import logger


class PDFProcessingError(Exception):
    """Exception voor PDF verwerkingsfouten."""

    pass


class PDFImportError(Exception):
    """Exception wanneer PyMuPDF niet geïnstalleerd is."""

    pass


@dataclass
class DocumentResult:
    """
    Resultaat van document processing.

    Attributes:
        success: Of de verwerking succesvol was
        text: De geëxtraheerde tekst
        filename: Naam van het verwerkte bestand
        page_count: Aantal verwerkte pagina's
        char_count: Totaal aantal karakters
        truncated: Of het document ingekort is
        error: Foutmelding indien niet succesvol
        page_boundaries: Lijst van (page_num, char_start, char_end) tuples
    """
    success: bool
    text: str
    filename: str
    page_count: int
    char_count: int
    truncated: bool
    error: Optional[str] = None
    page_boundaries: Optional[List[Tuple[int, int, int]]] = None


def extract_text_from_pdf(
    file_bytes: bytes,
    filename: str,
    max_pages: Optional[int] = None,
    max_chars: Optional[int] = None,
    unlimited: bool = False,
) -> DocumentResult:
    """
    Extraheer tekst uit een PDF bestand.

    Args:
        file_bytes: Ruwe bytes van het PDF bestand
        filename: Naam van het bestand (voor logging/display)
        max_pages: Maximum aantal pagina's om te verwerken (default uit settings)
        max_chars: Maximum aantal karakters (default uit settings)
        unlimited: Als True, geen limieten toepassen (voor RAG indexering)

    Returns:
        DocumentResult met geëxtraheerde tekst en metadata

    Note:
        Bij fouten wordt een DocumentResult met success=False geretourneerd,
        geen exception geraised. Dit maakt error handling in de UI eenvoudiger.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.error("PyMuPDF niet geïnstalleerd. Installeer met: pip install PyMuPDF")
        return DocumentResult(
            success=False,
            text="",
            filename=filename,
            page_count=0,
            char_count=0,
            truncated=False,
            error="PDF verwerking niet beschikbaar. Installeer PyMuPDF met: pip install PyMuPDF"
        )

    # Bij unlimited: gebruik zeer hoge limieten
    if unlimited:
        max_pages = 1000  # Praktisch ongelimiteerd
        max_chars = 10_000_000  # 10 miljoen karakters
    else:
        max_pages = max_pages or settings.MAX_DOCUMENT_PAGES
        max_chars = max_chars or settings.MAX_DOCUMENT_CHARS

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        total_pages = len(doc)
        text_parts = []
        page_boundaries = []  # (page_num, char_start, char_end)
        chars_collected = 0
        pages_processed = 0
        truncated = False

        for page_num in range(min(total_pages, max_pages)):
            page = doc[page_num]
            page_text = page.get_text()

            # Check karakter limiet
            if chars_collected + len(page_text) > max_chars:
                # Neem alleen wat nog past
                remaining = max_chars - chars_collected
                if remaining > 0:
                    text_parts.append(page_text[:remaining])
                    # Track partial page boundary
                    page_boundaries.append((page_num + 1, chars_collected, chars_collected + remaining))
                truncated = True
                pages_processed = page_num + 1
                break

            # Track page boundary (1-indexed page numbers)
            page_boundaries.append((page_num + 1, chars_collected, chars_collected + len(page_text)))

            text_parts.append(page_text)
            chars_collected += len(page_text)
            pages_processed = page_num + 1

        # Check of we pagina's hebben overgeslagen
        if total_pages > max_pages:
            truncated = True

        doc.close()

        # Combineer en clean tekst
        full_text = "\n".join(text_parts)
        cleaned_text = _clean_extracted_text(full_text)

        # Herbereken page boundaries na cleaning (tekst kan korter worden)
        # We gebruiken een simpele mapping: de ratio van cleaning
        if len(full_text) > 0:
            ratio = len(cleaned_text) / len(full_text)
            adjusted_boundaries = [
                (pg, int(start * ratio), int(end * ratio))
                for pg, start, end in page_boundaries
            ]
        else:
            adjusted_boundaries = page_boundaries

        logger.info(
            "PDF verwerkt: %s (%d/%d pagina's, %d karakters%s)",
            filename,
            pages_processed,
            total_pages,
            len(cleaned_text),
            ", ingekort" if truncated else ""
        )

        return DocumentResult(
            success=True,
            text=cleaned_text,
            filename=filename,
            page_count=pages_processed,
            char_count=len(cleaned_text),
            truncated=truncated,
            page_boundaries=adjusted_boundaries,
        )

    except Exception as e:
        logger.error("Fout bij verwerken PDF '%s': %s", filename, e)
        return DocumentResult(
            success=False,
            text="",
            filename=filename,
            page_count=0,
            char_count=0,
            truncated=False,
            error=f"Kon PDF niet verwerken: {str(e)}"
        )


def _clean_extracted_text(text: str) -> str:
    """
    Maak geëxtraheerde tekst schoon.

    - Verwijdert excessive whitespace
    - Normaliseert regeleindes
    - Verwijdert bekende PDF artefacten
    """
    # Normaliseer regeleindes
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Verwijder excessive lege regels (meer dan 2 achter elkaar)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Verwijder excessive spaties
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Trim elke regel
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Verwijder leading/trailing whitespace
    text = text.strip()

    return text


def estimate_token_count(text: str) -> int:
    """
    Schat het aantal tokens voor een tekst.

    Gebruikt een simpele heuristiek: ~1.3 tokens per woord voor Nederlands.
    Dit is een ruwe schatting, geen exacte telling.
    """
    word_count = len(text.split())
    return int(word_count * 1.3)


def validate_document_size(
    char_count: int,
    max_chars: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Valideer of een document binnen de limieten valt.

    Returns:
        Tuple van (is_valid, message)
    """
    max_chars = max_chars or settings.MAX_DOCUMENT_CHARS

    if char_count > max_chars:
        return False, (
            f"Document te groot ({char_count:,} karakters). "
            f"Maximum is {max_chars:,} karakters."
        )

    if char_count == 0:
        return False, "Document bevat geen leesbare tekst."

    return True, "OK"
