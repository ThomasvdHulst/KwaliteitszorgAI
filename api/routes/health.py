"""Health check endpoint."""

from fastapi import APIRouter

from api.config import check_ollama_connection, get_settings
from api.models.responses import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Controleer of de API en Ollama beschikbaar zijn.",
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Controleert:
    - API status
    - Ollama verbinding
    - Model beschikbaarheid
    """
    settings = get_settings()
    ollama_ok, ollama_message = check_ollama_connection()

    return HealthResponse(
        status="ok" if ollama_ok else "degraded",
        ollama="connected" if ollama_ok else "disconnected",
        model=settings.model_name,
        message=ollama_message if not ollama_ok else "",
    )
