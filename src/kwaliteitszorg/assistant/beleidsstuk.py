"""
Beleidsstuk-module voor Kwaliteitszorg AI.

Genereert samenhangende beleidsstukken per standaard op basis van de
schoolinvullingen. Per hoofdstuk (Ambitie, Beoogde Resultaten, etc.)
combineert de AI de invullingen van alle eisen tot een coherent verhaal.

Kernregel: verbindende tekst mag, maar concreet beleid verzinnen mag NIET.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import ollama

from config import settings
from config.settings import logger
from ..models.school_invulling import SchoolInvulling
from ..utils.database import load_database
from .assistent import ModelNotFoundError, OllamaConnectionError
from .prompts import build_beleidsstuk_chapter_prompt


CHAPTER_ORDER = [
    "ambitie",
    "beoogd_resultaat",
    "wettelijk_kader",
    "concrete_aanpak",
    "monitoring",
]

CHAPTER_LABELS = {
    "ambitie": "Ambitie",
    "beoogd_resultaat": "Beoogde Resultaten",
    "wettelijk_kader": "Wettelijk Kader",
    "concrete_aanpak": "Concrete Aanpak",
    "monitoring": "Monitoring",
}

# Mapping van chapter_type naar het PDCA-veld in SchoolInvulling
CHAPTER_TO_PDCA = {
    "ambitie": "ambitie",
    "beoogd_resultaat": "beoogd_resultaat",
    "concrete_aanpak": "concrete_acties",
    "monitoring": "wijze_van_meten",
}

# Keywords die aangeven dat wettelijk kader relevant is
_WETTELIJK_KEYWORDS = [
    "WVO", "WPO", "artikel", "wettelijk", "WETTELIJKE BASIS",
    "wet op", "wetgeving", "juridisch", "wetsartikel",
]


@dataclass
class HoofdstukResultaat:
    """Resultaat van één gegenereerd hoofdstuk."""
    chapter_type: str
    label: str
    content: str
    skipped: bool = False
    error: Optional[str] = None


@dataclass
class BeleidsstukResultaat:
    """Resultaat van een compleet beleidsstuk."""
    success: bool
    standaard_naam: str
    hoofdstukken: List[HoofdstukResultaat] = field(default_factory=list)
    error: Optional[str] = None


class BeleidsstukGenerator:
    """
    Genereert samenhangende beleidsstukken per standaard.

    Per hoofdstuk worden de invullingen van alle eisen gecombineerd
    tot een coherent verhaal door de AI.
    """

    def __init__(self, model: str = None, database_path: str = None):
        self.model = model or settings.MODEL_NAME
        self.database_path = database_path or str(settings.DATABASE_PATH)
        self.database = load_database(self.database_path)

    def genereer_beleidsstuk(
        self,
        standaard_naam: str,
        eis_lijst: list,
        invullingen: Dict[str, SchoolInvulling],
        progress_callback: Optional[Callable] = None,
    ) -> BeleidsstukResultaat:
        """
        Genereer een compleet beleidsstuk voor een standaard.

        Args:
            standaard_naam: Naam van de standaard
            eis_lijst: Lijst van (eis_id, eis_data) tuples
            invullingen: Dict van eis_id -> SchoolInvulling
            progress_callback: Optionele callback(current, total, label)

        Returns:
            BeleidsstukResultaat met alle hoofdstukken
        """
        include_wettelijk = self._should_include_wettelijk_kader(eis_lijst)

        chapters_to_generate = [
            ch for ch in CHAPTER_ORDER
            if ch != "wettelijk_kader" or include_wettelijk
        ]
        total = len(chapters_to_generate)

        already_generated: Dict[str, str] = {}
        hoofdstukken: List[HoofdstukResultaat] = []

        for idx, chapter_type in enumerate(chapters_to_generate):
            label = CHAPTER_LABELS[chapter_type]

            if progress_callback:
                progress_callback(idx, total, label)

            try:
                resultaat = self._genereer_hoofdstuk(
                    chapter_type=chapter_type,
                    standaard_naam=standaard_naam,
                    eis_lijst=eis_lijst,
                    invullingen=invullingen,
                    already_generated=already_generated,
                )
                hoofdstukken.append(resultaat)

                if not resultaat.skipped and not resultaat.error:
                    already_generated[chapter_type] = resultaat.content

            except (OllamaConnectionError, ModelNotFoundError) as e:
                # Fatale fouten: stop generatie
                return BeleidsstukResultaat(
                    success=False,
                    standaard_naam=standaard_naam,
                    hoofdstukken=hoofdstukken,
                    error=str(e),
                )
            except Exception as e:
                logger.error("Fout bij hoofdstuk %s: %s", chapter_type, e)
                hoofdstukken.append(HoofdstukResultaat(
                    chapter_type=chapter_type,
                    label=label,
                    content="",
                    error=f"Fout bij genereren: {e}",
                ))

        if progress_callback:
            progress_callback(total, total, "Gereed")

        return BeleidsstukResultaat(
            success=True,
            standaard_naam=standaard_naam,
            hoofdstukken=hoofdstukken,
        )

    def _should_include_wettelijk_kader(self, eis_lijst: list) -> bool:
        """
        Bepaal of het hoofdstuk 'Wettelijk Kader' relevant is.

        Doorzoekt eisomschrijving + uitleg op juridische keywords.
        Deterministisch, geen LLM call.
        """
        for _eis_id, eis_data in eis_lijst:
            text = (
                eis_data.get("eisomschrijving", "")
                + " "
                + eis_data.get("uitleg", "")
            ).upper()
            for keyword in _WETTELIJK_KEYWORDS:
                if keyword.upper() in text:
                    return True
        return False

    def _genereer_hoofdstuk(
        self,
        chapter_type: str,
        standaard_naam: str,
        eis_lijst: list,
        invullingen: Dict[str, SchoolInvulling],
        already_generated: Dict[str, str],
    ) -> HoofdstukResultaat:
        """
        Genereer één hoofdstuk van het beleidsstuk.

        Als er geen input is voor dit chapter, return placeholder zonder LLM call.
        """
        label = CHAPTER_LABELS[chapter_type]

        # Verzamel input per eis
        eis_inputs = self._collect_chapter_input(
            chapter_type, eis_lijst, invullingen
        )

        # Check of er input is
        if not eis_inputs:
            return HoofdstukResultaat(
                chapter_type=chapter_type,
                label=label,
                content="[Nog niet ingevuld door de school]",
                skipped=True,
            )

        # Bouw prompts
        system_prompt = build_beleidsstuk_chapter_prompt(
            chapter_type=chapter_type,
            standaard_naam=standaard_naam,
            already_generated=already_generated or None,
        )

        user_message = self._build_user_message(
            chapter_type, label, standaard_naam, eis_inputs,
            eis_lijst=eis_lijst,
        )

        # Genereer
        content = self._generate(system_prompt, user_message)

        return HoofdstukResultaat(
            chapter_type=chapter_type,
            label=label,
            content=content,
        )

    def _collect_chapter_input(
        self,
        chapter_type: str,
        eis_lijst: list,
        invullingen: Dict[str, SchoolInvulling],
    ) -> List[tuple]:
        """
        Verzamel de relevante input per eis voor dit chapter.

        Returns:
            Lijst van (eis_id, eis_titel, tekst) tuples met niet-lege input
        """
        result = []

        if chapter_type == "wettelijk_kader":
            # Wettelijk kader gebruikt eisomschrijvingen + uitleg uit database
            for eis_id, eis_data in eis_lijst:
                eisomschrijving = eis_data.get("eisomschrijving", "")
                uitleg = eis_data.get("uitleg", "")
                if eisomschrijving:
                    tekst = eisomschrijving
                    if uitleg:
                        tekst += f"\n\nUitleg:\n{uitleg}"
                    result.append((
                        eis_id,
                        eis_data.get("titel", ""),
                        tekst,
                    ))
        else:
            # PDCA chapters gebruiken schoolinvullingen
            pdca_field = CHAPTER_TO_PDCA.get(chapter_type)
            if not pdca_field:
                return result

            for eis_id, eis_data in eis_lijst:
                invulling = invullingen.get(eis_id)
                if not invulling:
                    continue
                tekst = getattr(invulling, pdca_field, "")
                if tekst and tekst.strip():
                    result.append((
                        eis_id,
                        eis_data.get("titel", ""),
                        tekst,
                    ))

        return result

    def _build_user_message(
        self,
        chapter_type: str,
        label: str,
        standaard_naam: str,
        eis_inputs: List[tuple],
        eis_lijst: list = None,
    ) -> str:
        """Bouw het user message met school inputs per eis."""
        parts = [
            f'Herformuleer de schoolinvullingen hieronder tot beleidstekst '
            f'voor het hoofdstuk "{label}".',
            "",
        ]

        if chapter_type == "wettelijk_kader":
            parts.append(
                "Hieronder staan de eisomschrijvingen en uitleg per eis:"
            )
        else:
            parts.append("SCHOOLINVULLINGEN:")

        parts.append("")

        for eis_id, eis_titel, tekst in eis_inputs:
            parts.append(f"=== {eis_id} - {eis_titel} ===")
            parts.append(tekst)
            parts.append("")

        if chapter_type == "wettelijk_kader":
            parts.append(
                "Vat de wettelijke kaders samen tot een samenhangend geheel."
            )
        else:
            parts.append(
                "Herformuleer bovenstaande teksten tot één samenhangend geheel. "
                "Voeg GEEN nieuwe inhoud, doelen, acties of details toe."
            )

        return "\n".join(parts)

    def _generate(self, system_prompt: str, user_message: str) -> str:
        """
        Genereer response via Ollama (plain text, geen JSON mode).

        Args:
            system_prompt: De system prompt met context
            user_message: Het gebruikersbericht

        Returns:
            Gegenereerde tekst

        Raises:
            OllamaConnectionError: Als Ollama niet bereikbaar is
            ModelNotFoundError: Als het model niet gevonden wordt
            RuntimeError: Bij andere Ollama fouten
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        options = {
            "temperature": 0.2,
            "num_predict": 2000,
            "num_ctx": 32768,
        }

        try:
            result = ollama.chat(
                model=self.model,
                messages=messages,
                options=options,
            )
            return result["message"]["content"]

        except Exception as e:
            error_msg = str(e).lower()
            if "connection refused" in error_msg or "connect" in error_msg:
                logger.error("Ollama verbinding verloren: %s", e)
                raise OllamaConnectionError(
                    "Kan geen verbinding maken met Ollama. "
                    "Controleer of Ollama draait."
                ) from e
            elif "not found" in error_msg:
                logger.error("Model niet gevonden: %s", e)
                raise ModelNotFoundError(
                    f"Model '{self.model}' niet gevonden. "
                    f"Installeer met: ollama pull {self.model}"
                ) from e
            else:
                logger.error("Ollama fout bij beleidsstuk: %s", e)
                raise RuntimeError(f"Fout bij genereren hoofdstuk: {e}") from e
