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
from .vector_store import ChromaVectorStore, QueryResult


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

    def print_summary(self):
        """Print een samenvatting van het indexeren."""
        print("\n" + "=" * 60)
        print("INDEXERING RESULTAAT")
        print("=" * 60)
        print(f"Document: {self.document_name}")
        print(f"Document ID: {self.document_id}")
        print(f"Status: {'SUCCESS' if self.success else 'FAILED'}")

        if self.error:
            print(f"Error: {self.error}")
            return

        print(f"\nChunking:")
        print(f"  - Chunks gecreëerd: {self.chunks_created}")

        if self.chunking_result:
            print(f"  - Gemiddelde chunk grootte: {self.chunking_result.avg_chunk_size:.0f} karakters")

        print(f"\nEmbeddings:")
        if self.embedding_result:
            print(f"  - Dimensies: {self.embedding_result.dimensions}")
            print(f"  - Tijd: {self.embedding_result.total_time_ms:.0f}ms totaal")
            print(f"  - Per chunk: {self.embedding_result.avg_time_per_text_ms:.0f}ms")

        print(f"\nGeïndexeerd: {self.chunks_indexed} chunks")
        print("=" * 60)


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

        # Initialiseer componenten
        self.chunker = DocumentChunker(verbose=self.verbose)
        self.embedder = OllamaEmbedder(model=embedding_model, verbose=self.verbose)
        self.vector_store = ChromaVectorStore(
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
        # Check embedding model
        available, message = self.embedder.check_model_available()
        if not available:
            return False, f"Embedding model probleem: {message}"

        # Check vector store
        try:
            stats = self.vector_store.get_stats()
            return True, f"Setup OK. Collection '{stats['collection_name']}' heeft {stats['total_chunks']} chunks."
        except Exception as e:
            return False, f"Vector store probleem: {str(e)}"

    def index_pdf(self, file_path: str) -> IndexResult:
        """
        Indexeer een PDF document.

        Args:
            file_path: Pad naar het PDF bestand

        Returns:
            IndexResult met details over het indexeren
        """
        path = Path(file_path)
        self._log(f"Start indexeren: {path.name}")

        # Stap 1: Chunk het document
        print(f"\n{'='*60}")
        print(f"STAP 1: CHUNKING")
        print(f"{'='*60}")

        chunking_result = chunk_pdf_file(str(path), self.chunker)

        if not chunking_result.success:
            return IndexResult(
                success=False,
                document_id=chunking_result.document_id,
                document_name=path.name,
                error=f"Chunking failed: {chunking_result.error}",
            )

        chunking_result.print_summary()
        chunking_result.print_chunks(max_chunks=3)  # Toon eerste 3 chunks

        # Stap 2: Genereer embeddings
        print(f"\n{'='*60}")
        print(f"STAP 2: EMBEDDINGS GENEREREN")
        print(f"{'='*60}")

        chunk_texts = [chunk.text for chunk in chunking_result.chunks]
        embedding_result = self.embedder.embed_batch(chunk_texts)

        embedding_result.print_summary()

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
        print(f"\n{'='*60}")
        print(f"STAP 3: OPSLAAN IN VECTOR STORE")
        print(f"{'='*60}")

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

        self.vector_store.print_status()

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
    ) -> IndexResult:
        """
        Indexeer een tekst direct.

        Args:
            text: De tekst om te indexeren
            document_name: Naam voor het document
            document_id: Optioneel document ID

        Returns:
            IndexResult met details
        """
        self._log(f"Start indexeren tekst: {document_name}")

        # Stap 1: Chunk de tekst
        chunking_result = self.chunker.chunk_text(
            text=text,
            document_name=document_name,
            document_id=document_id,
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
            return IndexResult(
                success=False,
                document_id=chunking_result.document_id,
                document_name=document_name,
                chunks_created=chunking_result.total_chunks,
                error=f"Embedding failed",
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
    ) -> QueryResult:
        """
        Haal relevante chunks op voor een query.

        Args:
            query: De zoek query
            top_k: Aantal resultaten
            min_similarity: Minimum similarity threshold
            filter_document: Optioneel filter op document ID

        Returns:
            QueryResult met gevonden chunks
        """
        print(f"\n{'='*60}")
        print(f"RETRIEVAL")
        print(f"{'='*60}")
        print(f"Query: \"{query[:100]}...\"" if len(query) > 100 else f"Query: \"{query}\"")

        # Genereer embedding voor query
        self._log("Genereer query embedding...")
        query_result = self.embedder.embed_text(query)

        if not query_result.success:
            return QueryResult(
                success=False,
                chunks=[],
                query_text=query,
                error=f"Query embedding failed: {query_result.error}",
            )

        # Zoek in vector store
        self._log("Zoek in vector store...")
        result = self.vector_store.query(
            query_embedding=query_result.embedding,
            query_text=query,
            top_k=top_k,
            min_similarity=min_similarity,
            filter_document_id=filter_document,
        )

        return result

    def retrieve_for_eis(
        self,
        eis_id: str,
        eis_titel: str = "",
        eis_kernvraag: str = "",
        focuspunten: str = "",
        top_k: int = None,
    ) -> QueryResult:
        """
        Haal relevante chunks op voor een specifieke deugdelijkheidseis.

        Bouwt een geoptimaliseerde query op basis van de eis informatie.

        Args:
            eis_id: ID van de eis (bijv. "OP 0.1")
            eis_titel: Titel van de eis
            eis_kernvraag: De kernvraag van de eis
            focuspunten: De focuspunten van de eis
            top_k: Aantal resultaten

        Returns:
            QueryResult met relevante chunks
        """
        # Bouw een rijke query op basis van de eis
        query_parts = []

        if eis_titel:
            query_parts.append(eis_titel)

        if eis_kernvraag:
            query_parts.append(eis_kernvraag)

        if focuspunten:
            # Neem de belangrijkste focuspunten
            query_parts.append(focuspunten[:500])

        query = " ".join(query_parts)

        self._log(f"Query voor eis {eis_id}: {len(query)} karakters")

        return self.retrieve(query, top_k=top_k)

    def get_context_for_llm(
        self,
        query: str,
        max_chunks: int = 5,
        max_chars: int = 8000,
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
        result = self.retrieve(query, top_k=max_chunks)

        if not result.success or not result.chunks:
            return ""

        # Format en limiteer
        context = result.format_context_for_llm(max_chunks)

        if len(context) > max_chars:
            context = context[:max_chars] + "\n\n[Context ingekort...]"

        return context

    def clear_all(self) -> bool:
        """Verwijder alle geïndexeerde data."""
        return self.vector_store.clear_collection()

    def list_indexed_documents(self) -> List[Dict[str, Any]]:
        """Lijst alle geïndexeerde documenten."""
        return self.vector_store.list_documents()

    def print_status(self):
        """Print de huidige status."""
        self.vector_store.print_status()
