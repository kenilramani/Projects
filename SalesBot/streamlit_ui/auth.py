"""
auth.py — Authentication UI (Login / Register / Logout).

Renders the auth gate screen before the main dashboard and the top-bar
logout strip once the user is authenticated.  All DB calls are delegated
to the database module imported via config-relative path injection done in
streamlit_app.py before this module is used.
"""

import streamlit as st
from database import create_user, verify_user, get_user_persona, save_user_persona


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------
def _get_default_persona():
    """Lazy import to avoid circular dependency at module level."""
    from persona import get_default_persona

    return get_default_persona()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def render_auth_screen():
    """
    Full-page login / register form.
    On successful auth the session state is populated and st.rerun() is called
    so the main dashboard renders on the next cycle.
    """
    st.markdown(
        '<div class="auth-wrap">',
        unsafe_allow_html=True,
    )

    # ── Hero card ──────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="auth-hero">
            <div style="font-size:2.4rem; margin-bottom:0.1rem;">🤖</div>
            <p class="auth-title">Botrunner Playground</p>
            <p class="auth-sub">Login or register to access your threads, QA tools &amp; persona.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Auth card with tabs ────────────────────────────────────────────
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    tab_login, tab_register = st.tabs(["Login", "Register"])

    # ── Login ──────────────────────────────────────────────────────────
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="yourname")
            password = st.text_input(
                "Password", type="password", placeholder="••••••••"
            )
            submit = st.form_submit_button(
                "Login", type="primary", use_container_width=True
            )

        if submit:
            user = verify_user(username, password)
            if not user:
                st.error("Invalid username or password.")
            else:
                _apply_login(user)

    # ── Register ───────────────────────────────────────────────────────
    with tab_register:
        with st.form("register_form"):
            full_name = st.text_input("Full name", placeholder="Jane Doe")
            username = st.text_input("Username", placeholder="janedoe")
            email = st.text_input("Email (optional)", placeholder="jane@company.com")
            password = st.text_input(
                "Password", type="password", placeholder="Create a strong password"
            )
            password2 = st.text_input(
                "Confirm password", type="password", placeholder="Repeat password"
            )
            submit = st.form_submit_button(
                "Create account", type="primary", use_container_width=True
            )

        if submit:
            if not full_name.strip() or not username.strip() or not password:
                st.error("Please fill in full name, username, and password.")
            elif password != password2:
                st.error("Passwords do not match.")
            else:
                try:
                    user_id = create_user(
                        username=username,
                        full_name=full_name,
                        password=password,
                        email=email,
                    )
                    persona = _get_default_persona()
                    save_user_persona(user_id, persona)

                    st.session_state.auth_user_id = user_id
                    st.session_state.auth_user_name = full_name.strip()
                    st.session_state.custom_persona = persona
                    st.success("Account created — you're logged in!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not create account: {exc}")

    st.markdown("</div></div>", unsafe_allow_html=True)


def render_topbar():
    """
    Thin top-bar shown after login: welcome text + logout button.
    """
    name = st.session_state.get("auth_user_name") or "User"

    c1, _, c3 = st.columns([5, 2, 1])
    with c1:
        st.markdown(
            f'<p style="font-size:0.88rem; color:#f0f2f5; font-weight:600; margin:0;">'
            f'👋 Welcome, <span style="color:#60a5fa;">{name}</span></p>',
            unsafe_allow_html=True,
        )
        st.caption("Persona is shared across all your threads.")
    with c3:
        if st.button("Logout", use_container_width=True):
            _clear_session()
            st.rerun()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------
def _apply_login(user: dict):
    """Populate session state after successful verification and rerun."""
    st.session_state.auth_user_id = user["id"]
    st.session_state.auth_user_name = user["full_name"]

    persona = get_user_persona(user["id"])
    if not persona:
        persona = _get_default_persona()
        save_user_persona(user["id"], persona)
    st.session_state.custom_persona = persona
    st.rerun()


def _clear_session():
    """Wipe all session state keys on logout."""
    keys = [
        "auth_user_id",
        "auth_user_name",
        "current_thread_id",
        "messages",
        "current_bot_state",
        "chat_history",
        "custom_persona",
    ]
    for k in keys:
        st.session_state[k] = None
    st.session_state.messages = []
    st.session_state.chat_history = []
