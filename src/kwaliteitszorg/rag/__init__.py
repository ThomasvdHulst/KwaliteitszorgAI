"""
RAG (Retrieval Augmented Generation) module voor Kwaliteitszorg AI.

Deze module biedt:
- Document indexering (PDF naar chunks met embeddings)
- Retrieval van relevante passages voor deugdelijkheidseisen
- Formatteren van context voor het LLM

Gebruik:
    from src.kwaliteitszorg.rag import RAGRetriever

    retriever = RAGRetriever()
    retriever.index_pdf("pad/naar/document.pdf")
    result = retriever.retrieve("taalbeleid doorlopende leerlijn")
"""

from .retriever import RAGRetriever, IndexResult
from .vector_store import QueryResult, RetrievedChunk

__all__ = [
    "RAGRetriever",
    "IndexResult",
    "QueryResult",
    "RetrievedChunk",
]
