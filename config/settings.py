"""
Centrale configuratie voor Kwaliteitszorg AI.

Instellingen kunnen worden overschreven via environment variables.
"""
import logging
import os
import sys
from pathlib import Path

# =============================================================================
# Logging configuratie
# =============================================================================
LOG_LEVEL = os.getenv("KWALITEITSZORG_LOG_LEVEL", "INFO").upper()

def setup_logging(name: str = "kwaliteitszorg") -> logging.Logger:
    """
    Configureer en retourneer een logger.

    Args:
        name: Naam van de logger

    Returns:
        Geconfigureerde logger instance
    """
    logger = logging.getLogger(name)

    # Voorkom dubbele handlers bij herhaalde aanroepen
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# Maak standaard logger beschikbaar
logger = setup_logging()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "deugdelijkheidseisen_db.json"

# Debug mode
DEBUG = os.getenv("KWALITEITSZORG_DEBUG", "false").lower() == "true"

# Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Model
MODEL_NAME = os.getenv("KWALITEITSZORG_MODEL", "gemma3:27b")

# Context - verhoogd voor chat-continuatie
MAX_CONTEXT_TOKENS = int(os.getenv("KWALITEITSZORG_MAX_TOKENS", "16000"))
NUM_CTX = 32768  # Context window van het model

# Generatie
TEMPERATURE_DEFAULT = 0.6
MAX_GENERATE_TOKENS = 4000
TOP_P = 0.9
REPEAT_PENALTY = 1.1

# Chat
MAX_CONVERSATION_HISTORY = 10  # Aantal bericht-paren (user + assistant)

# Input limieten
MAX_INPUT_CHARS = 5000  # Maximum karakters per tekstveld

# Document upload limieten
MAX_DOCUMENT_PAGES = 30  # Maximum aantal pagina's uit PDF
MAX_DOCUMENT_CHARS = 50000  # Maximum karakters uit document (~15-20 pagina's tekst)
ALLOWED_DOCUMENT_TYPES = ["pdf"]  # Toegestane bestandstypen


# =============================================================================
# Ollama health check
# =============================================================================
def check_ollama_connection() -> tuple[bool, str]:
    """
    Controleer of Ollama draait en het model beschikbaar is.

    Returns:
        Tuple van (success: bool, message: str)
    """
    try:
        import ollama

        # Check of Ollama server bereikbaar is
        response = ollama.list()

        # Check of het benodigde model aanwezig is
        # Ondersteun zowel nieuwere (object) als oudere (dict) ollama library versies
        model_names = []
        if hasattr(response, 'models'):
            model_names = [m.model for m in response.models if hasattr(m, 'model')]
        elif isinstance(response, dict) and 'models' in response:
            model_names = [m.get("name", m.get("model", "")) for m in response.get("models", [])]

        # Ollama kan modelnamen met :latest suffix hebben
        model_base = MODEL_NAME.split(":")[0]
        model_found = any(model_base in name for name in model_names)

        if not model_found:
            return False, (
                f"Model '{MODEL_NAME}' niet gevonden. "
                f"Beschikbare modellen: {', '.join(model_names) or 'geen'}. "
                f"Installeer met: ollama pull {MODEL_NAME}"
            )

        return True, "Ollama verbinding OK"

    except ImportError:
        return False, "Ollama Python package niet geïnstalleerd. Installeer met: pip install ollama"
    except Exception as e:
        error_msg = str(e).lower()
        if "connection refused" in error_msg or "connect" in error_msg:
            return False, (
                "Kan geen verbinding maken met Ollama. "
                "Zorg ervoor dat Ollama draait: ollama serve"
            )
        return False, f"Ollama fout: {str(e)}"
