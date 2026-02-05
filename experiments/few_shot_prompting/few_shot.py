"""Few-shot prompting module voor OnSpectAI.

Dit module bouwt conversation-based few-shot examples op basis van
de voorbeeld_invullingen.json. Het idee is dat de AI leert van
voorbeeldconversaties in plaats van voorbeelden in de system prompt.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Pad naar de voorbeeldinvullingen
VOORBEELDEN_PATH = Path(__file__).parent.parent / "data" / "voorbeeld_invullingen.json"

# Cache voor de voorbeelden
_voorbeelden_cache: Optional[Dict] = None


def load_voorbeeld_invullingen() -> Dict:
    """Laad de voorbeeld invullingen uit JSON."""
    global _voorbeelden_cache

    if _voorbeelden_cache is not None:
        return _voorbeelden_cache

    try:
        with open(VOORBEELDEN_PATH, encoding="utf-8") as f:
            _voorbeelden_cache = json.load(f)
        return _voorbeelden_cache
    except FileNotFoundError:
        logger.warning("voorbeeld_invullingen.json niet gevonden: %s", VOORBEELDEN_PATH)
        return {"invullingen": {}}
    except json.JSONDecodeError as e:
        logger.error("Fout bij laden voorbeeld_invullingen.json: %s", e)
        return {"invullingen": {}}


def get_voorbeeld_voor_eis(eis_id: str) -> Optional[Dict]:
    """Haal voorbeelden op voor een specifieke eis."""
    data = load_voorbeeld_invullingen()
    return data.get("invullingen", {}).get(eis_id)


# =============================================================================
# EIS-SPECIFIEKE FEW-SHOT RESPONSES
# =============================================================================
# Deze responses bevatten eis-specifieke kennis en terminologie.
# Ze leren het model niet alleen het FORMAT, maar ook de INHOUD.

EIS_SPECIFIEKE_RESPONSES = {
    "OP 2.1": {
        "zwak": """**Oordeel: Onvoldoende**

**Sterke punten:**
- Er is een begin gemaakt met het benoemen van informatieverzameling

**Verbeterpunten:**
- De ambitie is te vaag - "leerlingen in de gaten houden" is niet concreet. Beschrijf specifiek dat jullie systematisch informatie verzamelen over zowel cognitieve als sociaal-emotionele ontwikkeling.
- Er wordt geen melding gemaakt van informatieverzameling bij binnenkomst. De warme overdracht vanuit het primair onderwijs ontbreekt volledig (onderwijskundig rapport, intakegesprekken).
- Alleen "cijfers invoeren" is onvoldoende. Welk leerlingvolgsysteem gebruiken jullie? Welke toetsen (DIA, Cito VAS)? Hoe vaak wordt er getoetst?
- De sociaal-emotionele ontwikkeling wordt niet genoemd. Hoe volgen jullie het welbevinden van leerlingen? Wat is de rol van de mentor hierin?
- De wijze van meten is reactief ("we merken het als er iets aan de hand is"). Dit voldoet niet - informatieverzameling moet systematisch en proactief zijn.
- Er mist een evaluatie van het verzamelproces zelf: hoe weten jullie of de leerlingdossiers compleet zijn?

**Vervolgstappen:**
- Beschrijf de warme overdracht vanuit PO: onderwijskundig rapport, intakegesprek, eventueel nulmeting
- Benoem het leerlingvolgsysteem (bijv. Magister, SOMtoday) en hoe dit wordt gebruikt
- Voeg specifieke toetsen toe: DIA-toetsen, Cito VAS, methodetoetsen
- Beschrijf hoe de mentor systematisch de sociaal-emotionele ontwikkeling volgt (gesprekken, observaties, SAQI of vergelijkbaar instrument)
- Voeg een evaluatiemethode toe: hoe controleren jullie of dossiers compleet zijn?""",

        "goed": """**Oordeel: Goed**

**Sterke punten:**
- Heldere ambitie die specifiek benoemt dat jullie systematisch informatie verzamelen over zowel cognitieve als sociaal-emotionele ontwikkeling
- De informatieverzameling bij binnenkomst is goed beschreven: warme overdracht vanuit PO, onderwijskundig rapport, intakegesprek en nulmeting
- Concrete instrumenten worden genoemd: DIA-toetsen, Magister als leerlingvolgsysteem, SAQI voor sociaal-emotionele ontwikkeling
- De rol van de mentor is duidelijk: minimaal drie gesprekken per jaar, vastlegging in het systeem
- Er is een systematische evaluatie: steekproefsgewijze controle van dossiers, evaluatie van de warme overdracht
- De focus ligt terecht op VERZAMELEN van informatie, niet op wat er mee gedaan wordt (dat hoort bij OP 2.2)

