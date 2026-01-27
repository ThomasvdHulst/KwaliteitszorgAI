"""
Centrale configuratie voor OnSpect AI.

Instellingen kunnen worden overschreven via environment variables.
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "deugdelijkheidseisen_db.json"

# Model
MODEL_NAME = os.getenv("ONSPECT_MODEL", "gemma3:27b")

# Context - verhoogd voor chat-continuatie
MAX_CONTEXT_TOKENS = int(os.getenv("ONSPECT_MAX_TOKENS", "16000"))
NUM_CTX = 32768  # Context window van het model

# Generatie
TEMPERATURE_DEFAULT = 0.6
MAX_GENERATE_TOKENS = 4000
TOP_P = 0.9
REPEAT_PENALTY = 1.1

# Chat
MAX_CONVERSATION_HISTORY = 10  # Aantal bericht-paren (user + assistant)
