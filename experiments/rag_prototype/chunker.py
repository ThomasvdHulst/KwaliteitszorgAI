"""
Document Chunker voor RAG prototype.

Verantwoordelijk voor het opsplitsen van documenten in chunks met metadata.
Bevat uitgebreide logging voor monitoring en debugging.
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from . import config


@dataclass
class Chunk:
    """Een chunk van een document met alle metadata."""

    # Unieke identifiers
    chunk_id: str
    document_id: str

    # Content
    text: str

    # Document metadata
    document_name: str
    document_path: Optional[str] = None

    # Positie metadata
    page_number: Optional[int] = None
    chunk_index: int = 0
    total_chunks: int = 0
    char_start: int = 0
    char_end: int = 0

    # Context
    section_header: Optional[str] = None

    # Administratief
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Converteer naar dict voor ChromaDB metadata."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "document_path": self.document_path or "",
            "page_number": self.page_number or -1,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "section_header": self.section_header or "",
            "created_at": self.created_at,
            "char_count": len(self.text),
        }

    def preview(self, length: int = 100) -> str:
        """Geef een preview van de chunk tekst."""
        if len(self.text) <= length:
            return self.text
        return self.text[:length] + "..."


@dataclass
class ChunkingResult:
    """Resultaat van het chunking proces met statistieken."""

    success: bool
    chunks: List[Chunk]
    document_id: str
    document_name: str

    # Statistieken
    total_chunks: int = 0
    total_characters: int = 0
    avg_chunk_size: float = 0.0
    min_chunk_size: int = 0
    max_chunk_size: int = 0

    # Eventuele fout
    error: Optional[str] = None

    def print_summary(self):
        """Print een samenvatting van het chunking resultaat."""
        print("\n" + "=" * 60)
        print("CHUNKING RESULTAAT")
        print("=" * 60)
        print(f"Document: {self.document_name}")
        print(f"Document ID: {self.document_id}")
        print(f"Status: {'SUCCESS' if self.success else 'FAILED'}")

        if self.error:
            print(f"Error: {self.error}")
            return

        print(f"\nStatistieken:")
        print(f"  - Totaal chunks: {self.total_chunks}")
        print(f"  - Totaal karakters: {self.total_characters:,}")
        print(f"  - Gemiddelde chunk grootte: {self.avg_chunk_size:.0f} karakters")
        print(f"  - Kleinste chunk: {self.min_chunk_size} karakters")
        print(f"  - Grootste chunk: {self.max_chunk_size} karakters")
        print("=" * 60)

    def print_chunks(self, max_chunks: int = None, preview_length: int = None):
        """Print details van alle chunks."""
        preview_len = preview_length or config.CHUNK_PREVIEW_LENGTH
        chunks_to_show = self.chunks[:max_chunks] if max_chunks else self.chunks

        print(f"\n{'=' * 60}")
        print(f"CHUNK DETAILS ({len(chunks_to_show)} van {len(self.chunks)} chunks)")
        print("=" * 60)

        for chunk in chunks_to_show:
            print(f"\n[Chunk {chunk.chunk_index + 1}/{chunk.total_chunks}]")
            print(f"  ID: {chunk.chunk_id[:8]}...")
            print(f"  Karakters: {len(chunk.text)} (positie {chunk.char_start}-{chunk.char_end})")
            if chunk.page_number:
                print(f"  Pagina: {chunk.page_number}")
            if chunk.section_header:
                print(f"  Sectie: {chunk.section_header}")
            print(f"  Preview: \"{chunk.preview(preview_len)}\"")

        if max_chunks and len(self.chunks) > max_chunks:
            print(f"\n  ... en nog {len(self.chunks) - max_chunks} chunks")


class DocumentChunker:
    """
    Chunker voor documenten.

    Splitst tekst op in chunks van vergelijkbare grootte,
    respecteert paragraaf-grenzen waar mogelijk,
    en voegt metadata toe aan elke chunk.
    """

    def __init__(
        self,
        target_size: int = None,
        min_size: int = None,
        max_size: int = None,
        overlap_percent: int = None,
        verbose: bool = None,
    ):
        self.target_size = target_size or config.CHUNK_TARGET_SIZE
        self.min_size = min_size or config.CHUNK_MIN_SIZE
        self.max_size = max_size or config.CHUNK_MAX_SIZE
        self.overlap_percent = overlap_percent or config.CHUNK_OVERLAP_PERCENT
        self.verbose = verbose if verbose is not None else config.VERBOSE

        # Bereken overlap in karakters
        self.overlap_size = int(self.target_size * self.overlap_percent / 100)

    def _log(self, message: str):
        """Print log message als verbose aan staat."""
        if self.verbose:
            print(f"[Chunker] {message}")

    def chunk_text(
        self,
        text: str,
        document_name: str,
        document_path: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> ChunkingResult:
        """
        Chunk een tekst in kleinere delen met metadata.

        Args:
            text: De volledige tekst om te chunken
            document_name: Naam van het document
            document_path: Optioneel pad naar het document
            document_id: Optioneel document ID (wordt gegenereerd als niet gegeven)

        Returns:
            ChunkingResult met alle chunks en statistieken
        """
        doc_id = document_id or str(uuid.uuid4())

        self._log(f"Start chunking: {document_name}")
        self._log(f"Document grootte: {len(text):,} karakters")
        self._log(f"Parameters: target={self.target_size}, overlap={self.overlap_size}")

        try:
            # Stap 1: Clean de tekst
            cleaned_text = self._clean_text(text)
            self._log(f"Na cleaning: {len(cleaned_text):,} karakters")

            # Stap 2: Split in paragrafen
            paragraphs = self._split_into_paragraphs(cleaned_text)
            self._log(f"Gevonden paragrafen: {len(paragraphs)}")

            # Stap 3: Combineer paragrafen tot chunks van target grootte
            raw_chunks = self._combine_paragraphs_to_chunks(paragraphs)
            self._log(f"Ruwe chunks gecreëerd: {len(raw_chunks)}")

            # Stap 4: Voeg overlap toe
            chunks_with_overlap = self._add_overlap(raw_chunks)
            self._log(f"Chunks met overlap: {len(chunks_with_overlap)}")

            # Stap 5: Maak Chunk objecten met metadata
            chunks = self._create_chunk_objects(
                chunks_with_overlap,
                document_name=document_name,
                document_path=document_path,
                document_id=doc_id,
                original_text=cleaned_text,
            )

            # Bereken statistieken
            chunk_sizes = [len(c.text) for c in chunks]
            result = ChunkingResult(
                success=True,
                chunks=chunks,
                document_id=doc_id,
                document_name=document_name,
                total_chunks=len(chunks),
                total_characters=sum(chunk_sizes),
                avg_chunk_size=sum(chunk_sizes) / len(chunks) if chunks else 0,
                min_chunk_size=min(chunk_sizes) if chunks else 0,
                max_chunk_size=max(chunk_sizes) if chunks else 0,
            )

            self._log(f"Chunking voltooid: {len(chunks)} chunks")
            return result

        except Exception as e:
            self._log(f"ERROR: {str(e)}")
            return ChunkingResult(
                success=False,
                chunks=[],
                document_id=doc_id,
                document_name=document_name,
                error=str(e),
            )

    def _clean_text(self, text: str) -> str:
        """Clean de tekst voor chunking."""
        # Normaliseer line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Verwijder excessive whitespace maar behoud paragraaf-structuur
        text = re.sub(r"[ \t]+", " ", text)  # Multiple spaces/tabs -> single space
        text = re.sub(r"\n{3,}", "\n\n", text)  # Max 2 newlines

        # Trim elke regel
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        # Verwijder leading/trailing whitespace
        text = text.strip()

        return text

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split tekst in paragrafen."""
        # Split op dubbele newlines (paragraaf-grenzen)
        paragraphs = text.split(config.PARAGRAPH_SEPARATOR)

        # Filter lege paragrafen en strip whitespace
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _combine_paragraphs_to_chunks(self, paragraphs: List[str]) -> List[str]:
        """
        Combineer paragrafen tot chunks van target grootte.

        Probeert paragrafen bij elkaar te houden, maar splitst
        grote paragrafen indien nodig.
        """
        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            # Als de paragraaf zelf te groot is, split hem
            if len(paragraph) > self.max_size:
                # Eerst huidige chunk afsluiten als er iets in zit
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                # Split de grote paragraaf
                sub_chunks = self._split_large_paragraph(paragraph)
                chunks.extend(sub_chunks)
                continue

            # Check of toevoegen binnen target past
            potential_size = len(current_chunk) + len(paragraph) + 2  # +2 voor \n\n

            if potential_size <= self.target_size:
                # Past nog, voeg toe
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Past niet meer, start nieuwe chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph

        # Vergeet laatste chunk niet
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """Split een te grote paragraaf in kleinere delen op zin-grenzen."""
        chunks = []

        # Probeer te splitsen op zinnen
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)

        current_chunk = ""
        for sentence in sentences:
            potential_size = len(current_chunk) + len(sentence) + 1

            if potential_size <= self.target_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """Voeg overlap toe tussen opeenvolgende chunks."""
        if len(chunks) <= 1 or self.overlap_size <= 0:
            return chunks

        overlapped_chunks = []

        for i, chunk in enumerate(chunks):
            if i == 0:
                # Eerste chunk: geen prefix overlap nodig
                overlapped_chunks.append(chunk)
            else:
                # Voeg einde van vorige chunk toe als context
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk[-self.overlap_size:] if len(prev_chunk) > self.overlap_size else prev_chunk

                # Probeer op woord-grens te splitsen
                overlap_text = self._trim_to_word_boundary(overlap_text, from_start=True)

                if overlap_text:
                    overlapped_chunks.append(f"[...] {overlap_text}\n\n{chunk}")
                else:
                    overlapped_chunks.append(chunk)

        return overlapped_chunks

    def _trim_to_word_boundary(self, text: str, from_start: bool = True) -> str:
        """Trim tekst naar de dichtstbijzijnde woord-grens."""
        if from_start:
            # Vind eerste spatie en start daar
            match = re.search(r'\s', text)
            if match:
                return text[match.end():]
        else:
            # Vind laatste spatie en stop daar
            match = re.search(r'\s(?=[^\s]*$)', text)
            if match:
                return text[:match.start()]
        return text

    def _create_chunk_objects(
        self,
        chunk_texts: List[str],
        document_name: str,
        document_path: Optional[str],
        document_id: str,
        original_text: str,
    ) -> List[Chunk]:
        """Maak Chunk objecten met volledige metadata."""
        chunks = []
        total_chunks = len(chunk_texts)

        # Track positie in originele tekst (ongeveer, door overlap kan dit afwijken)
        char_position = 0

        for i, text in enumerate(chunk_texts):
            # Probeer sectie header te detecteren
            section_header = self._detect_section_header(text)

            # Zoek positie in originele tekst (zonder overlap markers)
            clean_text = re.sub(r'^\[\.\.\.\] ', '', text)
            try:
                char_start = original_text.find(clean_text[:50], char_position)
                if char_start == -1:
                    char_start = char_position
                char_end = char_start + len(clean_text)
                char_position = char_start + 100  # Move forward for next search
            except:
                char_start = char_position
                char_end = char_start + len(text)

            chunk = Chunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                text=text,
                document_name=document_name,
                document_path=document_path,
                chunk_index=i,
                total_chunks=total_chunks,
                char_start=char_start,
                char_end=char_end,
                section_header=section_header,
            )
            chunks.append(chunk)

        return chunks

    def _detect_section_header(self, text: str) -> Optional[str]:
        """Detecteer een sectie header aan het begin van de chunk."""
        # Zoek naar patronen zoals "1. Titel" of "1.1 Titel" of "Hoofdstuk 1:"
        patterns = [
            r'^(\d+\.?\d*\.?\s+[A-Z][^\n]{0,50})',  # "1. Titel" of "1.1 Titel"
            r'^([A-Z][A-Za-z\s]{0,30}:)',  # "Inleiding:"
            r'^(Hoofdstuk\s+\d+[^\n]{0,30})',  # "Hoofdstuk 1"
        ]

        for pattern in patterns:
            match = re.match(pattern, text)
            if match:
                return match.group(1).strip()

        return None


def chunk_pdf_file(
    file_path: str,
    chunker: DocumentChunker = None,
) -> ChunkingResult:
    """
    Convenience functie om een PDF bestand te chunken.

    Gebruikt de bestaande PDF processor uit de hoofdapplicatie.
    """
    import sys
    from pathlib import Path

    # Voeg project root toe aan path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from src.kwaliteitszorg.utils.pdf_processor import extract_text_from_pdf

    # Lees PDF
    path = Path(file_path)
    with open(path, "rb") as f:
        file_bytes = f.read()

    # Extract tekst
    result = extract_text_from_pdf(
        file_bytes=file_bytes,
        filename=path.name,
        max_pages=None,  # Alle pagina's
        max_chars=None,  # Geen limiet
    )

    if not result.success:
        return ChunkingResult(
            success=False,
            chunks=[],
            document_id="",
            document_name=path.name,
            error=result.error,
        )

    # Chunk de tekst
    if chunker is None:
        chunker = DocumentChunker()

    return chunker.chunk_text(
        text=result.text,
        document_name=path.name,
        document_path=str(path),
    )
