"""
Persistente opslag voor school-invullingen.

Slaat invullingen op als JSON in data/school_invullingen.json.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import settings


STORAGE_PATH = settings.DATA_DIR / "school_invullingen.json"


def _load_file() -> dict:
    """Laad het JSON-bestand, of return leeg template als het niet bestaat."""
    if not STORAGE_PATH.exists():
        return {"laatst_bijgewerkt": None, "invullingen": {}}
    with open(STORAGE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_file(data: dict):
    """Sla data op naar het JSON-bestand."""
    STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STORAGE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_all_invullingen() -> dict:
    """Laad alle invullingen. Return leeg template als bestand niet bestaat."""
    return _load_file()


def load_invulling(eis_id: str) -> Optional[dict]:
    """
    Laad de invulling voor één eis.

    Returns:
        Dict met ambitie, beoogd_resultaat, concrete_acties, wijze_van_meten
        of None als niet opgeslagen.
    """
    data = _load_file()
    return data["invullingen"].get(eis_id)


def save_invulling(
    eis_id: str,
    ambitie: str,
    beoogd_resultaat: str,
    concrete_acties: str,
    wijze_van_meten: str,
):
    """Sla een invulling op met timestamp."""
    data = _load_file()
    now = datetime.now().isoformat(timespec="seconds")
    data["invullingen"][eis_id] = {
        "ambitie": ambitie,
        "beoogd_resultaat": beoogd_resultaat,
        "concrete_acties": concrete_acties,
        "wijze_van_meten": wijze_van_meten,
        "laatst_opgeslagen": now,
    }
    data["laatst_bijgewerkt"] = now
    _save_file(data)


def get_invulling_status(eis_id: str) -> str:
    """Return 'opgeslagen' of 'niet_opgeslagen'."""
    data = _load_file()
    if eis_id in data["invullingen"]:
        return "opgeslagen"
    return "niet_opgeslagen"
