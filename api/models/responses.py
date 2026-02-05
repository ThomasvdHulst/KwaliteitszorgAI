"""API response models."""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standaard error response model."""

    detail: str = Field(..., description="Foutmelding")


class ChatResponse(BaseModel):
    """Response van de chat endpoint."""

    antwoord: str = Field(..., description="Het antwoord van de AI assistent")
    eis_id: str = Field(..., description="ID van de deugdelijkheidseis")
    vraag_type: str = Field(..., description="Type vraag dat werd gesteld")


class EisSummary(BaseModel):
    """Samenvatting van een deugdelijkheidseis."""

    id: str = Field(..., description="Unieke ID van de eis")
    standaard: str = Field(..., description="De standaard waar de eis onder valt")
    titel: str = Field(..., description="Titel van de eis")


class EisDetail(BaseModel):
    """Volledige details van een deugdelijkheidseis."""

    id: str = Field(..., description="Unieke ID van de eis")
    standaard: str = Field(..., description="De standaard waar de eis onder valt")
    titel: str = Field(..., description="Titel van de eis")
    eisomschrijving: str = Field(..., description="Volledige omschrijving van de eis")
    uitleg: str = Field(default="", description="Uitleg bij de eis")
    focuspunten: str = Field(default="", description="Focuspunten voor de eis")
    tips: str = Field(default="", description="Tips voor het invullen")
    voorbeelden: str = Field(default="", description="Voorbeelden")


class EisenListResponse(BaseModel):
    """Response met lijst van alle eisen."""

    eisen: list[EisSummary] = Field(..., description="Lijst van alle eisen")
    totaal: int = Field(..., description="Totaal aantal eisen")


class HealthResponse(BaseModel):
    """Response van de health check endpoint."""

    status: str = Field(..., description="Status van de API")
    ollama: str = Field(..., description="Status van de Ollama verbinding")
    model: str = Field(..., description="Naam van het actieve model")
    message: str = Field(default="", description="Extra informatie")
