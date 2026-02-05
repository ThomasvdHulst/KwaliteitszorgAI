"""Chat endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from api.core.database import EisNotFoundError
from api.middleware.auth import verify_api_key
from api.models.requests import ChatRequest
from api.models.responses import ChatResponse, ErrorResponse
from api.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


def get_chat_service() -> ChatService:
    """Chat service dependency."""
    return ChatService()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat met de AI assistent",
    description="Stuur een vraag naar de AI assistent voor feedback, uitleg of suggesties.",
    responses={
        400: {"model": ErrorResponse, "description": "Ongeldig eis_id formaat"},
        401: {"model": ErrorResponse, "description": "API key ontbreekt"},
        403: {"model": ErrorResponse, "description": "Ongeldige API key"},
        404: {"model": ErrorResponse, "description": "Eis niet gevonden"},
        503: {"model": ErrorResponse, "description": "Ollama service niet beschikbaar"},
    },
)
async def chat(
    request: ChatRequest,
    _api_key: str = Depends(verify_api_key),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """
    Chat endpoint voor feedback en vragen over deugdelijkheidseisen.

    Vraag types:
    - **feedback**: Krijg feedback op de invulling van de school
    - **uitleg**: Krijg uitleg over wat de eis inhoudt
    - **suggestie**: Krijg concrete suggesties voor verbetering
    - **algemeen**: Stel een algemene vraag

    De API is stateless - elke request wordt onafhankelijk verwerkt.
    """
    try:
        return chat_service.chat(request)
    except ValueError as e:
        # Validatie fouten (ongeldig eis_id formaat)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except EisNotFoundError as e:
        # Eis niet gevonden in database
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except RuntimeError as e:
        # Ollama connectie of model fouten - deze mogen we tonen
        logger.warning("Service error voor eis %s: %s", request.eis_id, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except Exception as e:
        # Onverwachte fouten - log details, maar toon generieke melding
        logger.exception("Onverwachte fout in chat endpoint voor eis %s", request.eis_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Er ging iets mis bij het verwerken van je vraag. Probeer het opnieuw.",
        ) from e
