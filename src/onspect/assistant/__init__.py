"""Assistant module voor OnSpect AI."""

from .assistent import DeugdelijkheidseisAssistent
from .prompts import SYSTEM_PROMPT, get_task_instruction

__all__ = [
    "DeugdelijkheidseisAssistent",
    "SYSTEM_PROMPT",
    "get_task_instruction",
]
