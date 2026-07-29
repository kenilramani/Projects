"""
bot_state.py — Right-column BotState Inspector.

Renders every section of the BotState dict returned by /chat_ui in a
structured, scannable layout.  Uses custom HTML badges and key-value rows
styled via the shared CSS.
"""

import streamlit as st
import requests
from config import STATE_CONTAINER_HEIGHT, GENERATE_EXECUTIVE_SUMMARY_ENDPOINT, API_CHAT_TIMEOUT
from kb_dialog import kb_dialog
from persona import persona_config_dialog


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------
def render_inspector_panel():
    """
    Full right-column inspector.  Call inside the right Streamlit column.
    """
    # ── Header row ───────────────────────────────────────────────────
    st.markdown("##### 📊 BotState Inspector")

    # Action Buttons
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("⚙️ Persona", use_container_width=True):
            persona_config_dialog()
    with b2:
        if st.button("📚 KB", use_container_width=True, help="Manage Knowledge Base"):
            kb_dialog()
    with b3:
        if st.button("🔄 Refresh", key="refresh_state", use_container_width=True):
            if st.session_state.current_thread_id:
                from database import get_last_bot_state

                st.session_state.current_bot_state = get_last_bot_state(
                    st.session_state.current_thread_id
                )

    st.divider()

    # ── Scrollable state container ───────────────────────────────────
    with st.container(height=STATE_CONTAINER_HEIGHT):
        state = st.session_state.current_bot_state
        if state:
            _render_bot_state(state)
        else:
            st.info("📭 Send a message to see BotState updates.")


# ---------------------------------------------------------------------------
# Private: section renderers
# ---------------------------------------------------------------------------
def _render_bot_state(s: dict):
    """Top-level dispatcher: renders every inspector section in order."""
    if "error" in s:
        st.error(s["error"])
        return

    uc = s.get("user_context") or {}
    bp = s.get("bot_persona") or {}

    _section_persona(bp)
    _section_agent_guardrails(s, uc)
    _section_user_context(uc)
    _section_collected_fields(uc)
    _section_booking_followup(uc)
    _section_negotiation(s)
    _section_probing(s, uc)
    _section_objection(s)
    _section_summary(uc)
    _section_raw_json(s)


