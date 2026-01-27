"""Database loading utilities voor Kwaliteitszorg AI."""

import json
from typing import Dict


def load_database(database_path: str) -> Dict:
    """Laadt de deugdelijkheidseisen database uit JSON bestand."""
    try:
        with open(database_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"WAARSCHUWING: Database bestand '{database_path}' niet gevonden.")
        print("Maak een bestand 'deugdelijkheidseisen_db.json' aan met de deugdelijkheidseisen.")
        return {"deugdelijkheidseisen": {}}
    except json.JSONDecodeError as e:
        print(f"FOUT: Kan database bestand niet laden: {e}")
        return {"deugdelijkheidseisen": {}}


def load_deugdelijkheidseis(database: Dict, deugdelijkheidseis_id: str) -> Dict:
    """Laadt een specifieke deugdelijkheidseis uit de database."""
    eisen = database.get("deugdelijkheidseisen", {})

    if deugdelijkheidseis_id in eisen:
        return eisen[deugdelijkheidseis_id]
    else:
        print(
            f"WAARSCHUWING: Deugdelijkheidseis '{deugdelijkheidseis_id}' "
            "niet gevonden in database."
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
