"""DeugdelijkheidseisAssistent - Hoofdklasse voor de AI-assistent.

Dit is de centrale class voor alle AI-interacties in de Kwaliteitszorg applicatie.
Ondersteunt chat met history, document context, en RAG integratie.
"""

from typing import Callable, Dict, List, Optional

import ollama

from config import settings
from config.settings import logger
from ..models.school_invulling import SchoolInvulling
from ..utils.database import DatabaseError, load_database, load_deugdelijkheidseis
from .prompts import (
    SYSTEM_PROMPT,
    build_document_context,
    build_rag_context,
    generate_document_salt,
    get_standaard_task_instruction,
    get_task_instruction,
)


class OllamaConnectionError(Exception):
    """Exception wanneer Ollama niet bereikbaar is."""

    pass


class ModelNotFoundError(Exception):
    """Exception wanneer het AI model niet gevonden wordt."""

    pass


class DeugdelijkheidseisAssistent:
    """
    AI-assistent voor hulp bij deugdelijkheidseisen.

    Deze class beheert alle interacties met het LLM model voor:
    - Feedback op schoolinvullingen
    - Uitleg van eisen
    - Suggesties voor verbeteringen
    - Algemene vragen over deugdelijkheidseisen

    Attributes:
        model: Naam van het Ollama model
        database_path: Pad naar de eisen database
        database: Geladen database dictionary
        chat_history: Lijst van vorige berichten in de conversatie
        document_salt: Unieke salt voor prompt injection preventie
    """

    def __init__(self, model: Optional[str] = None, database_path: Optional[str] = None):
        """
        Initialiseer de assistent.

        Args:
            model: Optioneel Ollama model naam (default uit settings)
            database_path: Optioneel pad naar database (default uit settings)

        Raises:
            DatabaseError: Als de database niet geladen kan worden
        """
        self.model = model or settings.MODEL_NAME
        self.database_path = database_path or str(settings.DATABASE_PATH)
        self.database = load_database(self.database_path)
        self.chat_history: List[Dict[str, str]] = []
        self.standaard_chat_history: List[Dict[str, str]] = []
        # Unieke salt per sessie voor document tags (prompt injection preventie)
        self.document_salt = generate_document_salt()

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
        document_text: Optional[str] = None,
        document_filename: Optional[str] = None,
        rag_context: Optional[str] = None,
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
            document_text: Optionele tekst uit geüpload document
            document_filename: Naam van het geüploade document
            rag_context: Optionele context van RAG-opgehaalde passages

        Returns:
            Het antwoord van de assistent
        """
        # Bouw de system prompt met alle context
        system_content = self._build_system_message(
            eis_id, school_invulling, vraag_type, document_text, document_filename, rag_context
        )

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
        self,
        eis_id: str,
        school_invulling: SchoolInvulling,
        vraag_type: str,
        document_text: Optional[str] = None,
        document_filename: Optional[str] = None,
        rag_context: Optional[str] = None,
    ) -> str:
        """Bouw de system message met alle context."""
        eis = load_deugdelijkheidseis(self.database, eis_id)

        # Bepaal welke context beschikbaar is
        has_document = bool(document_text)
        has_rag = bool(rag_context)

        # Haal task instructie op met de juiste flags
        task_instruction = get_task_instruction(
            vraag_type,
            has_document=has_document,
            has_rag=has_rag,
        )

        base_message = f"""{SYSTEM_PROMPT}

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

        # Voeg RAG context toe indien aanwezig (heeft prioriteit boven enkel document)
        if rag_context:
            rag_context_formatted = build_rag_context(
                rag_chunks_text=rag_context,
                salt=self.document_salt,
            )
            base_message += f"\n\n---\n{rag_context_formatted}"
        # Voeg document context toe indien aanwezig (alleen als geen RAG)
        elif document_text and document_filename:
            document_context = build_document_context(
                document_text=document_text,
                filename=document_filename,
                salt=self.document_salt,
            )
            base_message += f"\n\n---\n{document_context}"

        return base_message

    def chat_standaard(
        self,
        standaard_naam: str,
        eisen_met_invullingen: Dict[str, "SchoolInvulling"],
        vraag: str,
        vraag_type: str = "algemeen",
        stream_handler: Optional[Callable[[str], None]] = None,
        naslagwerk: str = "",
        standaard_omschrijving: str = "",
        rag_context: Optional[str] = None,
    ) -> str:
        """
        Voer een chat uit op standaard-niveau (meerdere eisen tegelijk).

        Args:
            standaard_naam: Naam van de standaard (bijv. "OP4 - Onderwijstijd")
            eisen_met_invullingen: Dict van eis_id -> SchoolInvulling
            vraag: De vraag van de gebruiker
            vraag_type: Type vraag (feedback/uitleg/suggestie/algemeen)
            stream_handler: Optionele callback voor streaming
            naslagwerk: Standaard-specifiek naslagwerk (blog, kenniskaart)
            standaard_omschrijving: Korte omschrijving van de standaard
            rag_context: Optionele context van RAG-opgehaalde passages

        Returns:
            Het antwoord van de assistent
        """
        system_content = self._build_standaard_system_message(
            standaard_naam=standaard_naam,
            eisen_met_invullingen=eisen_met_invullingen,
            vraag_type=vraag_type,
            naslagwerk=naslagwerk,
            standaard_omschrijving=standaard_omschrijving,
            rag_context=rag_context,
        )

        messages = [{"role": "system", "content": system_content}]
        for msg in self.standaard_chat_history:
            messages.append(msg)
        messages.append({"role": "user", "content": vraag})

        antwoord = self._generate(messages, stream_handler)

        self.standaard_chat_history.append({"role": "user", "content": vraag})
        self.standaard_chat_history.append({"role": "assistant", "content": antwoord})

        max_messages = settings.MAX_CONVERSATION_HISTORY * 2
        if len(self.standaard_chat_history) > max_messages:
            self.standaard_chat_history = self.standaard_chat_history[-max_messages:]

        return antwoord

    def _build_standaard_system_message(
        self,
        standaard_naam: str,
        eisen_met_invullingen: Dict[str, "SchoolInvulling"],
        vraag_type: str,
        naslagwerk: str = "",
        standaard_omschrijving: str = "",
        rag_context: Optional[str] = None,
    ) -> str:
        """Bouw de system message voor standaard-niveau chat (lean context)."""
        has_rag = bool(rag_context)
        task_instruction = get_standaard_task_instruction(vraag_type, has_rag=has_rag)

        # Header
        parts = [
            SYSTEM_PROMPT,
            f"\n\n---\nHUIDIGE TAAK: {task_instruction}\n---",
            f"\nSTANDAARD: {standaard_naam}",
        ]

        if standaard_omschrijving:
            parts.append(f"Omschrijving: {standaard_omschrijving}")

        # Naslagwerk (blog, kenniskaart)
        if naslagwerk:
            parts.append(f"\nNASLAGWERK OVER DEZE STANDAARD:\n{naslagwerk}")

        # Eisen met lean context (eisomschrijving + uitleg + invulling)
        parts.append("\n---\nOVERZICHT EISEN EN INVULLINGEN:")

        for eis_id in sorted(eisen_met_invullingen.keys()):
            invulling = eisen_met_invullingen[eis_id]
            try:
                eis = load_deugdelijkheidseis(self.database, eis_id)
            except Exception:
                continue

            parts.append(f"\n=== {eis['id']} - {eis['titel']} ===")
            parts.append(f"Eisomschrijving:\n{eis['eisomschrijving']}")
            parts.append(f"\nUitleg:\n{eis['uitleg']}")
            parts.append(f"\nInvulling van de school:\n{invulling.to_text()}")

        base_message = "\n".join(parts)

        # RAG context
        if rag_context:
            rag_formatted = build_rag_context(
                rag_chunks_text=rag_context,
                salt=self.document_salt,
            )
            base_message += f"\n\n---\n{rag_formatted}"

        return base_message

    def reset_standaard_chat(self):
        """Reset de standaard chatgeschiedenis."""
        self.standaard_chat_history = []

    def _generate(
        self,
        messages: List[Dict],
        stream_handler: Optional[Callable[[str], None]],
    ) -> str:
        """
        Genereer een antwoord via Ollama.

        Args:
            messages: Lijst van chat berichten (system, user, assistant)
            stream_handler: Optionele callback voor streaming output

        Returns:
            Het gegenereerde antwoord als string

        Raises:
            OllamaConnectionError: Als Ollama niet bereikbaar is
            ModelNotFoundError: Als het model niet gevonden wordt
            RuntimeError: Bij andere Ollama fouten
        """
        options = {
            "temperature": settings.TEMPERATURE_DEFAULT,
            "num_predict": settings.MAX_GENERATE_TOKENS,
            "top_p": settings.TOP_P,
            "repeat_penalty": settings.REPEAT_PENALTY,
            "num_ctx": settings.NUM_CTX,
        }

        try:
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

        except Exception as e:
            error_msg = str(e).lower()
            if "connection refused" in error_msg or "connect" in error_msg:
                logger.error("Ollama verbinding verloren: %s", e)
                raise OllamaConnectionError(
                    "Kan geen verbinding maken met Ollama. "
                    "Controleer of Ollama draait met: ollama serve"
                ) from e
            elif "not found" in error_msg:
                logger.error("Model niet gevonden: %s", e)
                raise ModelNotFoundError(
                    f"Model '{self.model}' niet gevonden. "
                    f"Installeer met: ollama pull {self.model}"
                ) from e
            else:
                logger.error("Ollama fout: %s", e)
                raise RuntimeError(f"Er ging iets mis bij het genereren: {e}") from e

    def reset_chat(self):
        """Reset de chatgeschiedenis en genereer nieuwe document salt."""
        self.chat_history = []
        self.document_salt = generate_document_salt()

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
