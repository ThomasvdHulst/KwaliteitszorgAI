"""Database loading utilities voor Kwaliteitszorg AI."""

import json
from typing import Dict

from config.settings import logger


def load_database(database_path: str) -> Dict:
    """Laadt de deugdelijkheidseisen database uit JSON bestand."""
    try:
        with open(database_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(
            "Database bestand '%s' niet gevonden. "
            "Maak een bestand 'deugdelijkheidseisen_db.json' aan.",
            database_path
        )
        return {"deugdelijkheidseisen": {}}
    except json.JSONDecodeError as e:
        logger.error("Kan database bestand niet laden: %s", e)
        return {"deugdelijkheidseisen": {}}


def load_deugdelijkheidseis(database: Dict, deugdelijkheidseis_id: str) -> Dict:
    """Laadt een specifieke deugdelijkheidseis uit de database."""
    eisen = database.get("deugdelijkheidseisen", {})

    if deugdelijkheidseis_id in eisen:
        return eisen[deugdelijkheidseis_id]
    else:
        logger.warning(
            "Deugdelijkheidseis '%s' niet gevonden in database.",
            deugdelijkheidseis_id
        )
        return {
            "id": deugdelijkheidseis_id,
            "standaard": "[Niet gevonden in database]",
            "titel": "[Niet gevonden in database]",
            "eisomschrijving": "[Deze deugdelijkheidseis is nog niet toegevoegd aan de database]",
            "uitleg": "",
            "focuspunten": "",
            "tips": "",
            "voorbeelden": "",
        }
