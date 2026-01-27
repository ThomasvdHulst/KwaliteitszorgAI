"""
Suggestie-module voor Kwaliteitszorg AI.

Deze module is experimenteel en kan worden verwijderd zonder impact op de rest.
Biedt functionaliteit voor het genereren van concrete tekstsuggesties per veld.
"""

import json
import re
from dataclasses import dataclass
from typing import Dict, Optional

import ollama

from config import settings
from ..models.school_invulling import SchoolInvulling
from ..utils.database import load_database, load_deugdelijkheidseis


@dataclass
class VeldSuggestie:
    """Een suggestie voor één veld."""
    veld: str
    heeft_suggestie: bool
    huidige_tekst: str
    nieuwe_tekst: Optional[str] = None
    toelichting: Optional[str] = None


@dataclass
class SuggestieResultaat:
    """Resultaat van een suggestie-aanvraag."""
    success: bool
    suggesties: Dict[str, VeldSuggestie]
    error: Optional[str] = None
    raw_response: Optional[str] = None


SUGGESTIE_PROMPT = """Je bent Kwaliteitszorg AI. Je taak is om concrete tekstsuggesties te geven voor de schoolinvulling.

Analyseer de huidige invulling en geef voor elk veld dat verbeterd kan worden een concrete nieuwe tekst.

BELANGRIJK: Antwoord ALLEEN met valid JSON in exact dit formaat, zonder extra tekst:
{
  "ambitie": {
    "heeft_suggestie": true of false,
    "nieuwe_tekst": "de complete nieuwe tekst" of null,
    "toelichting": "korte uitleg waarom" of null
  },
  "beoogd_resultaat": {
    "heeft_suggestie": true of false,
    "nieuwe_tekst": "..." of null,
    "toelichting": "..." of null
  },
  "concrete_acties": {
    "heeft_suggestie": true of false,
    "nieuwe_tekst": "..." of null,
    "toelichting": "..." of null
  },
  "wijze_van_meten": {
    "heeft_suggestie": true of false,
    "nieuwe_tekst": "..." of null,
    "toelichting": "..." of null
  }
}

BELANGRIJKE REGELS VOOR SUGGESTIES:
- BEHOUD de originele tekst van de school! Verwijder alleen tekst die echt niets met de eis te maken heeft.
- Suggesties zijn meestal TOEVOEGINGEN aan de bestaande tekst, geen vervanging.
- Bij concrete_acties: individuele acties mogen worden verwijderd als ze niet relevant zijn, maar relevante acties blijven staan.
- Geef alleen suggesties waar echt verbetering nodig is.
- Bij lege velden: geef een suggestie voor wat er zou moeten staan.
- Wees concreet en praktisch.
- De nieuwe_tekst bevat de VOLLEDIGE tekst inclusief wat er al stond."""


class SuggestieGenerator:
    """
    Genereert concrete tekstsuggesties voor schoolinvullingen.

    Deze klasse is onafhankelijk van de hoofdassistent en kan worden
    verwijderd zonder de rest van de applicatie te beïnvloeden.
    """

    def __init__(self, model: str = None, database_path: str = None):
        self.model = model or settings.MODEL_NAME
        self.database_path = database_path or str(settings.DATABASE_PATH)
        self.database = load_database(self.database_path)

    def genereer_suggesties(
        self,
        eis_id: str,
        school_invulling: SchoolInvulling,
    ) -> SuggestieResultaat:
        """
        Genereer suggesties voor de schoolinvulling.

        Returns:
            SuggestieResultaat met per veld een VeldSuggestie
        """
        # Bouw de prompt
        eis = load_deugdelijkheidseis(self.database, eis_id)

        context = f"""DEUGDELIJKHEIDSEIS: {eis['id']} - {eis['titel']}

Eisomschrijving:
{eis['eisomschrijving']}

Focuspunten:
{eis['focuspunten']}

---

HUIDIGE INVULLING VAN DE SCHOOL:

Ambitie:
{school_invulling.ambitie or '[niet ingevuld]'}

Beoogd resultaat:
{school_invulling.beoogd_resultaat or '[niet ingevuld]'}

Concrete acties:
{school_invulling.concrete_acties or '[niet ingevuld]'}

Wijze van meten:
{school_invulling.wijze_van_meten or '[niet ingevuld]'}"""

        system_prompt = f"{SUGGESTIE_PROMPT}\n\n{context}"

        # Genereer response
        try:
            response_text = self._generate(
                system_prompt,
                "Geef je suggesties als JSON.",
            )

            # Parse JSON
            return self._parse_response(response_text, school_invulling)

        except Exception as e:
            return SuggestieResultaat(
                success=False,
                suggesties={},
                error=f"Fout bij genereren: {str(e)}"
            )

    def _generate(
        self,
        system_prompt: str,
        user_message: str,
    ) -> str:
        """Genereer response via Ollama met JSON mode."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        options = {
            "temperature": 0.3,  # Lager voor meer consistente JSON
            "num_predict": settings.MAX_GENERATE_TOKENS,
            "num_ctx": settings.NUM_CTX,
        }

        # Gebruik Ollama's native JSON mode voor gegarandeerde valide JSON
        result = ollama.chat(
            model=self.model,
            messages=messages,
            options=options,
            format="json",  # Dit dwingt het model om valide JSON te produceren
        )
        return result["message"]["content"]

    def _parse_response(
        self, response: str, school_invulling: SchoolInvulling
    ) -> SuggestieResultaat:
        """Parse de JSON response naar SuggestieResultaat."""

        # Stap 1: Strip markdown code blocks als aanwezig
        cleaned = response.strip()
        
        # Verwijder ```json of ``` blocks
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned)
        if code_block_match:
            cleaned = code_block_match.group(1).strip()
        
        # Stap 2: Probeer JSON te extraheren
        # Zoek naar de buitenste { } structuur
        json_match = re.search(r'\{[\s\S]*\}', cleaned)
        if not json_match:
            return SuggestieResultaat(
                success=False,
                suggesties={},
                error="Geen valid JSON in response",
                raw_response=response
            )

        json_str = json_match.group()
        
        # Stap 3: Fix veelvoorkomende JSON problemen van LLMs
        # Soms schrijft het model "true" of "false" als strings
        json_str = re.sub(r':\s*"true"', ': true', json_str)
        json_str = re.sub(r':\s*"false"', ': false', json_str)
        # Fix trailing commas (niet valid in JSON)
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return SuggestieResultaat(
                success=False,
                suggesties={},
                error=f"JSON parse error: {str(e)}",
                raw_response=response
            )

        # Map velden naar huidige tekst
        huidige_teksten = {
            "ambitie": school_invulling.ambitie,
            "beoogd_resultaat": school_invulling.beoogd_resultaat,
            "concrete_acties": school_invulling.concrete_acties,
            "wijze_van_meten": school_invulling.wijze_van_meten,
        }

        # Bouw suggesties
        suggesties = {}
        for veld, huidige_tekst in huidige_teksten.items():
            veld_data = data.get(veld, {})

            suggesties[veld] = VeldSuggestie(
                veld=veld,
                heeft_suggestie=veld_data.get("heeft_suggestie", False),
                huidige_tekst=huidige_tekst or "",
                nieuwe_tekst=veld_data.get("nieuwe_tekst"),
                toelichting=veld_data.get("toelichting"),
            )

        return SuggestieResultaat(
            success=True,
            suggesties=suggesties,
            raw_response=response
        )
