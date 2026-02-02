"""
RAG Prototype voor Kwaliteitszorg AI

Dit is een experimentele module om RAG (Retrieval Augmented Generation) te testen
voordat we het integreren in de hoofdapplicatie.

Componenten:
- chunker.py: Document chunking met metadata
- embedder.py: Embedding generatie via Ollama
- vector_store.py: ChromaDB vector opslag
- retriever.py: Alles samenvoegen voor retrieval

Gebruik:
    python -m experiments.rag_prototype.test_rag
"""

# Lazy imports om circulaire dependencies te voorkomen
def get_chunker():
    from .chunker import DocumentChunker
    return DocumentChunker

def get_embedder():
    from .embedder import OllamaEmbedder
    return OllamaEmbedder

def get_vector_store():
    from .vector_store import ChromaVectorStore
    return ChromaVectorStore

def get_retriever():
    from .retriever import RAGRetriever
    return RAGRetriever
