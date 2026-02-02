"""
Configuratie voor het RAG prototype.

Alle instellingen staan hier zodat we makkelijk kunnen experimenteren
met verschillende parameters.
"""

from pathlib import Path

# =============================================================================
# Paden
# =============================================================================

# Base directory van het prototype
PROTOTYPE_DIR = Path(__file__).parent

# Data directories
DATA_DIR = PROTOTYPE_DIR / "data"
CHROMA_DB_PATH = DATA_DIR / "chroma_db"
TEST_DOCUMENTS_DIR = PROTOTYPE_DIR.parent.parent / "voorbeeldbeleid"

# Zorg dat directories bestaan
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DB_PATH.mkdir(exist_ok=True)


# =============================================================================
# Embedding Model
# =============================================================================

# Beschikbare modellen (in volgorde van voorkeur voor Nederlands)
EMBEDDING_MODELS = {
    "nomic-v2": "nomic-embed-text-v2-moe",  # Multilingual, ~100 talen
    "qwen3": "qwen3-embedding",              # Multilingual, 100+ talen
    "nomic-v1": "nomic-embed-text",          # Primair Engels
    "mxbai": "mxbai-embed-large",            # Primair Engels
}

# Actief model (pas dit aan om te wisselen)
ACTIVE_EMBEDDING_MODEL = EMBEDDING_MODELS["nomic-v2"]

# Ollama URL
OLLAMA_BASE_URL = "http://localhost:11434"


# =============================================================================
# Chunking Parameters
# =============================================================================

# Target chunk grootte (in karakters, ~4 karakters per token)
# 300-500 tokens = 1200-2000 karakters
CHUNK_TARGET_SIZE = 1500  # karakters
CHUNK_MIN_SIZE = 500      # minimum chunk grootte
CHUNK_MAX_SIZE = 2500     # maximum chunk grootte

# Overlap tussen chunks (percentage van chunk size)
CHUNK_OVERLAP_PERCENT = 15  # 15% overlap

# Paragraph-based chunking
PARAGRAPH_SEPARATOR = "\n\n"
SENTENCE_SEPARATORS = [".", "!", "?", ";\n"]


# =============================================================================
# Retrieval Parameters
# =============================================================================

# Aantal chunks om op te halen
DEFAULT_TOP_K = 10

# Minimum similarity score (0-1, hoger = strikter)
MIN_SIMILARITY_THRESHOLD = 0.3


# =============================================================================
# ChromaDB
# =============================================================================

# Collectie naam voor test documenten
COLLECTION_NAME = "kwaliteitszorg_test"

# Distance metric (cosine is standaard en werkt goed voor tekst)
DISTANCE_METRIC = "cosine"


# =============================================================================
# Logging & Monitoring
# =============================================================================

# Verbose output voor debugging
VERBOSE = True

# Toon chunk previews (eerste N karakters)
CHUNK_PREVIEW_LENGTH = 100

# Toon embedding dimensies
SHOW_EMBEDDING_STATS = True
