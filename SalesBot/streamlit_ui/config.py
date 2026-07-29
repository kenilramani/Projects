"""
config.py — Centralized configuration for Botrunner Playground.

All environment variables, paths, and shared constants live here.
Every other module imports from this file instead of duplicating settings.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# Directory that contains THIS file (streamlit_ui/)
STREAMLIT_UI_DIR: Path = Path(__file__).parent

# Sub-paths
DATA_DIR: Path = STREAMLIT_UI_DIR / "data"
QA_PAIRS_CSV: Path = DATA_DIR / "QA_PAIRS.csv"
THREADS_CSV: Path = DATA_DIR / "QA_THREADS.csv"  # reserved / not yet used
DB_PATH: Path = STREAMLIT_UI_DIR / "chat_threads.db"
STYLES_CSS: Path = STREAMLIT_UI_DIR / "styles.css"

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
CHAT_ENDPOINT: str = f"{API_BASE_URL}/chat_ui"  
GENERATE_PROBING_ENDPOINT: str = f"{API_BASE_URL}/generate_probing_questions"
AUTOFILL_PERSONA_ENDPOINT: str = f"{API_BASE_URL}/autofill_persona"
GENERATE_INSTRUCTIONS_ENDPOINT: str = f"{API_BASE_URL}/generate_instructions"
GENERATE_TEMPLATES_ENDPOINT: str = f"{API_BASE_URL}/generate_templates"
GENERATE_EXECUTIVE_SUMMARY_ENDPOINT: str = f"{API_BASE_URL}/generate_executive_summary"
API_AUTOFILL_TIMEOUT: int = 300  # Crawling can take time

# ---------------------------------------------------------------------------
# UI constants
# ---------------------------------------------------------------------------
THREAD_TITLE_MAX_LEN: int = 40
THREAD_LABEL_MAX_LEN: int = 22
CHAT_CONTAINER_HEIGHT: int = 480
STATE_CONTAINER_HEIGHT: int = 700
QA_SCROLL_CONTAINER_HEIGHT: int = 570
API_HEALTH_TIMEOUT: int = 2
API_CHAT_TIMEOUT: int = 120
API_GENERATE_TIMEOUT: int = 60

# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", 15))
