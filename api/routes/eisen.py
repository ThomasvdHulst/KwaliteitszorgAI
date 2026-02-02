"""Eisen endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from api.config import get_settings
from api.core.database import load_database, load_deugdelijkheidseis
from api.middleware.auth import verify_api_key
from api.models.responses import EisDetail, EisenListResponse, EisSummary

router = APIRouter(prefix="/api/v1", tags=["eisen"])


def get_database() -> dict:
    """Load database dependency."""
    settings = get_settings()
    return load_database(settings.database_path)


@router.get(
    "/eisen",
    response_model=EisenListResponse,
    summary="Lijst alle eisen",
    description="Haal een lijst op van alle beschikbare deugdelijkheidseisen.",
)
async def list_eisen(
    _api_key: str = Depends(verify_api_key),
    database: dict = Depends(get_database),
) -> EisenListResponse:
    """
    Haal alle deugdelijkheidseisen op.

    Returns:
        Lijst met summaries van alle eisen
    """
    eisen_dict = database.get("deugdelijkheidseisen", {})

    eisen = [
        EisSummary(
            id=eis_id,
            standaard=eis_data.get("standaard", ""),
            titel=eis_data.get("titel", ""),
        )
        for eis_id, eis_data in eisen_dict.items()
    ]

    # Sorteer op ID
    eisen.sort(key=lambda e: e.id)

    return EisenListResponse(eisen=eisen, totaal=len(eisen))


@router.get(
    "/eisen/{eis_id}",
    response_model=EisDetail,
    summary="Haal eis details op",
    description="Haal de volledige details van een specifieke deugdelijkheidseis op.",
)
async def get_eis(
    eis_id: str,
    _api_key: str = Depends(verify_api_key),
    database: dict = Depends(get_database),
) -> EisDetail:
    """
    Haal details van een specifieke deugdelijkheidseis op.

    Args:
        eis_id: ID van de eis (bijv. 'VS 1.5')

    Returns:
        Volledige details van de eis
    """
    eis = load_deugdelijkheidseis(database, eis_id)

    # Check of de eis gevonden is
    if eis.get("standaard") == "[Niet gevonden in database]":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deugdelijkheidseis '{eis_id}' niet gevonden.",
        )

    return EisDetail(
        id=eis.get("id", eis_id),
        standaard=eis.get("standaard", ""),
        titel=eis.get("titel", ""),
        eisomschrijving=eis.get("eisomschrijving", ""),
        uitleg=eis.get("uitleg", ""),
        focuspunten=eis.get("focuspunten", ""),
        tips=eis.get("tips", ""),
        voorbeelden=eis.get("voorbeelden", ""),
    )
