"""
Configuratie voor de RAG module.

Alle RAG-specifieke instellingen staan hier.
"""

from pathlib import Path

from config import settings

# =============================================================================
# Paden
# =============================================================================

# Data directory voor vector store
RAG_DATA_DIR = settings.DATA_DIR / "rag_vectorstore"
RAG_DATA_DIR.mkdir(exist_ok=True)

# =============================================================================
# Embedding Model
# =============================================================================

# Beschikbare modellen (in volgorde van voorkeur voor Nederlands)
EMBEDDING_MODELS = {
    "nomic-v2": "nomic-embed-text-v2-moe",  # Multilingual, ~100 talen (aanbevolen)
    "qwen3": "qwen3-embedding",              # Multilingual, 100+ talen
    "nomic-v1": "nomic-embed-text",          # Primair Engels
    "mxbai": "mxbai-embed-large",            # Primair Engels
}

# Actief embedding model
ACTIVE_EMBEDDING_MODEL = EMBEDDING_MODELS["nomic-v2"]

# Ollama URL (hergebruik uit hoofdconfig)
OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL

# =============================================================================
# Chunking Parameters
# =============================================================================

# Target chunk grootte (in karakters)
# Verlaagd van 1500/2500 naar 1200/1500 omdat gestructureerde content
# (tabellen, contactlijsten, e-mails) meer tokens kost dan gewone tekst.
# Met deze waardes werkt ook een schoolgids met contactinformatie.
CHUNK_TARGET_SIZE = 1200  # karakters (was 1500)
CHUNK_MIN_SIZE = 400      # minimum chunk grootte
CHUNK_MAX_SIZE = 1500     # maximum chunk grootte (was 2500)

# Overlap tussen chunks (percentage van chunk size)
CHUNK_OVERLAP_PERCENT = 15  # 15% overlap

# Paragraph-based chunking
PARAGRAPH_SEPARATOR = "\n\n"

# =============================================================================
# Embedding Parameters
# =============================================================================

# Maximum tekst lengte voor embedding (in karakters)
# nomic-embed-text-v2-moe ondersteunt 8192 tokens (~32000 karakters)
# We gebruiken een veilige marge
MAX_EMBED_TEXT_LENGTH = 24000  # ~6000 tokens

# =============================================================================
# Retrieval Parameters
# =============================================================================

# Aantal chunks om op te halen
DEFAULT_TOP_K = 10

# Minimum similarity score (0-1, hoger = strikter)
MIN_SIMILARITY_THRESHOLD = 0.3

# Maximum karakters voor context in LLM prompt
MAX_CONTEXT_CHARS = 8000

# =============================================================================
# Vector Store
# =============================================================================

# Collectie naam voor schooldocumenten
COLLECTION_NAME = "kwaliteitszorg_documenten"

# =============================================================================
# Logging
# =============================================================================

# Verbose output (gebruik DEBUG setting uit hoofdconfig)
VERBOSE = settings.DEBUG
