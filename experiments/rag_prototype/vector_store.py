"""
Vector Store voor RAG prototype.

Dit bestand importeert de SimpleVectorStore als ChromaVectorStore
voor backwards compatibility. De SimpleVectorStore werkt met elke
Python versie en heeft geen externe dependencies behalve NumPy.

Voor productie zou je ChromaDB of FAISS kunnen gebruiken, maar de
SimpleVectorStore werkt uitstekend voor prototyping en testing.

NOTE: ChromaDB werkt momenteel niet met Python 3.14 vanwege
dependency conflicts met onnxruntime en pydantic.
"""

# Import alles van de simple vector store
from .simple_vector_store import (
    SimpleVectorStore,
    ChromaVectorStore,  # Alias voor SimpleVectorStore
    RetrievedChunk,
    QueryResult,
)

# Re-export voor backwards compatibility
__all__ = [
    "SimpleVectorStore",
    "ChromaVectorStore",
    "RetrievedChunk",
    "QueryResult",
]