def _section_negotiation(s: dict):
    ns = s.get("negotiation_state") or {}
    session = ns.get("negotiation_session") or {}
    
    if not session:
        return

    # Get negotiated products list
    negotiated_products = session.get("negotiated_products") or []
    current_product_id = session.get("current_product_id")
    current_product_name = session.get("current_product_name")
    
    # Only show products that have been actively negotiated
    # (filter out empty/default-only entries, but ALWAYS include current product)
    active_products = [
        p for p in negotiated_products
        if p.get("product_id") == current_product_id
        or p.get("negotiation_active")
        or p.get("negotiation_attempts", 0) > 0
        or p.get("current_discount_percent", 0) > 0
        or p.get("discount_locked")
    ]
    
    if not active_products:
        return

    st.markdown(
        '<p class="section-label">🤝 Negotiation State</p>',
        unsafe_allow_html=True,
    )
    
    # Show current product being discussed
    if current_product_name:
        st.markdown(
            f'<div class="kv-row">'
            f'  <span class="kv-key">Current Product</span>'
            f'  <span class="badge badge-blue" style="font-size:0.8em; padding:2px 6px;">{current_product_name}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
    
    # Render each negotiated product
    for idx, product in enumerate(active_products):
        pid = product.get("product_id", "Unknown")
        pname = product.get("product_name") or pid
        is_current = pid == current_product_id
        
        # Product header with badge
        header_badge = "badge-green" if is_current else "badge-muted"
        header_label = f"📌 {pname}" if is_current else pname
        st.markdown(
            f'<div style="margin-top:0.5rem;">'
            f'  <span class="badge {header_badge}" style="font-size:0.8em; padding:2px 8px;">{header_label}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
    
        # Row 1: Status & Phase
        c1, c2 = st.columns(2)
        with c1:
            active = product.get("negotiation_active", False)
            st.markdown(
                f'<span class="badge {"badge-green" if active else "badge-muted"}">'
                f'{"Active" if active else "Inactive"}</span>', 
                unsafe_allow_html=True
            )
        with c2:
            phase = product.get("negotiation_phase", "initial")
            _kv("Phase", phase or "initial")
            
        # Row 2: Pricing
        c3, c4 = st.columns(2)
        with c3:
            price = product.get("active_base_price")
            _kv("Base Price", f"{price:,.0f}" if price else "Not Set")
        with c4:
            curr = product.get("current_discount_percent", 0)
            max_d = product.get("max_discount_percent", 0)
            _kv("Discount", f"{curr}% / {max_d}%")

        # Row 3: Lock & Round
        c5, c6 = st.columns(2)
        with c5:
            locked = product.get("discount_locked", False)
            badge = "badge-red" if locked else "badge-gray"
            label = "LOCKED" if locked else "Open"
            st.markdown(
                f'<div class="kv-row">'
                f'  <span class="kv-key">Status</span>'
                f'  <span class="badge {badge}" style="font-size:0.8em; padding:2px 6px;">{label}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
        with c6:
            _kv("Round", str(product.get("negotiation_attempts", 0)))

        # Row 4: Final Price & Budget
        c7, c8 = st.columns(2)
        with c7:
            final_price = product.get("final_price")
            _kv("Final Price", f"{final_price:,.0f}" if final_price else "—")
        with c8:
            budget = product.get("user_budget_constraint")
            _kv("Budget", f"{budget:,.0f}" if budget else "—")

        # Row 5: Last Offer Response & Discount Offered
        c9, c10 = st.columns(2)
        with c9:
            last_resp = product.get("last_offer_response")
            _kv("Last Response", last_resp if last_resp else "—")
        with c10:
            disc_offered = product.get("negotiation_discount_offered", False)
            _kv("Disc Offered", "Yes" if disc_offered else "No")

        # Internal Note
        internal_note = product.get("internal_note")
        if internal_note:
            st.markdown("**📝 Internal Note:**")
            st.caption(internal_note)

        # Reasoning
        reasoning = product.get("reasoning")
        if reasoning:
            st.markdown("**🧠 Strategy:**")
            st.info(reasoning)
        
        # Separator between products (not after the last one)
        if idx < len(active_products) - 1:
            st.markdown("<hr style='margin:0.5rem 0; border-color:#333;'>", unsafe_allow_html=True)
        
    st.divider()


# ── Individual sections ────────────────────────────────────────────────────


def _section_persona(bp: dict):
    st.markdown(
        '<p class="section-label">🎭 Bot Persona</p>',
        unsafe_allow_html=True,
    )
    _kv("Name", bp.get("name", "—"))
    _kv("Company", bp.get("company_name", "—"))
    _kv("Goal", bp.get("goal_type", "—"))
    st.divider()


def _section_agent_guardrails(s: dict, uc: dict):
    st.markdown(
        '<p class="section-label">🤖 Agent & Guardrails</p>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        agent = uc.get("last_agent") or "—"
        st.markdown(
            f'<span class="badge badge-blue">{agent}</span>', unsafe_allow_html=True
        )
    with c2:
        gd = s.get("guardrail_decision")
        if gd and isinstance(gd, dict):
            cls = gd.get("classification", "—")
            attack = gd.get("is_attack_query", False)
            badge = "badge-red" if attack else "badge-green"
            label = f"{cls} {'⚠️' if attack else '✓'}"
        else:
            badge, label = "badge-muted", "Passed"
        st.markdown(
            f'<span class="badge {badge}">{label}</span>', unsafe_allow_html=True
        )
    st.divider()


def _section_user_context(uc: dict):
    st.markdown(
        '<p class="section-label">👤 User Context</p>',
        unsafe_allow_html=True,
    )
    uid = str(uc.get("user_id") or "—")
    _kv("User ID", uid[:18] + ("…" if len(uid) > 18 else ""))
    _kv("Tenant", uc.get("tenant_id") or "—")
    _kv("Booking", str(uc.get("booking_confirmed", False)))
    _kv("Human Req", str(uc.get("human_requested", False)))
    st.divider()


def _section_collected_fields(uc: dict):
    st.markdown(
        '<p class="section-label">📋 Collected Fields</p>',
        unsafe_allow_html=True,
    )
    cf = uc.get("collected_fields")
    if cf and isinstance(cf, dict) and any(v for v in cf.values() if v):
        st.json(cf, expanded=False)
    else:
        st.caption("No fields collected yet")

    # Contact & lead details (optional extras)
    for key, label in [("contact_details", "Contact"), ("lead_details", "Lead")]:
        val = uc.get(key)
        if val:
            st.markdown(f"**{label}:**")
            st.json(val, expanded=False)
    st.divider()


def _section_booking_followup(uc: dict):
    st.markdown(
        '<p class="section-label">📅 Booking & Followup</p>',
        unsafe_allow_html=True,
    )

    followup = uc.get("followup_details", {}) or {}

    c1, c2 = st.columns(2)

    with c1:
        _kv("Book Confirmed", str(uc.get("booking_confirmed", False)))
        _kv("Book Type", str(uc.get("booking_type") or "—"))

    with c2:
        followup_flag = followup.get("followup_flag", False)
        _kv("Followup", str(followup_flag))

        followup_time = followup.get("followup_time")
        if followup_time:
            _kv("Time", followup_time)

    st.divider()


def _section_probing(s: dict, uc: dict):
    pc = s.get("probing_context") or {}
    bp = s.get("bot_persona") or {}

    if not pc:
        return

    st.markdown(
        '<p class="section-label">🔍 Probing Context</p>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        _kv("Score", str(pc.get("total_score", 0.0)))
        _kv("Completed", str(pc.get("probing_completed", False)))
    with c2:
        _kv("CTA Ready", str(pc.get("can_show_cta", False)))
        _kv("Threshold", str(bp.get("probing_threshold", "—")))

    # Detected Q&A pairs
    for qa in pc.get("detected_question_answer") or []:
        if isinstance(qa, dict):
            st.markdown(
                f'<p style="font-size:0.74rem; color:#9ca3af; margin:0.2rem 0 0;">'
                f'<b>Q.</b> {qa.get("question","")}</p>'
                f'<p style="font-size:0.74rem; color:#60a5fa; margin:0.05rem 0 0.25rem; padding-left:0.7rem;">'
                f'→ {qa.get("answer","")}</p>',
                unsafe_allow_html=True,
            )

    # Reasoning
    pd = uc.get("probing_details") or {}
    reasoning = pd.get("reasoning") if isinstance(pd, dict) else None
    if reasoning:
        st.markdown("**🧠 Reasoning:**")
        st.info(reasoning)
    st.divider()


def _section_objection(s: dict):
    os_data = s.get("objection_state") or {}
    bp = s.get("bot_persona") or {}

    st.markdown(
        '<p class="section-label">⛔ Objection Details</p>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        _kv("Count", str(os_data.get("current_objection_count", 0)))
        _kv("Limit", str(bp.get("objection_count_limit", "—")))
    with c2:
        reached = os_data.get("is_objection_limit_reached", False)
        # Use a badge style for limit reached
        label = "YES" if reached else "No"
        badge = "badge-red" if reached else "badge-muted"
        st.markdown(
            f'<div class="kv-row">'
            f'  <span class="kv-key">Limit Reached</span>'
            f'  <span class="badgex {badge}" style="font-size:0.8em; padding:2px 6px; border-radius:4px;">{label}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    st.divider()


def _section_summary(uc: dict):
    st.markdown(
        '<p class="section-label">📝 Executive Summary</p>',
        unsafe_allow_html=True,
    )

    # Show existing executive summary if present
    existing = st.session_state.get("executive_summary") or uc.get("executive_summary") or ""
    if existing:
        st.markdown(existing)

    # Generate button
    if st.button("📊 Generate Executive Summary", key="gen_exec_summary", use_container_width=True):
        agent_result = uc.get("agent_result") or []
        chat_history = uc.get("chat_history") or []

        if not agent_result and not chat_history:
            st.warning("No conversation data available yet. Send some messages first.")
        else:
            with st.spinner("Generating executive summary..."):
                try:
                    resp = requests.post(
                        GENERATE_EXECUTIVE_SUMMARY_ENDPOINT,
                        json={
                            "agent_result": agent_result,
                            "chat_history": chat_history,
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=API_CHAT_TIMEOUT,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    summary = data.get("executive_summary", "")
                    if summary:
                        st.session_state["executive_summary"] = summary
                        st.rerun()
                    else:
                        st.warning("Summary returned empty.")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to API. Is the server running?")
                except requests.exceptions.Timeout:
                    st.error("Request timed out.")
                except Exception as e:
                    st.error(f"Error generating summary: {e}")

    st.divider()


def _section_raw_json(s: dict):
    with st.expander("📄 Full BotState JSON", expanded=False):
        st.json(s)


# ---------------------------------------------------------------------------
# Micro-helpers
# ---------------------------------------------------------------------------
def _kv(key: str, value: str):
    """Render a single key-value row using the .kv-row CSS class."""
    st.markdown(
        f'<div class="kv-row">'
        f'  <span class="kv-key">{key}</span>'
        f'  <span class="kv-val">{value}</span>'
        f"</div>",
        unsafe_allow_html=True,
    )
