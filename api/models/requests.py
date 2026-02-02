"""API request models met input validatie."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Maximum karakters per veld
MAX_VELD_CHARS = 5000  # Per invullingsveld (ambitie, etc.)
MAX_VRAAG_CHARS = 2000  # Voor de vraag zelf
MAX_EIS_ID_CHARS = 20   # Voor eis ID


class SchoolInvullingRequest(BaseModel):
    """School invulling voor een deugdelijkheidseis met lengte validatie."""

    ambitie: str = Field(
        default="",
        description="De ambitie van de school",
        max_length=MAX_VELD_CHARS,
    )
    beoogd_resultaat: str = Field(
        default="",
        description="Het beoogde resultaat",
        max_length=MAX_VELD_CHARS,
    )
    concrete_acties: str = Field(
        default="",
        description="Concrete acties die de school neemt",
        max_length=MAX_VELD_CHARS,
    )
    wijze_van_meten: str = Field(
        default="",
        description="Hoe de school succes meet",
        max_length=MAX_VELD_CHARS,
    )

    @field_validator("ambitie", "beoogd_resultaat", "concrete_acties", "wijze_van_meten", mode="before")
    @classmethod
    def truncate_if_too_long(cls, v: str) -> str:
        """Trunceer velden die te lang zijn (met waarschuwing in logs)."""
        if isinstance(v, str) and len(v) > MAX_VELD_CHARS:
            return v[:MAX_VELD_CHARS]
        return v


class ChatRequest(BaseModel):
    """Request voor de chat endpoint met input validatie."""

    eis_id: str = Field(
        ...,
        description="ID van de deugdelijkheidseis (bijv. 'VS 1.5')",
        max_length=MAX_EIS_ID_CHARS,
    )
    vraag: str = Field(
        ...,
        description="De vraag van de gebruiker",
        max_length=MAX_VRAAG_CHARS,
    )
    vraag_type: Literal["feedback", "uitleg", "suggestie", "algemeen"] = Field(
        default="algemeen",
        description="Type vraag bepaalt de instructies voor de AI",
    )
    school_invulling: SchoolInvullingRequest = Field(
        default_factory=SchoolInvullingRequest,
        description="De invulling van de school voor deze eis",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "eis_id": "VS 1.5",
                    "vraag": "Geef feedback op onze invulling",
                    "vraag_type": "feedback",
                    "school_invulling": {
                        "ambitie": "Wij streven naar een veilig schoolklimaat waar ieder kind zich thuis voelt.",
                        "beoogd_resultaat": "- 95% van de leerlingen voelt zich veilig\n- Pestincidenten dalen met 50%",
                        "concrete_acties": "- Wekelijkse klassengesprekken\n- Training voor leerkrachten",
                        "wijze_van_meten": "- Jaarlijkse veiligheidsmonitor\n- Incidentenregistratie",
                    },
                }
            ]
        }
    }