**Verbeterpunten:**
- De invulling is sterk en compleet
- Overweeg om de frequentie van toetsing nog explicieter te maken per leerjaar
- Het zou nog sterker zijn om te beschrijven hoe jullie omgaan met leerlingen die tussentijds instromen

**Vervolgstappen:**
- Behoud deze systematische aanpak
- Evalueer jaarlijks of de gebruikte instrumenten nog actueel en effectief zijn
- Zorg dat nieuwe collega's worden ingewerkt in het gebruik van het leerlingvolgsysteem"""
    }
}


def format_school_invulling_text(invulling: Dict) -> str:
    """Formatteer een voorbeeld invulling als tekst."""
    return f"""Ambitie:
{invulling.get('ambitie', '(niet ingevuld)')}

Beoogd resultaat:
{invulling.get('beoogd_resultaat', '(niet ingevuld)')}

Concrete acties:
{invulling.get('concrete_acties', '(niet ingevuld)')}

Wijze van meten:
{invulling.get('wijze_van_meten', '(niet ingevuld)')}"""


def generate_example_feedback_response(niveau: str, invulling: Dict, eis_id: str = None) -> str:
    """
    Genereer een voorbeeld feedback response gebaseerd op het niveau.

    Dit zijn handgeschreven voorbeelden die laten zien hoe de AI
    zou moeten reageren op verschillende kwaliteitsniveaus.

    Args:
        niveau: "zwak", "gemiddeld", of "goed"
        invulling: De invulling dict (voor context)
        eis_id: Optioneel - als gegeven, gebruik eis-specifieke responses
    """
    # Check of er eis-specifieke responses zijn
    if eis_id and eis_id in EIS_SPECIFIEKE_RESPONSES:
        eis_responses = EIS_SPECIFIEKE_RESPONSES[eis_id]
        if niveau in eis_responses:
            return eis_responses[niveau]

    # Fallback naar generieke responses
    if niveau == "zwak":
        return f"""**Oordeel: Onvoldoende**

**Sterke punten:**
- Er is een begin gemaakt met het beschrijven van de aanpak

**Verbeterpunten:**
- De ambitie is te vaag en niet concreet genoeg - beschrijf specifieker wat jullie willen bereiken
- Er zijn geen meetbare doelen geformuleerd in het beoogde resultaat
- De concrete acties zijn te algemeen - beschrijf specifiek welke stappen jullie nemen
- De wijze van meten ontbreekt grotendeels of is onduidelijk - hoe weten jullie of het werkt?
- De PDCA-cyclus is niet compleet: er mist een duidelijke koppeling tussen acties en evaluatie

**Vervolgstappen:**
- Formuleer een concrete, meetbare ambitie met streefpercentages of aantallen
- Beschrijf per actie: wie, wat, wanneer en hoe vaak
- Voeg een systematische evaluatiemethode toe (bijv. jaarlijkse enquête, registratiesysteem)
- Zorg dat alle vier PDCA-onderdelen volledig zijn ingevuld"""

    elif niveau == "gemiddeld":
        return f"""**Oordeel: Voldoende**

**Sterke punten:**
- Er is een duidelijke ambitie geformuleerd
- Er zijn enkele concrete acties benoemd
- Er is nagedacht over het meten van resultaten

**Verbeterpunten:**
- De doelen in het beoogde resultaat mogen concreter en meetbaarder (met percentages of aantallen)
- De concrete acties kunnen specifieker - wie is verantwoordelijk en hoe vaak gebeurt dit?
- De wijze van meten kan systematischer - beschrijf wanneer en hoe jullie evalueren

**Vervolgstappen:**
- Voeg meetbare streefcijfers toe aan het beoogde resultaat
- Maak de acties SMART: specifiek, meetbaar, met tijdspad
- Beschrijf een concrete evaluatiecyclus: welk instrument, hoe vaak, wie analyseert"""

    else:  # goed
        return f"""**Oordeel: Goed**

**Sterke punten:**
- Heldere en concrete ambitie die aansluit bij de eis
- Meetbare doelen met duidelijke streefcijfers
- Uitgebreide en specifieke concrete acties met verantwoordelijken
- Systematische wijze van meten met concrete instrumenten en evaluatiemomenten
- De PDCA-cyclus is volledig: er is een duidelijke koppeling tussen plan, uitvoering, meting en bijsturing

**Verbeterpunten:**
- De invulling is sterk; kleine verfijningen zijn mogelijk maar niet noodzakelijk
- Overweeg om de frequentie van evaluatie nog explicieter te maken

**Vervolgstappen:**
- Behoud deze systematische aanpak
- Zorg dat de evaluatieresultaten ook daadwerkelijk leiden tot bijstelling van het beleid
- Deel deze goede praktijk met collega's voor andere eisen"""


