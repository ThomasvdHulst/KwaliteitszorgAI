"""API key authentication middleware."""

import logging

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from api.config import get_settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """
    Verify the API key from the X-API-Key header.

    Als geen API key is geconfigureerd (ONSPECTAI_API_KEY niet gezet),
    werkt de API in development mode zonder authenticatie.

    Args:
        api_key: The API key from the header

    Returns:
        The validated API key (of "dev-mode" als geen key geconfigureerd)

    Raises:
        HTTPException: If the API key is missing or invalid
    """
    settings = get_settings()

    # Development mode: geen API key geconfigureerd
    if not settings.api_key:
        logger.debug("API draait zonder authenticatie (development mode)")
        return "dev-mode"

    # Production mode: API key vereist
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key ontbreekt. Voeg header 'X-API-Key' toe.",
        )

    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ongeldige API key.",
        )

    return api_key
