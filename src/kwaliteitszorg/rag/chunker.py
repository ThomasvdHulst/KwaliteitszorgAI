"""
Document Chunker voor RAG.

Verantwoordelijk voor het opsplitsen van documenten in chunks met metadata.
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

    chunk_id: str
    document_id: str
    text: str
    document_name: str
    document_path: Optional[str] = None
    page_number: Optional[int] = None
    chunk_index: int = 0
    total_chunks: int = 0
    char_start: int = 0
    char_end: int = 0
    section_header: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Converteer naar dict voor vector store metadata."""
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
    total_chunks: int = 0
    total_characters: int = 0
    avg_chunk_size: float = 0.0
    min_chunk_size: int = 0
    max_chunk_size: int = 0
    error: Optional[str] = None


class DocumentChunker:
    """
    Chunker voor documenten.

    Splitst tekst op in chunks van vergelijkbare grootte,
    respecteert paragraaf-grenzen waar mogelijk,
    en voegt metadata toe aan elke chunk.

    Gebruikt content-aware chunking: gestructureerde content (tabellen,
    lijsten met veel symbolen) wordt in kleinere chunks gesplitst omdat
    deze meer tokens per karakter kosten bij embedding.
    """

    # Token cost thresholds
    # Normale tekst: ~4 karakters per token
    # Gestructureerde tekst: ~2-3 karakters per token
    TOKEN_COST_NORMAL = 1.0
    TOKEN_COST_STRUCTURED = 1.5  # 50% meer tokens per karakter
    TOKEN_COST_HIGH = 2.0  # 100% meer tokens per karakter

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
        self.overlap_size = int(self.target_size * self.overlap_percent / 100)

    def _log(self, message: str):
        """Print log message als verbose aan staat."""
        if self.verbose:
            print(f"[Chunker] {message}")

    def _estimate_token_cost(self, text: str) -> float:
        """
        Schat hoe "token-duur" een tekst is.

        Gestructureerde content (tabellen, lijsten met veel symbolen,
        overgangsnormen-achtige patronen, PTA-documenten) kost meer
        tokens per karakter dan normale prose tekst.

        Returns:
            Float >= 1.0 waar hogere waarden betekenen dat de tekst
            meer tokens per karakter kost.
        """
        if not text:
            return self.TOKEN_COST_NORMAL

        length = len(text)

        # Tel indicatoren voor gestructureerde/tabel-achtige content
        dashes = text.count('-')
        arrows = text.count('>')
        slashes = text.count('/')
        pipes = text.count('|')
        brackets = text.count('(') + text.count(')')
        colons = text.count(':')

        # Speciale patronen die wijzen op overgangsnormen/tabellen
        # Patronen zoals "vh1 > v2", "kb2 > k3", "ht1 > h2"
        class_refs = len(re.findall(r'[a-z]+\d', text))

        # Herhalende educatieve termen
        a_vakken = text.lower().count('a-vakken') + text.lower().count('a-vak')
        b_vakken = text.lower().count('b-vakken') + text.lower().count('b-vak')
        niveau_refs = len(re.findall(r'(vwo|havo|vmbo|mbo)-?(niveau|[bktg])?', text.lower()))

        # PTA-specifieke patronen (Programma van Toetsing en Afsluiting)
        # Codes zoals PW-P1, HD-P10, PR, SE, TO, etc.
        pta_codes = len(re.findall(r'\b[A-Z]{2,3}-?[A-Z]?\d*\b', text))
        # Periodeaanduidingen zoals "4PW", "50", "15", "100"
        period_numbers = len(re.findall(r'\b\d{1,3}[A-Z]*\b', text))
        # Herkansing, toets, etc
        toets_terms = text.lower().count('toets') + text.lower().count('herkans')

        # Bereken totale "structured score"
        special_chars = dashes + arrows + slashes + pipes
        special_ratio = special_chars / length if length > 0 else 0

        # Combineer alle structuur-indicatoren
        structured_indicators = class_refs + a_vakken + b_vakken + niveau_refs

        # PTA score (hoge waarden wijzen op PTA-tabellen)
        pta_score = pta_codes + (period_numbers / 3) + toets_terms
        pta_density = pta_score / (length / 100) if length > 0 else 0

        # Bepaal token cost multiplier
        if special_ratio > 0.04 and structured_indicators > 5:
            # Zeer gestructureerd (zoals overgangsnormen tabellen)
            return self.TOKEN_COST_HIGH
        elif pta_density > 1.5 or pta_codes > 15:
            # PTA-tabel met veel codes
            return self.TOKEN_COST_HIGH
        elif special_ratio > 0.025 or structured_indicators > 3:
            # Matig gestructureerd
            return self.TOKEN_COST_STRUCTURED
        elif pta_density > 0.8 or pta_codes > 8:
            # Licht gestructureerde PTA content
            return self.TOKEN_COST_STRUCTURED
        else:
            return self.TOKEN_COST_NORMAL

    def _get_adaptive_max_size(self, text: str) -> int:
        """
        Bereken een aangepaste max_size op basis van content type.

        Voor gestructureerde content wordt de max_size verlaagd om
        te voorkomen dat chunks te veel tokens bevatten.
        """
        cost = self._estimate_token_cost(text)
        # Verlaag max_size proportioneel aan token cost
        adaptive_max = int(self.max_size / cost)
        return max(adaptive_max, self.min_size)  # Nooit kleiner dan min_size

    def chunk_text(
        self,
        text: str,
        document_name: str,
        document_path: Optional[str] = None,
        document_id: Optional[str] = None,
        page_boundaries: Optional[List[tuple]] = None,
    ) -> ChunkingResult:
        """
        Chunk een tekst in kleinere delen met metadata.

        Args:
            text: De volledige tekst om te chunken
            document_name: Naam van het document
            document_path: Optioneel pad naar het document
            document_id: Optioneel document ID

        Returns:
            ChunkingResult met alle chunks en statistieken
        """
        doc_id = document_id or str(uuid.uuid4())
        self._log(f"Start chunking: {document_name}")

        try:
            # Clean de tekst
            cleaned_text = self._clean_text(text)

            # Split in paragrafen
            paragraphs = self._split_into_paragraphs(cleaned_text)

            # Combineer paragrafen tot chunks
            raw_chunks = self._combine_paragraphs_to_chunks(paragraphs)

            # Voeg overlap toe
            chunks_with_overlap = self._add_overlap(raw_chunks)

            # Finale check: content-aware splitting
            # Zorg dat geen chunk te groot is voor zijn token-complexiteit
            final_chunks = []
            for chunk in chunks_with_overlap:
                adaptive_max = self._get_adaptive_max_size(chunk)
                if len(chunk) > adaptive_max:
                    # Split chunk met aangepaste limiet
                    self._log(f"Chunk te groot ({len(chunk)} > {adaptive_max}), splitting...")
                    final_chunks.extend(self._force_split_text_adaptive(chunk, adaptive_max))
                else:
                    final_chunks.append(chunk)

            # Maak Chunk objecten met metadata
            chunks = self._create_chunk_objects(
                final_chunks,
                document_name=document_name,
                document_path=document_path,
                document_id=doc_id,
                original_text=cleaned_text,
                page_boundaries=page_boundaries,
            )

            # Bereken statistieken
            chunk_sizes = [len(c.text) for c in chunks]
            return ChunkingResult(
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
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)
        return text.strip()

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split tekst in paragrafen."""
        paragraphs = text.split(config.PARAGRAPH_SEPARATOR)
        return [p.strip() for p in paragraphs if p.strip()]

    def _combine_paragraphs_to_chunks(self, paragraphs: List[str]) -> List[str]:
        """Combineer paragrafen tot chunks van target grootte."""
        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            if len(paragraph) > self.max_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                sub_chunks = self._split_large_paragraph(paragraph)
                chunks.extend(sub_chunks)
                continue

            potential_size = len(current_chunk) + len(paragraph) + 2

            if potential_size <= self.target_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _force_split_text(self, text: str) -> List[str]:
        """
        Force-split tekst die te groot is, op woord-grenzen.

        Dit is een fallback voor tekst die zelfs na zin-splitting te groot is.
        """
        return self._force_split_text_adaptive(text, self.max_size)

    def _force_split_text_adaptive(self, text: str, max_size: int) -> List[str]:
        """
        Force-split tekst die te groot is, op woord-grenzen.

        Args:
            text: De tekst om te splitten
            max_size: De maximale grootte per chunk (kan aangepast zijn
                      voor token-dure content)

        Returns:
            Lijst van chunks die elk <= max_size karakters zijn
        """
        if len(text) <= max_size:
            return [text]

        chunks = []
        words = text.split()
        current_chunk = ""

        for word in words:
            if len(current_chunk) + len(word) + 1 <= max_size:
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # Als een enkel woord te lang is, knip het
                if len(word) > max_size:
                    for i in range(0, len(word), max_size):
                        chunks.append(word[i:i + max_size])
                    current_chunk = ""
                else:
                    current_chunk = word

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """Split een te grote paragraaf in kleinere delen op zin-grenzen."""
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        current_chunk = ""

        for sentence in sentences:
            # Als een enkele zin te groot is, force-split deze
            if len(sentence) > self.max_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # Force split de lange zin
                chunks.extend(self._force_split_text(sentence))
                continue

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
                overlapped_chunks.append(chunk)
            else:
                prev_chunk = chunks[i - 1]
                overlap_text = prev_chunk[-self.overlap_size:] if len(prev_chunk) > self.overlap_size else prev_chunk
                overlap_text = self._trim_to_word_boundary(overlap_text, from_start=True)

                if overlap_text:
                    overlapped_chunks.append(f"[...] {overlap_text}\n\n{chunk}")
                else:
                    overlapped_chunks.append(chunk)

        return overlapped_chunks

    def _trim_to_word_boundary(self, text: str, from_start: bool = True) -> str:
        """Trim tekst naar de dichtstbijzijnde woord-grens."""
        if from_start:
            match = re.search(r'\s', text)
            if match:
                return text[match.end():]
        else:
            match = re.search(r'\s(?=[^\s]*$)', text)
            if match:
                return text[:match.start()]
        return text

    def _find_page_for_position(
        self,
        char_pos: int,
        page_boundaries: Optional[List[tuple]],
    ) -> Optional[int]:
        """
        Vind het paginanummer voor een karakterpositie.

        Args:
            char_pos: De karakterpositie in de tekst
            page_boundaries: Lijst van (page_num, char_start, char_end)

        Returns:
            Paginanummer (1-indexed) of None
        """
        if not page_boundaries:
            return None

        for page_num, start, end in page_boundaries:
            if start <= char_pos < end:
                return page_num

        # Fallback: laatste pagina als positie voorbij alle grenzen is
        if page_boundaries and char_pos >= page_boundaries[-1][1]:
            return page_boundaries[-1][0]

        return None

    def _create_chunk_objects(
        self,
        chunk_texts: List[str],
        document_name: str,
        document_path: Optional[str],
        document_id: str,
        original_text: str,
        page_boundaries: Optional[List[tuple]] = None,
    ) -> List[Chunk]:
        """Maak Chunk objecten met volledige metadata."""
        chunks = []
        total_chunks = len(chunk_texts)
        char_position = 0

        for i, text in enumerate(chunk_texts):
            section_header = self._detect_section_header(text)

            clean_text = re.sub(r'^\[\.\.\.\] ', '', text)
            try:
                char_start = original_text.find(clean_text[:50], char_position)
                if char_start == -1:
                    char_start = char_position
                char_end = char_start + len(clean_text)
                char_position = char_start + 100
            except Exception:
                char_start = char_position
                char_end = char_start + len(text)

            # Bepaal paginanummer op basis van char_start
            page_number = self._find_page_for_position(char_start, page_boundaries)

            chunk = Chunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                text=text,
                document_name=document_name,
                document_path=document_path,
                page_number=page_number,
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
        patterns = [
            r'^(\d+\.?\d*\.?\s+[A-Z][^\n]{0,50})',
            r'^([A-Z][A-Za-z\s]{0,30}:)',
            r'^(Hoofdstuk\s+\d+[^\n]{0,30})',
        ]

        for pattern in patterns:
            match = re.match(pattern, text)
            if match:
                return match.group(1).strip()

        return None


def chunk_pdf_file(file_path: str, chunker: DocumentChunker = None) -> ChunkingResult:
    """Convenience functie om een PDF bestand te chunken."""
    from ..utils.pdf_processor import extract_text_from_pdf

    path = Path(file_path)
    with open(path, "rb") as f:
        file_bytes = f.read()

    result = extract_text_from_pdf(
        file_bytes=file_bytes,
        filename=path.name,
        max_pages=None,
        max_chars=None,
    )

    if not result.success:
        return ChunkingResult(
            success=False,
            chunks=[],
            document_id="",
            document_name=path.name,
            error=result.error,
        )

    if chunker is None:
        chunker = DocumentChunker()

    return chunker.chunk_text(
        text=result.text,
        document_name=path.name,
        document_path=str(path),
        page_boundaries=result.page_boundaries,
    )
