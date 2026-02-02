"""
RAG Retriever - Brengt alle componenten samen.

Dit is de hoofdklasse die je gebruikt om:
1. Documenten te indexeren
2. Relevante chunks op te halen voor een vraag/eis
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

from . import config
from .chunker import DocumentChunker, ChunkingResult, chunk_pdf_file, Chunk
from .embedder import OllamaEmbedder, BatchEmbeddingResult
from .vector_store import VectorStore, QueryResult


@dataclass
class IndexResult:
    """Resultaat van het indexeren van een document."""

    success: bool
    document_id: str
    document_name: str
    chunks_created: int = 0
    chunks_indexed: int = 0
    chunking_result: Optional[ChunkingResult] = None
    embedding_result: Optional[BatchEmbeddingResult] = None
    error: Optional[str] = None


class RAGRetriever:
    """
    Hoofdklasse voor RAG operaties.

    Combineert chunking, embedding en vector storage
    voor document indexering en retrieval.
    """

    def __init__(
        self,
        embedding_model: str = None,
        persist_path: str = None,
        collection_name: str = None,
        verbose: bool = None,
    ):
        self.verbose = verbose if verbose is not None else config.VERBOSE

        self.chunker = DocumentChunker(verbose=self.verbose)
        self.embedder = OllamaEmbedder(model=embedding_model, verbose=self.verbose)
        self.vector_store = VectorStore(
            persist_path=persist_path,
            collection_name=collection_name,
            verbose=self.verbose,
        )

    def _log(self, message: str):
        """Print log message als verbose aan staat."""
        if self.verbose:
            print(f"[RAGRetriever] {message}")

    def check_setup(self) -> tuple[bool, str]:
        """
        Controleer of alle componenten correct zijn geconfigureerd.

        Returns:
            Tuple van (is_ok, message)
        """
        available, message = self.embedder.check_model_available()
        if not available:
            return False, f"Embedding model probleem: {message}"

        try:
            stats = self.vector_store.get_stats()
            return True, f"Setup OK. Collection '{stats['collection_name']}' heeft {stats['total_chunks']} chunks."
        except Exception as e:
            return False, f"Vector store probleem: {str(e)}"

    def index_pdf(self, file_path: str, show_progress: bool = True) -> IndexResult:
        """
        Indexeer een PDF document.

        Args:
            file_path: Pad naar het PDF bestand
            show_progress: Toon voortgang

        Returns:
            IndexResult met details over het indexeren
        """
        path = Path(file_path)
        self._log(f"Start indexeren: {path.name}")

        # Stap 1: Chunk het document
        chunking_result = chunk_pdf_file(str(path), self.chunker)

        if not chunking_result.success:
            return IndexResult(
                success=False,
                document_id=chunking_result.document_id,
                document_name=path.name,
                error=f"Chunking failed: {chunking_result.error}",
            )

        # Stap 2: Genereer embeddings
        chunk_texts = [chunk.text for chunk in chunking_result.chunks]
        embedding_result = self.embedder.embed_batch(chunk_texts, show_progress=show_progress)

        if not embedding_result.success:
            return IndexResult(
                success=False,
                document_id=chunking_result.document_id,
                document_name=path.name,
                chunks_created=chunking_result.total_chunks,
                chunking_result=chunking_result,
                embedding_result=embedding_result,
                error=f"Embedding failed: {embedding_result.errors}",
            )

        # Stap 3: Opslaan in vector store
        success = self.vector_store.add_chunks(
            chunks=chunking_result.chunks,
            embeddings=embedding_result.embeddings,
        )

        if not success:
            return IndexResult(
                success=False,
                document_id=chunking_result.document_id,
                document_name=path.name,
                chunks_created=chunking_result.total_chunks,
                chunking_result=chunking_result,
                embedding_result=embedding_result,
                error="Failed to add chunks to vector store",
            )

        return IndexResult(
            success=True,
            document_id=chunking_result.document_id,
            document_name=path.name,
            chunks_created=chunking_result.total_chunks,
            chunks_indexed=chunking_result.total_chunks,
            chunking_result=chunking_result,
            embedding_result=embedding_result,
        )

    def index_text(
        self,
        text: str,
        document_name: str,
        document_id: str = None,
        page_boundaries: list = None,
    ) -> IndexResult:
        """
        Indexeer een tekst direct (bijv. van een geüpload document).

        Args:
            text: De tekst om te indexeren
            document_name: Naam voor het document
            document_id: Optioneel document ID
            page_boundaries: Optioneel - lijst van (page_num, char_start, char_end) voor paginanummers

        Returns:
            IndexResult met details
        """
        self._log(f"Start indexeren tekst: {document_name}")

        # Stap 1: Chunk de tekst
        chunking_result = self.chunker.chunk_text(
            text=text,
            document_name=document_name,
            document_id=document_id,
            page_boundaries=page_boundaries,
        )

        if not chunking_result.success:
            return IndexResult(
                success=False,
                document_id=chunking_result.document_id,
                document_name=document_name,
                error=f"Chunking failed: {chunking_result.error}",
            )

        # Stap 2: Genereer embeddings
        chunk_texts = [chunk.text for chunk in chunking_result.chunks]
        embedding_result = self.embedder.embed_batch(chunk_texts, show_progress=False)

        if not embedding_result.success:
            error_details = ""
            if embedding_result.errors:
                error_details = f": {embedding_result.errors[0]}" if len(embedding_result.errors) == 1 else f": {embedding_result.errors[:3]}"
            return IndexResult(
                success=False,
                document_id=chunking_result.document_id,
                document_name=document_name,
                chunks_created=chunking_result.total_chunks,
                error=f"Embedding failed ({embedding_result.failed_count}/{embedding_result.total_texts} mislukt){error_details}",
            )

        # Stap 3: Opslaan
        success = self.vector_store.add_chunks(
            chunks=chunking_result.chunks,
            embeddings=embedding_result.embeddings,
        )

        return IndexResult(
            success=success,
            document_id=chunking_result.document_id,
            document_name=document_name,
            chunks_created=chunking_result.total_chunks,
            chunks_indexed=chunking_result.total_chunks if success else 0,
            chunking_result=chunking_result,
            embedding_result=embedding_result,
        )

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        min_similarity: float = None,
        filter_document: str = None,
        filter_document_ids: List[str] = None,
    ) -> QueryResult:
        """
        Haal relevante chunks op voor een query.

        Args:
            query: De zoek query
            top_k: Aantal resultaten
            min_similarity: Minimum similarity threshold
            filter_document: Optioneel filter op enkel document ID
            filter_document_ids: Optioneel filter op meerdere document IDs

        Returns:
            QueryResult met gevonden chunks
        """
        self._log(f"Retrieve voor query: {query[:50]}...")

        # Genereer embedding voor query
        query_result = self.embedder.embed_text(query)

        if not query_result.success:
            return QueryResult(
                success=False,
                chunks=[],
                query_text=query,
                error=f"Query embedding failed: {query_result.error}",
            )

        # Zoek in vector store
        return self.vector_store.query(
            query_embedding=query_result.embedding,
            query_text=query,
            top_k=top_k,
            min_similarity=min_similarity,
            filter_document_id=filter_document,
            filter_document_ids=filter_document_ids,
        )

    def retrieve_for_eis(
        self,
        retrieval_query: str,
        top_k: int = None,
        filter_document_ids: List[str] = None,
    ) -> QueryResult:
        """
        Haal relevante chunks op voor een deugdelijkheidseis.

        Gebruikt de geoptimaliseerde retrieval_query uit de database.

        Args:
            retrieval_query: De geoptimaliseerde query voor de eis
            top_k: Aantal resultaten
            filter_document_ids: Optioneel filter op specifieke documenten

        Returns:
            QueryResult met relevante chunks
        """
        self._log(f"Retrieve voor eis met query: {retrieval_query[:50]}...")
        return self.retrieve(retrieval_query, top_k=top_k, filter_document_ids=filter_document_ids)

    def get_context_for_llm(
        self,
        query: str,
        max_chunks: int = None,
        max_chars: int = None,
    ) -> str:
        """
        Haal context op en format voor gebruik in LLM prompt.

        Args:
            query: De zoek query
            max_chunks: Maximum aantal chunks
            max_chars: Maximum totaal karakters

        Returns:
            Geformatteerde context string
        """
        max_chunks = max_chunks or config.DEFAULT_TOP_K
        max_chars = max_chars or config.MAX_CONTEXT_CHARS

        result = self.retrieve(query, top_k=max_chunks)

        if not result.success or not result.chunks:
            return ""

        context = result.format_context_for_llm(max_chunks)

        if len(context) > max_chars:
            context = context[:max_chars] + "\n\n[Context ingekort...]"

        return context

    def delete_document(self, document_id: str) -> bool:
        """Verwijder een document uit de index."""
        return self.vector_store.delete_document(document_id)

    def clear_all(self) -> bool:
        """Verwijder alle geindexeerde data."""
        return self.vector_store.clear_collection()

    def list_indexed_documents(self) -> List[Dict[str, Any]]:
        """Lijst alle geindexeerde documenten."""
        return self.vector_store.list_documents()

    def is_empty(self) -> bool:
        """Check of er documenten geindexeerd zijn."""
        return self.vector_store.is_empty()

    def get_stats(self) -> Dict[str, Any]:
        """Haal statistieken op."""
        return self.vector_store.get_stats()
