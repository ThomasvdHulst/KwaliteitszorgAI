"""
Ollama Embedder voor RAG prototype.

Genereert embeddings via lokale Ollama installatie.
Bevat uitgebreide logging en monitoring.
"""

import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

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

    def print_summary(self):
        """Print een samenvatting van het embedding resultaat."""
        print("\n" + "=" * 60)
        print("EMBEDDING RESULTAAT")
        print("=" * 60)
        print(f"Status: {'SUCCESS' if self.success else 'FAILED'}")
        print(f"Totaal teksten: {self.total_texts}")
        print(f"Succesvol: {self.successful_count}")
        print(f"Mislukt: {self.failed_count}")
        print(f"\nPerformance:")
        print(f"  - Totale tijd: {self.total_time_ms:.0f} ms")
        print(f"  - Gemiddeld per tekst: {self.avg_time_per_text_ms:.0f} ms")
        print(f"\nEmbedding dimensies: {self.dimensions}")

        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for err in self.errors[:5]:  # Max 5 errors tonen
                print(f"  - {err}")
        print("=" * 60)


class OllamaEmbedder:
    """
    Wrapper voor Ollama embedding generatie.

    Ondersteunt meerdere embedding modellen en biedt
    uitgebreide monitoring en foutafhandeling.
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

        # Cache voor model info
        self._model_info: Optional[Dict] = None
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
            # Probeer model info op te halen
            response = ollama.list()

            # De ollama library geeft een ListResponse object terug met .models attribuut
            # Elk model heeft een .model attribuut met de naam
            model_names = []
            if hasattr(response, 'models'):
                model_names = [m.model for m in response.models if hasattr(m, 'model')]
            elif isinstance(response, dict) and 'models' in response:
                # Fallback voor oudere versies
                model_names = [m.get("name", "") for m in response.get("models", [])]

            # Check of ons model erbij zit (met of zonder :latest tag)
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
                    f"Installeer met: ollama pull {self.model}\n"
                    f"Beschikbare modellen: {', '.join(model_names)}"
                )

        except Exception as e:
            return False, f"Kan geen verbinding maken met Ollama: {str(e)}"

    def get_embedding_dimensions(self) -> int:
        """Haal het aantal dimensies van het embedding model op."""
        if self._dimensions:
            return self._dimensions

        # Genereer een test embedding om dimensies te bepalen
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

        self._log(f"Embedding tekst: \"{preview}\"")

        try:
            response = ollama.embeddings(
                model=self.model,
                prompt=text,
            )

            # De ollama library geeft een EmbeddingsResponse object terug
            # met een .embedding attribuut
            if hasattr(response, 'embedding'):
                embedding = response.embedding
            elif isinstance(response, dict):
                embedding = response.get("embedding", [])
            else:
                embedding = []

            processing_time = (time.time() - start_time) * 1000

            self._log(f"Embedding gegenereerd: {len(embedding)} dimensies in {processing_time:.0f}ms")

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

            self._log(f"ERROR: {error_msg}")

            return EmbeddingResult(
                success=False,
                text_preview=preview,
                processing_time_ms=processing_time,
                error=error_msg,
            )

    def embed_batch(
        self,
        texts: List[str],
        show_progress: bool = True,
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
                embeddings.append([])  # Placeholder
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

        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


def test_embedding_model(model: str = None) -> bool:
    """
    Test of een embedding model werkt.

    Handig voor het vergelijken van verschillende modellen.
    """
    embedder = OllamaEmbedder(model=model)

    print(f"\n{'=' * 60}")
    print(f"TEST EMBEDDING MODEL: {embedder.model}")
    print("=" * 60)

    # Check beschikbaarheid
    available, message = embedder.check_model_available()
    print(f"\n1. Model beschikbaarheid: {message}")

    if not available:
        return False

    # Test met Nederlandse tekst
    test_texts = [
        "De school heeft een doorlopende leerlijn voor taalonderwijs.",
        "De anti-pestcoördinator is het aanspreekpunt voor leerlingen en ouders.",
        "We meten het taalniveau via Cito-toetsen.",
    ]

    print(f"\n2. Test embeddings genereren ({len(test_texts)} teksten)...")
    result = embedder.embed_batch(test_texts, show_progress=False)

    if not result.success:
        print(f"   FAILED: {result.errors}")
        return False

    print(f"   SUCCESS: {result.dimensions} dimensies, {result.avg_time_per_text_ms:.0f}ms per tekst")

    # Test similarity
    print(f"\n3. Test similarity berekening...")
    sim_12 = embedder.compute_similarity(result.embeddings[0], result.embeddings[1])
    sim_13 = embedder.compute_similarity(result.embeddings[0], result.embeddings[2])

    print(f"   Similarity tekst 1-2 (taal vs pesten): {sim_12:.3f}")
    print(f"   Similarity tekst 1-3 (taal vs taal meten): {sim_13:.3f}")

    # Tekst 1 en 3 zouden meer gerelateerd moeten zijn (beide over taal)
    if sim_13 > sim_12:
        print(f"   GOED: Teksten over taal zijn meer gerelateerd dan taal vs pesten")
    else:
        print(f"   LET OP: Verwachte similarity patroon niet gevonden")

    print("=" * 60)
    return True


def compare_embedding_models():
    """
    Vergelijk verschillende embedding modellen.

    Handig om te bepalen welk model het beste werkt voor Nederlandse teksten.
    """
    print("\n" + "=" * 60)
    print("VERGELIJKING EMBEDDING MODELLEN")
    print("=" * 60)

    models_to_test = [
        config.EMBEDDING_MODELS.get("nomic-v2"),
        config.EMBEDDING_MODELS.get("qwen3"),
    ]

    for model in models_to_test:
        if model:
            try:
                test_embedding_model(model)
            except Exception as e:
                print(f"\nModel {model} overgeslagen: {e}")
