"""Assistant module voor Kwaliteitszorg AI."""

from .assistent import (
    DeugdelijkheidseisAssistent,
    ModelNotFoundError,
    OllamaConnectionError,
)
from .prompts import SYSTEM_PROMPT, get_task_instruction

__all__ = [
    "DeugdelijkheidseisAssistent",
    "OllamaConnectionError",
    "ModelNotFoundError",
    "SYSTEM_PROMPT",
    "get_task_instruction",
]
