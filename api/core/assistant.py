"""DeugdelijkheidseisAssistent voor de OnSpectAI API.

Vereenvoudigde versie: geen streaming, geen RAG, geen document upload.
Elke request is stateless (geen chat history).
"""

import logging
from typing import Dict, List, Optional

import ollama

from api.config import get_settings
from .database import EisNotFoundError, load_database, load_deugdelijkheidseis
from .prompts import SYSTEM_PROMPT, get_task_instruction
from .school_invulling import SchoolInvulling

logger = logging.getLogger(__name__)


class DeugdelijkheidseisAssistent:
    """AI-assistent voor hulp bij deugdelijkheidseisen (API versie)."""

    def __init__(self, model: str = None, database_path: str = None):
        settings = get_settings()
        self.model = model or settings.model_name
        self.database_path = database_path or settings.database_path
        self.database = load_database(self.database_path)

    def get_deugdelijkheidseis(self, eis_id: str) -> Optional[Dict]:
        """
        Haal deugdelijkheidseis op uit database.

        Args:
            eis_id: ID van de eis (bijv. 'VS 1.5')

        Returns:
            Dictionary met eis data, of None als niet gevonden
        """
        return load_deugdelijkheidseis(self.database, eis_id)

    def chat(
        self,
        eis_id: str,
        school_invulling: SchoolInvulling,
        vraag: str,
        vraag_type: str = "algemeen",
    ) -> str:
        """
        Beantwoord een vraag over een deugdelijkheidseis.

        Dit is een stateless operatie - geen chat history wordt bijgehouden.

        Args:
            eis_id: ID van de deugdelijkheidseis
            school_invulling: De invulling van de school
            vraag: De vraag van de gebruiker
            vraag_type: Type vraag (feedback/uitleg/suggestie/algemeen)

        Returns:
            Het antwoord van de assistent
        """
        # Bouw de system prompt met alle context
        system_content = self._build_system_message(eis_id, school_invulling, vraag_type)

        # Bouw messages array (geen history - stateless)
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": vraag},
        ]

        # Genereer antwoord
        return self._generate(messages)

    def _build_system_message(
        self,
        eis_id: str,
        school_invulling: SchoolInvulling,
        vraag_type: str,
    ) -> str:
        """
        Bouw de system message met alle context.

        Args:
            eis_id: ID van de deugdelijkheidseis
            school_invulling: De invulling van de school
            vraag_type: Type vraag (feedback/uitleg/suggestie/algemeen)

        Returns:
            De volledige system prompt met context

        Raises:
            EisNotFoundError: Als de eis niet in de database staat
        """
        eis = load_deugdelijkheidseis(self.database, eis_id, raise_on_not_found=True)
        task_instruction = get_task_instruction(vraag_type)

        return f"""{SYSTEM_PROMPT}

---
HUIDIGE TAAK: {task_instruction}
---

DEUGDELIJKHEIDSEIS: {eis['id']} - {eis['titel']}
Standaard: {eis['standaard']}

Eisomschrijving:
{eis['eisomschrijving']}

Uitleg:
{eis['uitleg']}

Focuspunten:
{eis['focuspunten']}

Tips:
{eis['tips']}

Voorbeelden:
{eis['voorbeelden']}

---

INVULLING VAN DE SCHOOL:
{school_invulling.to_text()}"""

    def _generate(self, messages: List[Dict]) -> str:
        """Genereer een antwoord via Ollama."""
        settings = get_settings()

        options = {
            "temperature": settings.temperature,
            "num_predict": settings.max_tokens,
            "top_p": settings.top_p,
            "repeat_penalty": settings.repeat_penalty,
            "num_ctx": settings.num_ctx,
        }

        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options=options,
            )
            return response["message"]["content"]

        except Exception as e:
            error_msg = str(e).lower()
            if "connection refused" in error_msg or "connect" in error_msg:
                logger.error("Ollama verbinding verloren: %s", e)
                raise RuntimeError(
                    "Kan geen verbinding maken met Ollama. "
                    "Controleer of Ollama draait."
                ) from e
            elif "not found" in error_msg:
                logger.error("Model niet gevonden: %s", e)
                raise RuntimeError(
                    f"Model '{self.model}' niet gevonden. "
                    f"Installeer met: ollama pull {self.model}"
                ) from e
            else:
                logger.error("Ollama fout: %s", e)
                raise RuntimeError(f"Er ging iets mis bij het genereren: {e}") from e
