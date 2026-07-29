"""
threads.py — Left-column thread management panel.

Responsibilities:
  • API online/offline badge
  • "New Chat" button
  • Scrollable thread list with click-to-switch, checkbox multi-select, delete
"""

import streamlit as st
import requests
from config import API_BASE_URL, API_HEALTH_TIMEOUT, MAX_HISTORY
from database import (
    create_thread,
    get_all_threads,
    delete_thread,
    get_thread_messages,
    get_last_bot_state,
)


def render_threads_panel():
    """
    Render the entire left-column thread panel.
    Must be called inside a Streamlit column context.
    """
    # ── Branding ─────────────────────────────────────────────────────
    st.markdown(
        '<p style="font-size:1.15rem; font-weight:700; color:#f0f2f5; margin:0 0 0.15rem;">'
        "🤖 Botrunner</p>",
        unsafe_allow_html=True,
    )

    # ── API health badge ─────────────────────────────────────────────
    _render_api_badge()
    st.divider()

    # ── New Chat ─────────────────────────────────────────────────────
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        _create_new_thread()

    st.divider()

    # ── Thread list ──────────────────────────────────────────────────
    threads = get_all_threads(st.session_state.auth_user_id)

    if not threads:
        st.caption("No conversations yet. Start a new chat!")
        return

    # Gather which threads are checked
    selected_ids = [
        t["id"] for t in threads if st.session_state.get(f"sel_{t['id']}", False)
    ]

    # Bulk-delete bar (only visible when ≥1 checkbox is ticked)
    if selected_ids:
        if st.button(
            f"🗑️ Delete Selected ({len(selected_ids)})",
            use_container_width=True,
            type="secondary",
        ):
            _bulk_delete(selected_ids)
        st.divider()

    # Individual thread rows
    for thread in threads:
        _render_thread_row(thread)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------
def _render_api_badge():
    """Quick GET to /docs to determine backend liveness."""
    try:
        requests.get(f"{API_BASE_URL}/docs", timeout=API_HEALTH_TIMEOUT)
        st.markdown(
            '<span class="badge badge-green">● API Online</span>',
            unsafe_allow_html=True,
        )
    except Exception:
        st.markdown(
            '<span class="badge badge-red">● API Offline</span>',
            unsafe_allow_html=True,
        )


def _create_new_thread():
    """Create a blank thread, reset chat state, rerun."""
    new_id = create_thread(st.session_state.auth_user_id, "New Chat")
    st.session_state.current_thread_id = new_id
    st.session_state.messages = []
    st.session_state.current_bot_state = None
    st.session_state.chat_history = []
    st.rerun()


def _bulk_delete(thread_ids: list):
    """Delete every selected thread and clear their checkbox state."""
    for tid in thread_ids:
        delete_thread(tid)
        st.session_state.pop(f"sel_{tid}", None)
        if st.session_state.current_thread_id == tid:
            _clear_active_thread()
    st.rerun()


def _render_thread_row(thread: dict):
    """Single thread row: checkbox | title button | delete button."""
    tid = thread["id"]
    is_active = st.session_state.current_thread_id == tid

    # Truncate title for display
    raw_title = thread.get("title", "New Chat")
    label = raw_title[:22] + ("…" if len(raw_title) > 22 else "")

    c0, c1, c2 = st.columns([0.45, 3.6, 0.75])

    with c0:
        st.checkbox("", key=f"sel_{tid}", label_visibility="collapsed")

    with c1:
        btn_type = "primary" if is_active else "secondary"
        if st.button(
            f"💬 {label}",
            key=f"t_{tid}",
            use_container_width=True,
            type=btn_type,
        ):
            _switch_to_thread(tid)

    with c2:
        if st.button("🗑️", key=f"d_{tid}", help="Delete thread"):
            delete_thread(tid)
            st.session_state.pop(f"sel_{tid}", None)
            if st.session_state.current_thread_id == tid:
                _clear_active_thread()
            st.rerun()


def _switch_to_thread(tid: str):
    """Load a thread's messages and state into session, then rerun."""
    st.session_state.current_thread_id = tid
    msgs = get_thread_messages(tid)
    # Respect MAX_HISTORY from env
    st.session_state.messages = msgs
    st.session_state.chat_history = [
        {"role": m["role"], "content": m["content"]} for m in msgs
    ]
    st.session_state.current_bot_state = get_last_bot_state(tid)
    st.rerun()


def _clear_active_thread():
    """Reset session state when the active thread is deleted."""
    st.session_state.current_thread_id = None
    st.session_state.messages = []
    st.session_state.current_bot_state = None
    st.session_state.chat_history = []
