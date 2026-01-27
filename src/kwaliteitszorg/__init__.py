"""
Kwaliteitszorg AI - Deugdelijkheidseisen Assistent

Een AI-assistent die scholen helpt met het waarderingskader
van de Inspectie van het Onderwijs.
"""

from .models.school_invulling import SchoolInvulling
from .assistant.assistent import DeugdelijkheidseisAssistent

__version__ = "2.1.0"
__all__ = ["SchoolInvulling", "DeugdelijkheidseisAssistent"]
