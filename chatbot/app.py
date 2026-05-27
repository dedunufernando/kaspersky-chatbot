"""
Kaspersky Expert AI Chatbot — Streamlit UI
Run: streamlit run chatbot/app.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from rag.pipeline import ask

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kaspersky Expert AI",
    page_icon="🛡️",
    layout="centered",
)

st.title("🛡️ Kaspersky Expert AI")
st.caption(
    "Unofficial helper powered by official Kaspersky knowledge base. "
    "For critical issues, always contact [Kaspersky Support](https://support.kaspersky.com)."
)

# ── Quick-reply buttons ───────────────────────────────────────────────────────
QUICK_REPLIES = [
    "Kaspersky won't update on Windows 11",
    "Fix installation error 0x80070005",
    "Kaspersky VPN not connecting",
    "License activation failed",
    "Kaspersky blocking my app",
]

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown("**Common issues — click to ask:**")
    cols = st.columns(len(QUICK_REPLIES))
    for col, q in zip(cols, QUICK_REPLIES):
        if col.button(q, use_container_width=True):
            st.session_state.prefill = q
            st.rerun()

# ── Chat history display ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input ─────────────────────────────────────────────────────────────────────
prefill = st.session_state.pop("prefill", None)
user_input = st.chat_input("Describe your Kaspersky issue...") or prefill

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build history for multi-turn context (exclude current message)
    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        for chunk in ask(user_input, history):
            full_response += chunk
            response_placeholder.markdown(full_response + "▌")

        response_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("About")
    st.markdown(
        "This chatbot retrieves answers **only** from the official "
        "[Kaspersky Support KB](https://support.kaspersky.com). "
        "It does not guess or hallucinate solutions.\n\n"
        "**Supported products:**\n"
        "- Kaspersky Standard / Plus / Premium\n"
        "- Endpoint Security for Windows\n"
        "- Kaspersky Security Center\n"
        "- Kaspersky VPN\n"
        "- Safe Kids / Password Manager"
    )
    st.divider()
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("Not affiliated with Kaspersky Lab.")
