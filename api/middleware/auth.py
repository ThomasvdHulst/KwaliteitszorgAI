"""API key authentication middleware."""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from api.config import get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """
    Verify the API key from the X-API-Key header.

    Args:
        api_key: The API key from the header

    Returns:
        The validated API key

    Raises:
        HTTPException: If the API key is missing or invalid
    """
    settings = get_settings()

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
