"""Chat service - wrapper rond DeugdelijkheidseisAssistent."""

import re

from api.config import get_settings
from api.core import DeugdelijkheidseisAssistent, SchoolInvulling
from api.core.database import EisNotFoundError
from api.models.requests import ChatRequest
from api.models.responses import ChatResponse

# Regex voor geldige eis IDs (bijv. "VS 1.5", "OP 4.1", etc.)
EIS_ID_PATTERN = re.compile(r"^[A-Z]{2}\s\d+\.\d+$")


class ChatService:
    """Service voor chat functionaliteit."""

    def __init__(self):
        """Initialize met settings."""
        self.settings = get_settings()

    def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Verwerk een chat request.

        Maakt een nieuwe assistent instance per request (stateless).

        Args:
            request: Het chat request met eis_id, vraag, en school_invulling

        Returns:
            ChatResponse met het antwoord van de AI

        Raises:
            ValueError: Bij ongeldig eis_id formaat
            EisNotFoundError: Als de eis niet in de database staat
            RuntimeError: Bij Ollama connectie of model fouten
        """
        # Valideer eis_id formaat
        if not EIS_ID_PATTERN.match(request.eis_id):
            raise ValueError(
                f"Ongeldig eis ID formaat: '{request.eis_id}'. "
                f"Verwacht formaat: 'XX 0.0' (bijv. 'VS 1.5', 'OP 4.1')"
            )

        # Maak een nieuwe assistent per request (stateless)
        assistent = DeugdelijkheidseisAssistent(model=self.settings.model_name)

        # Converteer request model naar SchoolInvulling dataclass
        school_invulling = SchoolInvulling(
            ambitie=request.school_invulling.ambitie,
            beoogd_resultaat=request.school_invulling.beoogd_resultaat,
            concrete_acties=request.school_invulling.concrete_acties,
            wijze_van_meten=request.school_invulling.wijze_van_meten,
        )

        # Voer chat uit (stateless, geen streaming)
        # Kan EisNotFoundError of RuntimeError gooien
        antwoord = assistent.chat(
            eis_id=request.eis_id,
            school_invulling=school_invulling,
            vraag=request.vraag,
            vraag_type=request.vraag_type,
        )

        return ChatResponse(
            antwoord=antwoord,
            eis_id=request.eis_id,
            vraag_type=request.vraag_type,
        )
