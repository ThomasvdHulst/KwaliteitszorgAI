"""Database utilities voor de OnSpectAI API."""

import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EisNotFoundError(Exception):
    """Exception wanneer een deugdelijkheidseis niet gevonden wordt."""

    def __init__(self, eis_id: str):
        self.eis_id = eis_id
        super().__init__(f"Deugdelijkheidseis '{eis_id}' niet gevonden in database.")


class DatabaseError(Exception):
    """Exception voor database laad fouten."""

    pass


def load_database(database_path: str) -> Dict:
    """
    Laadt de deugdelijkheidseisen database uit JSON bestand.

    Args:
        database_path: Pad naar het JSON bestand

    Returns:
        Dictionary met de database inhoud

    Raises:
        DatabaseError: Als het bestand niet geladen kan worden
    """
    try:
        with open(database_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Database bestand '%s' niet gevonden.", database_path)
        raise DatabaseError(f"Database bestand niet gevonden: {database_path}")
    except json.JSONDecodeError as e:
        logger.error("Kan database bestand niet laden: %s", e)
        raise DatabaseError(f"Database bestand is geen geldige JSON: {e}")


def load_deugdelijkheidseis(
    database: Dict, deugdelijkheidseis_id: str, raise_on_not_found: bool = False
) -> Optional[Dict]:
    """
    Laadt een specifieke deugdelijkheidseis uit de database.

    Args:
        database: De geladen database dictionary
        deugdelijkheidseis_id: ID van de eis (bijv. 'VS 1.5')
        raise_on_not_found: Als True, raise EisNotFoundError. Als False, return None.

    Returns:
        Dictionary met eis data, of None als niet gevonden (en raise_on_not_found=False)

    Raises:
        EisNotFoundError: Als de eis niet gevonden wordt en raise_on_not_found=True
    """
    eisen = database.get("deugdelijkheidseisen", {})

    if deugdelijkheidseis_id in eisen:
        eis = eisen[deugdelijkheidseis_id].copy()
        # Zorg dat id altijd aanwezig is
        eis["id"] = deugdelijkheidseis_id
        return eis

    logger.warning(
        "Deugdelijkheidseis '%s' niet gevonden in database.",
        deugdelijkheidseis_id
    )

    if raise_on_not_found:
        raise EisNotFoundError(deugdelijkheidseis_id)

    return None


def get_all_eis_ids(database: Dict) -> list[str]:
    """
    Haal alle eis IDs op uit de database.

    Args:
        database: De geladen database dictionary

    Returns:
        Gesorteerde lijst met alle eis IDs
    """
    eisen = database.get("deugdelijkheidseisen", {})
    return sorted(eisen.keys())
