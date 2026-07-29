"""
chat.py — Centre-column chat interface.

Responsibilities:
  • Render scrollable message list
  • Show pending-message "Thinking…" indicator
  • Chat input pill
  • Orchestrate the send → API → store → rerun loop
"""

import streamlit as st
import requests
import math
from config import (
    CHAT_ENDPOINT,
    THREAD_TITLE_MAX_LEN,
    CHAT_CONTAINER_HEIGHT,
    API_CHAT_TIMEOUT,
)
from database import add_message, update_thread_title
from persona import get_default_persona
from database import get_user_persona


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------
def render_chat_panel():
    """
    Render the full chat column.  Call inside the centre Streamlit column.
    """
    st.markdown("##### 💬 Chat")

    if not st.session_state.current_thread_id:
        st.info("👈 Select a thread or start a new chat to begin.")
        return

    # ── Scrollable message area ──────────────────────────────────────
    chat_box = st.container(height=CHAT_CONTAINER_HEIGHT)
    with chat_box:
        if not st.session_state.messages and not st.session_state.pending_message:
            st.caption("Start the conversation by typing a message below.")

        # Render persisted messages
        for msg in st.session_state.messages:
            avatar = "👤" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.write(msg["content"])

        # Pending message + thinking indicator
        if st.session_state.pending_message:
            with st.chat_message("user", avatar="👤"):
                st.write(st.session_state.pending_message)
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown("⏳ *Thinking…*")

    # ── Chat input pill ──────────────────────────────────────────────
    user_input = st.chat_input(
        "Type your message…",
        disabled=st.session_state.processing,
    )

    if user_input and not st.session_state.processing:
        st.session_state.pending_message = user_input
        st.session_state.processing = True
        st.rerun()


# ---------------------------------------------------------------------------
# Processing loop  (called from streamlit_app.py after columns are rendered)
# ---------------------------------------------------------------------------
def process_pending_message():
    """
    If a pending message exists and processing flag is set, execute the
    full send → API → save → rerun cycle.  Should be called unconditionally
    at the bottom of the main app after all columns are laid out.
    """
    if not (st.session_state.pending_message and st.session_state.processing):
        return

    user_msg = st.session_state.pending_message
    thread_id = st.session_state.current_thread_id

    # 1. Persist user message
    add_message(thread_id, "user", user_msg)
    st.session_state.messages.append({"role": "user", "content": user_msg})

    # 2. Auto-title on first message
    if len(st.session_state.messages) == 1:
        update_thread_title(thread_id, _generate_title(user_msg))

    # 3. Call backend
    api_response = _send_to_api(user_msg, thread_id, st.session_state.chat_history)

    # 4. Extract bot text
    if "error" in api_response:
        bot_text = f"❌ {api_response['error']}"
    else:
        bot_text = api_response.get("response", "Sorry, I couldn't respond.")

    # 5. Persist assistant message (with full state blob)
    add_message(thread_id, "assistant", bot_text, api_response)
    st.session_state.messages.append({"role": "assistant", "content": bot_text})

    # 6. Update rolling history - prefer backend's truncated/managed history
    if api_response.get("user_context", {}).get("chat_history"):
        st.session_state.chat_history = api_response["user_context"]["chat_history"]
    else:
        st.session_state.chat_history.append({"role": "user", "content": user_msg})
        st.session_state.chat_history.append({"role": "assistant", "content": bot_text})

    # 7. Store full BotState for inspector
    st.session_state.current_bot_state = api_response

    # 8. Clear pending & rerun
    st.session_state.pending_message = None
    st.session_state.processing = False
    st.rerun()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------
def _generate_title(first_message: str) -> str:
    """Short title from the first user message."""
    t = first_message[:THREAD_TITLE_MAX_LEN].strip()
    return (t + "…") if len(first_message) > THREAD_TITLE_MAX_LEN else t or "New Chat"


def _send_to_api(user_message: str, thread_id: str, chat_history: list) -> dict:
    """
    POST to /chat_ui with the full BotRequest payload.
    Returns the parsed JSON response or an error dict.
    """
    persona = (
        st.session_state.custom_persona
        or get_user_persona(st.session_state.auth_user_id)
        or get_default_persona()
    )

    # Get previous user context from last API response (or empty dict for first message)
    prev_uc = (
        st.session_state.current_bot_state.get("user_context", {})
        if st.session_state.current_bot_state
        else {}
    )

    payload = {
        "bot_persona": persona,
        "user_context": {
            "user_id": thread_id,
            "user_query": user_message,
            "tenant_id": st.session_state.auth_user_id,
            "chat_summary": "",
            "executive_summary": "",
            # Valid optimization: Don't send full history back. Backend has it in DB.
            # Sending empty list prevents overwriting backend state (is_meaningful check).
            "chat_history": [],
            "to_summarise": False,
            "retrieved_docs": [],
            "contact_details": None,
            "follow_trigger": False,
            "ask_new_date": False,
            "previous_time": prev_uc.get("previous_time"),
            "previous_date": prev_uc.get("previous_date"),
            "timezone": prev_uc.get("timezone"),
            "region_code": prev_uc.get("region_code"),
            "collected_fields": prev_uc.get("collected_fields") or {},
            "all_info_collected": prev_uc.get("all_info_collected", False),
            "booking_confirmed": prev_uc.get("booking_confirmed", False),
            "booking_type": prev_uc.get("booking_type"),
            "new_booking": prev_uc.get("new_booking", False),
        },
    }

    # Sanitize NaN/Inf in persona (Streamlit data_editor can inject NaN for empty numbers)
    payload = _sanitize_nan(payload)

    try:
        resp = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=API_CHAT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        # Ensure persona is echoed for the inspector even if backend omits it
        if isinstance(data, dict) and not data.get("bot_persona"):
            data["bot_persona"] = persona
        return data

    except requests.exceptions.ConnectionError:
        from config import API_BASE_URL

        return {
            "error": f"Cannot connect to API at {API_BASE_URL}. Start FastAPI first."
        }
    except requests.exceptions.Timeout:
        return {"error": "Request timed out (120 s)."}
    except requests.exceptions.RequestException as exc:
        return {"error": str(exc)}


def _sanitize_nan(obj):
    """Recursively replace NaN/Inf floats with None."""
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitize_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_nan(i) for i in obj]
    return obj
