"""Chat endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status

from api.middleware.auth import verify_api_key
from api.models.requests import ChatRequest
from api.models.responses import ChatResponse
from api.services.chat_service import ChatService

router = APIRouter(prefix="/api/v1", tags=["chat"])


def get_chat_service() -> ChatService:
    """Chat service dependency."""
    return ChatService()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat met de AI assistent",
    description="Stuur een vraag naar de AI assistent voor feedback, uitleg of suggesties.",
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
    except RuntimeError as e:
        # Ollama connectie of model fouten
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Er ging iets mis: {str(e)}",
        ) from e