def build_few_shot_messages(
    eis_id: str,
    eis_info: Dict,
    school_invulling_text: str,
    vraag: str,
    vraag_type: str,
    system_prompt: str,
) -> List[Dict]:
    """
    Bouw de messages array met few-shot voorbeelden.

    Structuur:
    1. System message (zonder de "voorbeelden" sectie)
    2. Voorbeeld user message (zwakke invulling)
    3. Voorbeeld assistant message (kritische feedback)
    4. Voorbeeld user message (goede invulling)
    5. Voorbeeld assistant message (positieve feedback)
    6. Echte user message

    Args:
        eis_id: ID van de deugdelijkheidseis
        eis_info: Informatie over de eis (titel, uitleg, etc.)
        school_invulling_text: De invulling van de school als tekst
        vraag: De vraag van de gebruiker
        vraag_type: Type vraag (feedback/uitleg/suggestie/algemeen)
        system_prompt: De basis system prompt

    Returns:
        List van messages voor de Ollama API
    """
    messages = []

    # 1. System message
    messages.append({
        "role": "system",
        "content": system_prompt
    })

    # 2. Few-shot voorbeelden (alleen voor feedback, daar is het meest effectief)
    if vraag_type == "feedback":
        voorbeelden = get_voorbeeld_voor_eis(eis_id)

        if voorbeelden:
            # Voorbeeld 1: Zwakke invulling met kritische feedback
            zwak = voorbeelden.get("zwak", {})
            if zwak:
                zwak_invulling = format_school_invulling_text(zwak)
                zwak_response = generate_example_feedback_response("zwak", zwak, eis_id)

                messages.append({
                    "role": "user",
                    "content": f"Geef feedback op deze invulling voor {eis_id}:\n\n{zwak_invulling}"
                })
                messages.append({
                    "role": "assistant",
                    "content": zwak_response
                })

            # Voorbeeld 2: Goede invulling met positieve feedback
            goed = voorbeelden.get("goed", {})
            if goed:
                goed_invulling = format_school_invulling_text(goed)
                goed_response = generate_example_feedback_response("goed", goed, eis_id)

                messages.append({
                    "role": "user",
                    "content": f"Geef feedback op deze invulling voor {eis_id}:\n\n{goed_invulling}"
                })
                messages.append({
                    "role": "assistant",
                    "content": goed_response
                })

    # 3. De echte vraag
    user_content = f"{vraag}\n\nInvulling van de school:\n\n{school_invulling_text}"
    messages.append({
        "role": "user",
        "content": user_content
    })

    return messages


def build_few_shot_system_prompt(
    base_system_prompt: str,
    task_instruction: str,
    eis_info: Dict,
) -> str:
    """
    Bouw een slankere system prompt voor few-shot (zonder voorbeelden sectie).

    De "voorbeelden" komen nu als conversatie-turns, dus we laten die
    sectie weg uit de system prompt om duplicatie te voorkomen.
    """
    return f"""{base_system_prompt}

---
HUIDIGE TAAK: {task_instruction}
---

DEUGDELIJKHEIDSEIS: {eis_info['id']} - {eis_info['titel']}
Standaard: {eis_info['standaard']}

Eisomschrijving:
{eis_info['eisomschrijving']}

Uitleg:
{eis_info['uitleg']}

Focuspunten:
{eis_info['focuspunten']}

Tips:
{eis_info['tips']}"""

# NOTE: "Voorbeelden" sectie is weggelaten - deze komen als conversation turns
