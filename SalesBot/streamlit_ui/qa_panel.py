"""
qa_panel.py — Full-width QA Testing Panel (below the 3-column layout).

Features:
  • Loads test questions from QA_PAIRS.csv, grouped by agent_type
  • One-click send any question into the active chat thread
  • Side-by-side expected vs actual response comparison
  • Quick-evaluation checks (handoff, guardrail, response presence)
"""

import streamlit as st
import pandas as pd
from config import QA_PAIRS_CSV, QA_SCROLL_CONTAINER_HEIGHT


# ---------------------------------------------------------------------------
# CSV loader (cached)
# ---------------------------------------------------------------------------
@st.cache_data
def load_qa_pairs() -> pd.DataFrame:
    """
    Read QA_PAIRS.csv.  Cached so it only touches disk once per session.
    Returns an empty DataFrame with the expected columns when the file is
    missing so the rest of the code never has to guard against None.
    """
    if QA_PAIRS_CSV.exists():
        return pd.read_csv(QA_PAIRS_CSV)
    return pd.DataFrame(columns=["agent_type", "question", "expected_response"])


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------
def render_qa_panel():
    """Render the full QA panel.  Call at the bottom of streamlit_app.py."""
    st.divider()
    st.markdown("##### 🧪 QA Testing Panel")

    df = load_qa_pairs()
    if df.empty:
        st.warning("⚠️ No QA pairs found — check `streamlit_ui/data/QA_PAIRS.csv`.")
        return

    left, right = st.columns([1, 1])

    with left:
        _render_question_picker(df)

    with right:
        _render_comparison()


# ---------------------------------------------------------------------------
# Left panel – question list grouped by agent
# ---------------------------------------------------------------------------
def _render_question_picker(df: pd.DataFrame):
    st.markdown("##### 📋 Select Test Question")

    scroll = st.container(height=QA_SCROLL_CONTAINER_HEIGHT)
    with scroll:
        for agent in df["agent_type"].unique():
            agent_df = df[df["agent_type"] == agent]
            title = agent.replace("_", " ").title()

            with st.expander(
                f"🤖 {title}  ({len(agent_df)} questions)", expanded=False
            ):
                for idx, row in agent_df.iterrows():
                    question = row["question"]
                    expected = row["expected_response"]

                    c1, c2 = st.columns([4, 0.8])
                    with c1:
                        # Truncated question preview
                        preview = question[:70] + ("…" if len(question) > 70 else "")
                        st.markdown(
                            f'<p style="font-size:0.78rem; color:#f0f2f5; margin:0.15rem 0 0;">'
                            f"<b>Q:</b> {preview}</p>",
                            unsafe_allow_html=True,
                        )
                        # Expected-response snippet
                        exp_preview = str(expected)[:80] + (
                            "…" if len(str(expected)) > 80 else ""
                        )
                        st.markdown(
                            f'<p style="font-size:0.7rem; color:#6b7280; margin:0.05rem 0 0.3rem;">'
                            f"Expected: {exp_preview}</p>",
                            unsafe_allow_html=True,
                        )
                    with c2:
                        if st.button("▶️", key=f"qa_{idx}", help="Send to chat"):
                            _dispatch_question(question, expected)


# ---------------------------------------------------------------------------
# Right panel – comparison view
# ---------------------------------------------------------------------------
def _render_comparison():
    st.markdown("##### 📊 Response Comparison")

    if not (
        st.session_state.qa_show_comparison and st.session_state.qa_selected_question
    ):
        st.info("👈 Pick a question from the left panel to compare.")
        return

    # Question
    st.markdown("**📝 Question:**")
    st.info(st.session_state.qa_selected_question)

    # Expected
    st.markdown("**✅ Expected:**")
    st.success(st.session_state.qa_expected_response or "N/A")

    # Actual
    st.markdown("**🤖 Actual Response:**")
    state = st.session_state.current_bot_state
    if state and "response" in state:
        actual = state.get("response", "")
        st.warning(actual or "No response received")
        _render_quick_eval(actual)
    else:
        st.info("⏳ Waiting for response…")

    # Clear button
    if st.button("🔄 Clear Comparison"):
        st.session_state.qa_selected_question = None
        st.session_state.qa_expected_response = None
        st.session_state.qa_show_comparison = False
        st.rerun()


# ---------------------------------------------------------------------------
# Quick evaluation checks
# ---------------------------------------------------------------------------
def _render_quick_eval(actual: str):
    st.divider()
    st.markdown("**📈 Quick Evaluation:**")

    expected_lower = (st.session_state.qa_expected_response or "").lower()
    actual_lower = (actual or "").lower()
    state = st.session_state.current_bot_state or {}
    checks = []

    # 1. Handoff detection
    if "[handoff" in expected_lower or "-> " in expected_lower:
        last_agent = state.get("user_context", {}).get("last_agent", "")
        if last_agent:
            checks.append(("🔄 Handoff occurred", True, f"Routed → {last_agent}"))
        else:
            checks.append(("🔄 Handoff expected", False, "No handoff detected"))

    # 2. Response presence
    checks.append(
        ("💬 Response generated", bool(actual), "Bot responded" if actual else "Empty")
    )

    # 3. Guardrail classification
    if "classification:" in expected_lower:
        gd = state.get("guardrail_decision") or {}
        cls = gd.get("classification", "")
        atk = gd.get("is_attack_query", False)
        if "attack" in expected_lower and atk:
            checks.append(("🛡️ Attack detected", True, f"Class: {cls}"))
        elif "safe" in expected_lower and not atk:
            checks.append(("🛡️ Safe query", True, f"Class: {cls}"))
        else:
            checks.append(("🛡️ Guardrail mismatch", False, f"Got: {cls}"))

    # Render
    for label, passed, detail in checks:
        icon = "✅" if passed else "❌"
        color = "#34d399" if passed else "#f87171"
        st.markdown(
            f'<p style="font-size:0.77rem; color:{color}; margin:0.18rem 0;">'
            f"{icon} <b>{label}</b> — {detail}</p>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Dispatch helper
# ---------------------------------------------------------------------------
def _dispatch_question(question: str, expected: str):
    """
    Fire a QA question into the active chat thread (if one exists).
    Sets the pending-message machinery so chat.py picks it up on next rerun.
    """
    if not st.session_state.current_thread_id:
        st.toast("⚠️ Please select or create a chat thread first!")
        return

    st.session_state.qa_selected_question = question
    st.session_state.qa_expected_response = expected
    st.session_state.pending_message = question
    st.session_state.processing = True
    st.session_state.qa_show_comparison = True
    st.rerun()
