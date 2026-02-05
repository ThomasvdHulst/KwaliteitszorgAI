"""Utility functies voor Kwaliteitszorg AI."""

from .database import (
    DatabaseError,
    EisNotFoundError,
    get_all_eis_ids,
    load_database,
    load_deugdelijkheidseis,
)
from .pdf_processor import (
    DocumentResult,
    PDFImportError,
    PDFProcessingError,
    extract_text_from_pdf,
    estimate_token_count,
    validate_document_size,
)

__all__ = [
    # Database
    "load_database",
    "load_deugdelijkheidseis",
    "get_all_eis_ids",
    "EisNotFoundError",
    "DatabaseError",
    # PDF Processing
    "extract_text_from_pdf",
    "estimate_token_count",
    "validate_document_size",
    "DocumentResult",
    "PDFProcessingError",
    "PDFImportError",
]
