"""
streamlit_app.py — Botrunner Playground  (main entry-point)
============================================================

This file is intentionally THIN.  It owns:
  1. Page configuration & CSS injection
  2. Session-state initialisation
  3. Auth gate
  4. The 3-column layout orchestration
  5. The post-layout message-processing hook

All heavy logic lives in the sibling modules:
  config.py      – constants & paths
  styles.css     – full OpenAI-style dark theme
  auth.py        – login / register / topbar
  persona.py     – default persona + config dialog
  threads.py     – left sidebar thread panel
  chat.py        – centre chat panel + send loop
  bot_state.py   – right inspector panel
  qa_panel.py    – full-width QA testing panel
  database.py    – SQLite persistence (pre-existing)

Run:
  streamlit run streamlit_ui/streamlit_app.py
"""

import warnings, logging, sys
from pathlib import Path

warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)

import streamlit as st

# ---------------------------------------------------------------------------
# Path bootstrap — make sibling modules importable
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(_THIS_DIR))

# ---------------------------------------------------------------------------
# Import project modules (order matters: config first, then DB, then others)
# ---------------------------------------------------------------------------
from config import STYLES_CSS
from database import (
    init_db,
    get_global_persona,
    get_user_persona,
)
from persona import get_default_persona

# ---------------------------------------------------------------------------
# Streamlit page config (must come before ANY st.* rendering call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Botrunner Playground",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Inject CSS
# ---------------------------------------------------------------------------
if STYLES_CSS.exists():
    _css_text = STYLES_CSS.read_text()
else:
    _css_text = ""  # graceful fallback

st.markdown(f"<style>{_css_text}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session-state initialisation
# ---------------------------------------------------------------------------
_SESSION_DEFAULTS = {
    # Auth
    "auth_user_id": None,
    "auth_user_name": None,
    # Thread / chat
    "current_thread_id": None,
    "current_bot_state": None,
    "messages": [],
    "processing": False,
    "chat_history": [],
    "pending_message": None,
    # QA panel
    "qa_selected_question": None,
    "qa_expected_response": None,
    "qa_last_llm_response": None,
    "qa_show_comparison": False,
    # Persona
    "custom_persona": None,
}

for _k, _v in _SESSION_DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Fallback persona load (global store) – will be overridden per-user after login
if st.session_state.custom_persona is None:
    st.session_state.custom_persona = get_global_persona()

# ---------------------------------------------------------------------------
# DB init (idempotent – creates tables if missing)
# ---------------------------------------------------------------------------
init_db()

# ---------------------------------------------------------------------------
# AUTH GATE  ─  everything below is guarded
# ---------------------------------------------------------------------------
if not st.session_state.get("auth_user_id"):
    from auth import render_auth_screen

    render_auth_screen()
    st.stop()  # ← hard stop; nothing below executes for unauthenticated users

# Ensure per-user persona is loaded after login
if st.session_state.custom_persona is None:
    st.session_state.custom_persona = (
        get_user_persona(st.session_state.auth_user_id) or get_default_persona()
    )

# ---------------------------------------------------------------------------
# TOP BAR
# ---------------------------------------------------------------------------
from auth import render_topbar

render_topbar()

# ---------------------------------------------------------------------------
# 3-COLUMN LAYOUT
# ---------------------------------------------------------------------------
# Proportions: Threads (1) | Chat (2) | Inspector (1.5)
# ---------------------------------------------------------------------------
col_threads, col_chat, col_state = st.columns([1, 2, 1.5])

# ── Left: Threads ─────────────────────────────────────────────────────────
with col_threads:
    from threads import render_threads_panel

    render_threads_panel()

# ── Centre: Chat ──────────────────────────────────────────────────────────
with col_chat:
    from chat import render_chat_panel

    render_chat_panel()

# ── Right: Inspector ──────────────────────────────────────────────────────
with col_state:
    from bot_state import render_inspector_panel

    render_inspector_panel()

# ---------------------------------------------------------------------------
# POST-LAYOUT: message processing hook
# Must run AFTER columns are rendered so the pending_message flag set by
# chat_input or qa_panel is visible.
# ---------------------------------------------------------------------------
from chat import process_pending_message

process_pending_message()

# ---------------------------------------------------------------------------
# FULL-WIDTH: QA Testing Panel
# ---------------------------------------------------------------------------
from qa_panel import render_qa_panel

render_qa_panel()
