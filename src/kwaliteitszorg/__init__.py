"""
Kwaliteitszorg AI - Deugdelijkheidseisen Assistent

Een AI-assistent die scholen helpt met het waarderingskader
van de Inspectie van het Onderwijs.

Componenten:
- DeugdelijkheidseisAssistent: Hoofdclass voor AI interacties
- SchoolInvulling: Dataclass voor schoolinvullingen (PDCA)
- SuggestieGenerator: Genereer tekstsuggesties per veld
- RAGRetriever: Document indexering en retrieval (optioneel)
"""

from .assistant.assistent import (
    DeugdelijkheidseisAssistent,
    ModelNotFoundError,
    OllamaConnectionError,
)
from .models.school_invulling import SchoolInvulling
from .utils.database import DatabaseError, EisNotFoundError

__version__ = "2.1.0"

__all__ = [
    # Main classes
    "SchoolInvulling",
    "DeugdelijkheidseisAssistent",
    # Exceptions
    "OllamaConnectionError",
    "ModelNotFoundError",
    "EisNotFoundError",
    "DatabaseError",
]
