"""API configuratie - Volledig standalone."""

import logging
import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Bepaal het pad naar de api/ directory
API_DIR = Path(__file__).resolve().parent
DATA_DIR = API_DIR / "data"
DATABASE_PATH = DATA_DIR / "deugdelijkheidseisen_db.json"


class APISettings(BaseSettings):
    """API configuratie via environment variables."""

    # API settings
    api_title: str = "OnSpectAI API"
    api_version: str = "1.0.0"
    api_description: str = "REST API voor OnSpectAI - Laravel integratie"

    # Security - GEEN default in productie!
    api_key: str = os.getenv("ONSPECTAI_API_KEY", "")

    # CORS - comma-separated list of origins
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")

    # Ollama
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model_name: str = os.getenv("KWALITEITSZORG_MODEL", "gemma3:27b")

    # Database
    database_path: str = os.getenv("DATABASE_PATH", str(DATABASE_PATH))

    # Timeouts
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "120"))

    # Model parameters
    temperature: float = float(os.getenv("TEMPERATURE", "0.6"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "4000"))
    top_p: float = float(os.getenv("TOP_P", "0.9"))
    repeat_penalty: float = float(os.getenv("REPEAT_PENALTY", "1.1"))
    num_ctx: int = int(os.getenv("NUM_CTX", "32768"))

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string to list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    class Config:
        env_file = ".env.api"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> APISettings:
    """Get cached settings instance."""
    settings = APISettings()

    # Waarschuw als geen API key geconfigureerd
    if not settings.api_key:
        logger.warning(
            "ONSPECTAI_API_KEY niet geconfigureerd! "
            "De API is onbeveiligd zonder API key."
        )

    return settings


def check_ollama_connection() -> tuple[bool, str]:
    """
    Controleer of Ollama draait en het model beschikbaar is.

    Returns:
        Tuple van (success: bool, message: str)
    """
    try:
        import ollama

        settings = get_settings()

        # Check of Ollama server bereikbaar is
        models = ollama.list()

        # Check of het benodigde model aanwezig is
        model_names = [m.get("name", m.get("model", "")) for m in models.get("models", [])]

        # Ollama kan modelnamen met :latest suffix hebben
        model_base = settings.model_name.split(":")[0]
        model_found = any(model_base in name for name in model_names)

        if not model_found:
            return False, (
                f"Model '{settings.model_name}' niet gevonden. "
                f"Beschikbare modellen: {', '.join(model_names) or 'geen'}. "
                f"Installeer met: ollama pull {settings.model_name}"
            )

        return True, "Ollama verbinding OK"

    except ImportError:
        return False, "Ollama Python package niet geïnstalleerd."
    except Exception as e:
        error_msg = str(e).lower()
        if "connection refused" in error_msg or "connect" in error_msg:
            return False, "Kan geen verbinding maken met Ollama."
        return False, f"Ollama fout: {str(e)}"
