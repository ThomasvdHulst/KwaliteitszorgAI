"""DeugdelijkheidseisAssistent - Hoofdklasse voor de AI-assistent."""

from typing import Callable, Dict, List, Optional

import ollama

from config import settings
from ..models.school_invulling import SchoolInvulling
from ..utils.database import load_database, load_deugdelijkheidseis
from .prompts import SYSTEM_PROMPT, get_task_instruction


class DeugdelijkheidseisAssistent:
    """AI-assistent voor hulp bij deugdelijkheidseisen."""

    def __init__(self, model: str = None, database_path: str = None):
        self.model = model or settings.MODEL_NAME
        self.database_path = database_path or str(settings.DATABASE_PATH)
        self.database = load_database(self.database_path)
        self.chat_history: List[Dict[str, str]] = []

    def get_deugdelijkheidseis(self, eis_id: str) -> Dict:
        """Haal deugdelijkheidseis op uit database."""
        return load_deugdelijkheidseis(self.database, eis_id)

    def chat(
        self,
        eis_id: str,
        school_invulling: SchoolInvulling,
        vraag: str,
        vraag_type: str = "algemeen",
        stream_handler: Optional[Callable[[str], None]] = None,
    ) -> str:
        """
        Voer een chat-bericht uit met de assistent.

        De volledige context (eis + schoolinvulling) wordt bij elk bericht meegestuurd,
        samen met de chatgeschiedenis. Dit is hoe echte AI-assistenten werken.

        Args:
            eis_id: ID van de deugdelijkheidseis
            school_invulling: De invulling van de school
            vraag: De vraag van de gebruiker
            vraag_type: Type vraag (feedback/uitleg/suggestie/algemeen)
            stream_handler: Optionele callback voor streaming

        Returns:
            Het antwoord van de assistent
        """
        # Bouw de system prompt met alle context
        system_content = self._build_system_message(eis_id, school_invulling, vraag_type)

        # Bouw de messages array
        messages = [{"role": "system", "content": system_content}]

        # Voeg chatgeschiedenis toe
        for msg in self.chat_history:
            messages.append(msg)

        # Voeg huidige vraag toe
        messages.append({"role": "user", "content": vraag})

        # Genereer antwoord
        antwoord = self._generate(messages, stream_handler)

        # Sla op in geschiedenis
        self.chat_history.append({"role": "user", "content": vraag})
        self.chat_history.append({"role": "assistant", "content": antwoord})

        # Beperk geschiedenis tot laatste N berichten
        max_messages = settings.MAX_CONVERSATION_HISTORY * 2  # user + assistant pairs
        if len(self.chat_history) > max_messages:
            self.chat_history = self.chat_history[-max_messages:]

        return antwoord

    def _build_system_message(
        self, eis_id: str, school_invulling: SchoolInvulling, vraag_type: str
    ) -> str:
        """Bouw de system message met alle context."""
        eis = load_deugdelijkheidseis(self.database, eis_id)
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

    def _generate(
        self,
        messages: List[Dict],
        stream_handler: Optional[Callable[[str], None]],
    ) -> str:
        """Genereer een antwoord via Ollama."""
        options = {
            "temperature": settings.TEMPERATURE_DEFAULT,
            "num_predict": settings.MAX_GENERATE_TOKENS,
            "top_p": settings.TOP_P,
            "repeat_penalty": settings.REPEAT_PENALTY,
            "num_ctx": settings.NUM_CTX,
        }

        if stream_handler:
            antwoord = ""
            for chunk in ollama.chat(
                model=self.model,
                messages=messages,
                options=options,
                stream=True,
            ):
                text = chunk.get("message", {}).get("content", "")
                if text:
                    antwoord += text
                    stream_handler(text)
            return antwoord
        else:
            response = ollama.chat(
                model=self.model, messages=messages, options=options
            )
            return response["message"]["content"]

    def reset_chat(self):
        """Reset de chatgeschiedenis."""
        self.chat_history = []

    def get_chat_history(self) -> List[Dict[str, str]]:
        """Haal de chatgeschiedenis op."""
        return self.chat_history.copy()

    # Backwards compatibility
    def beantwoord_vraag(self, deugdelijkheidseis_id: str, school_invulling: SchoolInvulling,
                         vraag: str, vraag_type: str = "algemeen", stream: bool = False,
                         stream_handler: Optional[Callable[[str], None]] = None) -> Dict:
        """Backwards compatible methode."""
        handler = stream_handler if stream else None
        antwoord = self.chat(deugdelijkheidseis_id, school_invulling, vraag, vraag_type, handler)
        return {"antwoord": antwoord, "vraag_type": vraag_type}

    def reset_conversatie(self):
        """Backwards compatible methode."""
        self.reset_chat()
