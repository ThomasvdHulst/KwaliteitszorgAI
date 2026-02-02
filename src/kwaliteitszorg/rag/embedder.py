"""
Ollama Embedder voor RAG.

Genereert embeddings via lokale Ollama installatie.
"""

import time
from dataclasses import dataclass
from typing import List, Optional, Dict

import ollama

from . import config


@dataclass
class EmbeddingResult:
    """Resultaat van een embedding operatie."""

    success: bool
    embedding: Optional[List[float]] = None
    text_preview: str = ""
    dimensions: int = 0
    processing_time_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class BatchEmbeddingResult:
    """Resultaat van een batch embedding operatie."""

    success: bool
    embeddings: List[List[float]]
    total_texts: int = 0
    successful_count: int = 0
    failed_count: int = 0
    total_time_ms: float = 0.0
    avg_time_per_text_ms: float = 0.0
    dimensions: int = 0
    errors: List[str] = None


class OllamaEmbedder:
    """
    Wrapper voor Ollama embedding generatie.

    Ondersteunt meerdere embedding modellen en biedt
    foutafhandeling voor productie gebruik.
    """

    def __init__(
        self,
        model: str = None,
        base_url: str = None,
        verbose: bool = None,
    ):
        self.model = model or config.ACTIVE_EMBEDDING_MODEL
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.verbose = verbose if verbose is not None else config.VERBOSE
        self._dimensions: Optional[int] = None

    def _log(self, message: str):
        """Print log message als verbose aan staat."""
        if self.verbose:
            print(f"[Embedder] {message}")

    def check_model_available(self) -> tuple[bool, str]:
        """
        Check of het embedding model beschikbaar is.

        Returns:
            Tuple van (is_available, message)
        """
        try:
            response = ollama.list()

            model_names = []
            if hasattr(response, 'models'):
                model_names = [m.model for m in response.models if hasattr(m, 'model')]
            elif isinstance(response, dict) and 'models' in response:
                model_names = [m.get("name", "") for m in response.get("models", [])]

            model_base = self.model.split(":")[0]
            available = any(
                model_base in name or self.model in name
                for name in model_names
            )

            if available:
                return True, f"Model '{self.model}' is beschikbaar"
            else:
                return False, (
                    f"Model '{self.model}' niet gevonden. "
                    f"Installeer met: ollama pull {self.model}"
                )

        except Exception as e:
            return False, f"Kan geen verbinding maken met Ollama: {str(e)}"

    def get_embedding_dimensions(self) -> int:
        """Haal het aantal dimensies van het embedding model op."""
        if self._dimensions:
            return self._dimensions

        result = self.embed_text("test")
        if result.success:
            self._dimensions = result.dimensions
            return self._dimensions

        return 0

    def embed_text(self, text: str) -> EmbeddingResult:
        """
        Genereer een embedding voor een enkele tekst.

        Args:
            text: De tekst om te embedden

        Returns:
            EmbeddingResult met de embedding en metadata
        """
        start_time = time.time()
        preview = text[:50] + "..." if len(text) > 50 else text

        # Truncate tekst als deze te lang is voor het embedding model
        original_length = len(text)
        if len(text) > config.MAX_EMBED_TEXT_LENGTH:
            text = text[:config.MAX_EMBED_TEXT_LENGTH]
            self._log(f"Tekst ingekort van {original_length} naar {len(text)} karakters")

        try:
            response = ollama.embeddings(
                model=self.model,
                prompt=text,
            )

            if hasattr(response, 'embedding'):
                embedding = response.embedding
            elif isinstance(response, dict):
                embedding = response.get("embedding", [])
            else:
                embedding = []

            processing_time = (time.time() - start_time) * 1000

            return EmbeddingResult(
                success=True,
                embedding=embedding,
                text_preview=preview,
                dimensions=len(embedding),
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            # Maak de foutmelding informatiever
            if "connection" in error_msg.lower():
                error_msg = f"Ollama verbinding verloren: {error_msg}"
            elif "timeout" in error_msg.lower():
                error_msg = f"Timeout bij embedding (tekst: {len(text)} chars): {error_msg}"
            return EmbeddingResult(
                success=False,
                text_preview=preview,
                processing_time_ms=processing_time,
                error=error_msg,
            )

    def embed_batch(
        self,
        texts: List[str],
        show_progress: bool = False,
    ) -> BatchEmbeddingResult:
        """
        Genereer embeddings voor meerdere teksten.

        Args:
            texts: Lijst van teksten om te embedden
            show_progress: Toon voortgang tijdens verwerking

        Returns:
            BatchEmbeddingResult met alle embeddings en statistieken
        """
        start_time = time.time()
        embeddings = []
        errors = []
        successful = 0
        failed = 0
        dimensions = 0

        self._log(f"Start batch embedding: {len(texts)} teksten")

        for i, text in enumerate(texts):
            if show_progress and (i + 1) % 5 == 0:
                elapsed = (time.time() - start_time) * 1000
                print(f"  Voortgang: {i + 1}/{len(texts)} ({elapsed:.0f}ms)")

            result = self.embed_text(text)

            if result.success:
                embeddings.append(result.embedding)
                successful += 1
                if dimensions == 0:
                    dimensions = result.dimensions
            else:
                embeddings.append([])
                errors.append(f"Text {i}: {result.error}")
                failed += 1

        total_time = (time.time() - start_time) * 1000

        return BatchEmbeddingResult(
            success=failed == 0,
            embeddings=embeddings,
            total_texts=len(texts),
            successful_count=successful,
            failed_count=failed,
            total_time_ms=total_time,
            avg_time_per_text_ms=total_time / len(texts) if texts else 0,
            dimensions=dimensions,
            errors=errors if errors else None,
        )

    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """
        Bereken cosine similarity tussen twee embeddings.

        Returns:
            Similarity score tussen 0 en 1
        """
        if not embedding1 or not embedding2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)
