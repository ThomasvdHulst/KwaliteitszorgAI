"""
Vector Store voor RAG.

Eenvoudige vector store gebaseerd op NumPy voor similarity search.
Volledig lokaal, geen externe dependencies behalve NumPy.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np

from . import config
from .chunker import Chunk


@dataclass
class RetrievedChunk:
    """Een opgehaalde chunk met similarity score."""

    chunk_id: str
    text: str
    similarity_score: float
    distance: float
    document_name: str
    document_id: str
    chunk_index: int
    total_chunks: int
    page_number: Optional[int] = None
    section_header: Optional[str] = None

    def format_for_context(self) -> str:
        """Format de chunk voor gebruik in LLM context."""
        source_info = f"[Bron: {self.document_name}"
        if self.page_number and self.page_number > 0:
            source_info += f", p.{self.page_number}"
        if self.section_header:
            source_info += f", sectie: {self.section_header}"
        source_info += f"] (relevantie: {self.similarity_score:.0%})"

        return f"{source_info}\n{self.text}"


@dataclass
class QueryResult:
    """Resultaat van een query operatie."""

    success: bool
    chunks: List[RetrievedChunk]
    query_text: str
    total_results: int = 0
    error: Optional[str] = None

    def get_used_documents(self) -> List[str]:
        """
        Haal lijst van unieke documentnamen op die in de resultaten voorkomen.

        Returns:
            Gesorteerde lijst van documentnamen
        """
        doc_names = set()
        for chunk in self.chunks:
            if chunk.document_name:
                doc_names.add(chunk.document_name)
        return sorted(doc_names)

    def format_context_for_llm(self, max_chunks: int = None) -> str:
        """Format alle chunks als context voor het LLM."""
        chunks_to_use = self.chunks[:max_chunks] if max_chunks else self.chunks

        if not chunks_to_use:
            return ""

        context_parts = [
            "RELEVANTE PASSAGES UIT SCHOOLDOCUMENTEN:",
            ""
        ]

        for i, chunk in enumerate(chunks_to_use, 1):
            context_parts.append(f"--- Passage {i} ---")
            context_parts.append(chunk.format_for_context())
            context_parts.append("")

        return "\n".join(context_parts)


class VectorStore:
    """
    Eenvoudige vector store gebaseerd op NumPy.

    Slaat embeddings op in een NumPy array en metadata in JSON.
    Alle data wordt lokaal opgeslagen.
    """

    def __init__(
        self,
        persist_path: str = None,
        collection_name: str = None,
        verbose: bool = None,
    ):
        self.persist_path = Path(persist_path or config.RAG_DATA_DIR)
        self.collection_name = collection_name or config.COLLECTION_NAME
        self.verbose = verbose if verbose is not None else config.VERBOSE

        self._embeddings: Optional[np.ndarray] = None
        self._metadata: List[Dict[str, Any]] = []
        self._texts: List[str] = []
        self._ids: List[str] = []

        self.persist_path.mkdir(parents=True, exist_ok=True)
        self._load()

    def _log(self, message: str):
        """Print log message als verbose aan staat."""
        if self.verbose:
            print(f"[VectorStore] {message}")

    def _get_data_path(self) -> Path:
        """Get path voor data bestanden."""
        return self.persist_path / f"{self.collection_name}_data.json"

    def _get_embeddings_path(self) -> Path:
        """Get path voor embeddings bestand."""
        return self.persist_path / f"{self.collection_name}_embeddings.npy"

    def _save(self):
        """Sla data op naar disk."""
        data = {
            "ids": self._ids,
            "texts": self._texts,
            "metadata": self._metadata,
            "saved_at": datetime.now().isoformat(),
        }

        with open(self._get_data_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        embeddings_path = self._get_embeddings_path()
        if self._embeddings is not None and len(self._embeddings) > 0:
            np.save(embeddings_path, self._embeddings)
        else:
            # Verwijder embeddings file als er geen embeddings meer zijn
            if embeddings_path.exists():
                embeddings_path.unlink()
                self._log("Embeddings file verwijderd (geen data)")

        self._log(f"Data opgeslagen: {len(self._ids)} chunks")

    def _load(self):
        """Laad data van disk."""
        data_path = self._get_data_path()
        embeddings_path = self._get_embeddings_path()

        # Reset state
        self._ids = []
        self._texts = []
        self._metadata = []
        self._embeddings = None

        if data_path.exists():
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._ids = data.get("ids", [])
            self._texts = data.get("texts", [])
            self._metadata = data.get("metadata", [])

            self._log(f"Metadata geladen: {len(self._ids)} chunks")

        if embeddings_path.exists():
            self._embeddings = np.load(embeddings_path)
            self._log(f"Embeddings geladen: shape {self._embeddings.shape}")

            # Valideer sync na laden
            if len(self._ids) != len(self._embeddings):
                self._log(f"WARNING: Data out of sync na laden! {len(self._ids)} ids vs {len(self._embeddings)} embeddings")
                # Als metadata leeg is maar embeddings niet, verwijder embeddings
                if len(self._ids) == 0:
                    self._log("Verwijder orphan embeddings file")
                    embeddings_path.unlink()
                    self._embeddings = None

    def get_stats(self) -> Dict[str, Any]:
        """Haal statistieken op over de vector store."""
        return {
            "collection_name": self.collection_name,
            "persist_path": str(self.persist_path),
            "total_chunks": len(self._ids),
            "embedding_dimensions": self._embeddings.shape[1] if self._embeddings is not None and len(self._embeddings) > 0 else 0,
        }

    def add_chunks(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]],
    ) -> bool:
        """
        Voeg chunks met embeddings toe aan de store.

        Args:
            chunks: Lijst van Chunk objecten
            embeddings: Corresponderende embeddings

        Returns:
            True als succesvol
        """
        if len(chunks) != len(embeddings):
            self._log(f"ERROR: Mismatch tussen chunks ({len(chunks)}) en embeddings ({len(embeddings)})")
            return False

        # BELANGRIJK: Herlaad altijd van disk voor we toevoegen
        # Dit voorkomt sync problemen tussen Streamlit sessies
        self._load()

        self._log(f"Voeg {len(chunks)} chunks toe (huidige stand: {len(self._ids)} chunks)")

        try:
            for chunk, embedding in zip(chunks, embeddings):
                self._ids.append(chunk.chunk_id)
                self._texts.append(chunk.text)
                self._metadata.append(chunk.to_metadata_dict())

            new_embeddings = np.array(embeddings)

            if self._embeddings is None or len(self._embeddings) == 0:
                self._embeddings = new_embeddings
            else:
                self._embeddings = np.vstack([self._embeddings, new_embeddings])

            # Valideer voor opslaan
            if len(self._ids) != len(self._embeddings):
                self._log(f"ERROR: Sync check failed na toevoegen: {len(self._ids)} ids vs {len(self._embeddings)} embeddings")
                # Rollback
                self._load()
                return False

            self._save()
            self._log(f"Succesvol toegevoegd. Totaal: {len(self._ids)} chunks")
            return True

        except Exception as e:
            self._log(f"ERROR bij toevoegen: {str(e)}")
            # Rollback naar disk state
            self._load()
            return False

    def query(
        self,
        query_embedding: List[float],
        query_text: str = "",
        top_k: int = None,
        min_similarity: float = None,
        filter_document_id: str = None,
        filter_document_ids: List[str] = None,
    ) -> QueryResult:
        """
        Zoek naar relevante chunks via cosine similarity.

        Args:
            query_embedding: De embedding van de query
            query_text: De originele query tekst
            top_k: Aantal resultaten om terug te geven
            min_similarity: Minimum similarity threshold
            filter_document_id: Optioneel filter op enkel document (deprecated)
            filter_document_ids: Optioneel filter op meerdere documenten

        Returns:
            QueryResult met gevonden chunks
        """
        # Herlaad van disk om zeker te zijn dat we actuele data hebben
        self._load()

        top_k = top_k or config.DEFAULT_TOP_K
        min_similarity = min_similarity or config.MIN_SIMILARITY_THRESHOLD

        if self._embeddings is None or len(self._embeddings) == 0:
            return QueryResult(
                success=True,
                chunks=[],
                query_text=query_text,
                total_results=0,
            )

        try:
            # Valideer dat embeddings en metadata in sync zijn
            if len(self._embeddings) != len(self._metadata):
                self._log(f"WARNING: embeddings ({len(self._embeddings)}) en metadata ({len(self._metadata)}) niet in sync!")
                # Probeer te herladen
                self._load()
                if len(self._embeddings) != len(self._metadata):
                    return QueryResult(
                        success=False,
                        chunks=[],
                        query_text=query_text,
                        error="Data synchronisatie probleem. Probeer de pagina te verversen.",
                    )

            query_vec = np.array(query_embedding)

            query_norm = np.linalg.norm(query_vec)
            embedding_norms = np.linalg.norm(self._embeddings, axis=1)

            valid_mask = (embedding_norms > 0) & (query_norm > 0)

            similarities = np.zeros(len(self._embeddings))
            if np.any(valid_mask):
                dot_products = np.dot(self._embeddings[valid_mask], query_vec)
                similarities[valid_mask] = dot_products / (embedding_norms[valid_mask] * query_norm)

            # Filter op document(en)
            if filter_document_ids:
                # Filter op meerdere documenten
                allowed_ids = set(filter_document_ids)
                for i, meta in enumerate(self._metadata):
                    if meta.get("document_id") not in allowed_ids:
                        similarities[i] = -1
            elif filter_document_id:
                # Backwards compatible: filter op enkel document
                for i, meta in enumerate(self._metadata):
                    if meta.get("document_id") != filter_document_id:
                        similarities[i] = -1

            valid_indices = np.where(similarities >= min_similarity)[0]
            sorted_indices = valid_indices[np.argsort(similarities[valid_indices])[::-1]]
            top_indices = sorted_indices[:top_k]

            retrieved_chunks = []
            for idx in top_indices:
                # Extra bounds check
                if idx >= len(self._metadata) or idx >= len(self._texts) or idx >= len(self._ids):
                    self._log(f"WARNING: Index {idx} out of bounds, skipping")
                    continue
                similarity = float(similarities[idx])
                metadata = self._metadata[idx]

                chunk = RetrievedChunk(
                    chunk_id=self._ids[idx],
                    text=self._texts[idx],
                    similarity_score=similarity,
                    distance=1 - similarity,
                    document_name=metadata.get("document_name", ""),
                    document_id=metadata.get("document_id", ""),
                    chunk_index=metadata.get("chunk_index", 0),
                    total_chunks=metadata.get("total_chunks", 0),
                    page_number=metadata.get("page_number"),
                    section_header=metadata.get("section_header"),
                )
                retrieved_chunks.append(chunk)

            self._log(f"Gevonden: {len(retrieved_chunks)} chunks boven threshold")

            return QueryResult(
                success=True,
                chunks=retrieved_chunks,
                query_text=query_text,
                total_results=len(retrieved_chunks),
            )

        except Exception as e:
            self._log(f"ERROR bij query: {str(e)}")
            return QueryResult(
                success=False,
                chunks=[],
                query_text=query_text,
                error=str(e),
            )

    def delete_document(self, document_id: str) -> bool:
        """Verwijder alle chunks van een document."""
        try:
            indices_to_remove = []
            for i, meta in enumerate(self._metadata):
                if meta.get("document_id") == document_id:
                    indices_to_remove.append(i)

            if not indices_to_remove:
                self._log(f"Geen chunks gevonden voor document {document_id}")
                return True

            self._log(f"Verwijder {len(indices_to_remove)} chunks voor document {document_id}")

            for idx in sorted(indices_to_remove, reverse=True):
                del self._ids[idx]
                del self._texts[idx]
                del self._metadata[idx]

            mask = np.ones(len(self._embeddings), dtype=bool)
            mask[indices_to_remove] = False
            self._embeddings = self._embeddings[mask]

            self._save()
            return True

        except Exception as e:
            self._log(f"ERROR bij verwijderen: {str(e)}")
            return False

    def clear_collection(self) -> bool:
        """Verwijder alle data uit de collection."""
        try:
            self._log(f"Verwijder alle data uit collection: {self.collection_name}")

            self._ids = []
            self._texts = []
            self._metadata = []
            self._embeddings = None

            data_path = self._get_data_path()
            embeddings_path = self._get_embeddings_path()

            if data_path.exists():
                data_path.unlink()
            if embeddings_path.exists():
                embeddings_path.unlink()

            return True

        except Exception as e:
            self._log(f"ERROR bij clearen: {str(e)}")
            return False

    def list_documents(self) -> List[Dict[str, Any]]:
        """Lijst alle geindexeerde documenten."""
        documents = {}
        for metadata in self._metadata:
            doc_id = metadata.get("document_id", "unknown")
            if doc_id not in documents:
                documents[doc_id] = {
                    "document_id": doc_id,
                    "document_name": metadata.get("document_name", "unknown"),
                    "chunk_count": 0,
                    "total_chars": 0,
                }
            documents[doc_id]["chunk_count"] += 1
            documents[doc_id]["total_chars"] += metadata.get("char_count", 0)

        return list(documents.values())

    def is_empty(self) -> bool:
        """Check of de vector store leeg is."""
        return len(self._ids) == 0
