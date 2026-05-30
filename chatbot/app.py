"""
Kaspersky Expert AI Chatbot — Streamlit UI
Run: python -m streamlit run chatbot/app.py
"""
import json
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from rag.pipeline import ask

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kaspersky Expert AI",
    page_icon="🛡️",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.news-card {
    background: #1e1e2e;
    border-left: 3px solid #00a651;
    padding: 10px 14px;
    margin-bottom: 8px;
    border-radius: 4px;
}
.news-title { font-weight: bold; font-size: 0.9em; }
.news-meta  { color: #888; font-size: 0.75em; }
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.7em;
    font-weight: bold;
    margin-left: 6px;
}
.badge-blog { background:#1a6b3a; color:#fff; }
.badge-news { background:#1a3b6b; color:#fff; }
.badge-threat { background:#6b1a1a; color:#fff; }
</style>
""", unsafe_allow_html=True)

# ── Helper: load recent news from data/raw ────────────────────────────────────
def load_recent_news(limit: int = 8) -> list[dict]:
    news = []
    if not DATA_DIR.exists():
        return news
    files = sorted(DATA_DIR.glob("news_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    for f in files[:limit]:
        try:
            article = json.loads(f.read_text(encoding="utf-8"))
            news.append(article)
        except Exception:
            continue
    return news

# ── Layout: two columns ───────────────────────────────────────────────────────
chat_col, news_col = st.columns([2, 1])

# ══════════════════════════════════════════════════════════════════════════════
# LEFT: Main chat
# ══════════════════════════════════════════════════════════════════════════════
with chat_col:
    st.title("🛡️ Kaspersky Expert AI")
    st.caption(
        "Unofficial helper powered by official Kaspersky knowledge base. "
        "For critical issues, always contact [Kaspersky Support](https://support.kaspersky.com)."
    )

    QUICK_REPLIES = [
        "Kaspersky won't update on Windows 11",
        "Fix installation error 0x80070005",
        "USB block policy not applying to Linux device",
        "Network Agent not connecting to KSC",
        "Device Control running in test mode",
        "klmover command to change KSC server",
    ]

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not st.session_state.messages:
        st.markdown("**Common issues — click to ask:**")
        cols = st.columns(3)
        for i, q in enumerate(QUICK_REPLIES):
            if cols[i % 3].button(q, use_container_width=True):
                st.session_state.prefill = q
                st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prefill = st.session_state.pop("prefill", None)
    user_input = st.chat_input("Describe your Kaspersky issue...") or prefill

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]
        ]

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""
            for chunk in ask(user_input, history):
                full_response += chunk
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

# ══════════════════════════════════════════════════════════════════════════════
# RIGHT: News panel
# ══════════════════════════════════════════════════════════════════════════════
with news_col:
    st.subheader("📰 Latest Kaspersky News")

    news_items = load_recent_news(limit=10)

    if news_items:
        for item in news_items:
            cat = item.get("category", "news")
            badge_class = {"blog": "badge-blog", "threat_intel": "badge-threat"}.get(cat, "badge-news")
            badge_label = {"blog": "Blog", "threat_intel": "Threat Intel", "news": "News"}.get(cat, "News")
            url = item.get("url", "#")
            title = item.get("title", "No title")[:80]
            source = item.get("source", "")
            date = item.get("last_modified", "")[:10]

            st.markdown(f"""
<div class="news-card">
  <div class="news-title">
    <a href="{url}" target="_blank" style="color:#fff;text-decoration:none;">{title}</a>
    <span class="badge {badge_class}">{badge_label}</span>
  </div>
  <div class="news-meta">{source} · {date}</div>
</div>
""", unsafe_allow_html=True)
    else:
        st.info("No news yet. Run the news fetcher to populate:\n```\npython crawler/news_fetcher.py\n```")

    st.divider()

    # Last update time
    log_file = Path(__file__).parent.parent / "data" / "update_log.txt"
    if log_file.exists():
        lines = log_file.read_text(encoding="utf-8").strip().split("\n")
        last = next((l for l in reversed(lines) if "COMPLETE" in l or "Started" in l), "")
        if last:
            st.caption(f"🔄 {last[:60]}")
    else:
        st.caption("🔄 Auto-updates daily at midnight")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("About")
    st.markdown(
        "Answers sourced from the official "
        "[Kaspersky Support KB](https://support.kaspersky.com), "
        "Kaspersky Blog, and Securelist.\n\n"
        "**Supported products:**\n"
        "- Kaspersky Standard / Plus / Premium\n"
        "- Endpoint Security for Windows (KES)\n"
        "- KES for Linux\n"
        "- Kaspersky Security Center (KSC)\n"
        "- Network Agent / Device Control\n"
        "- Kaspersky VPN / Safe Kids"
    )
    st.divider()

    kb_count = len(list(DATA_DIR.glob("*.json"))) if DATA_DIR.exists() else 0
    news_count = len(list(DATA_DIR.glob("news_*.json"))) if DATA_DIR.exists() else 0
    st.metric("KB Articles", kb_count - news_count)
    st.metric("News Articles", news_count)

    st.divider()
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.rerun()

    if st.button("🔄 Refresh news now"):
        with st.spinner("Fetching latest news..."):
            try:
                from crawler.news_fetcher import fetch_all_news
                count = fetch_all_news(max_per_feed=20)
                st.success(f"Fetched {count} articles!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    st.caption("Not affiliated with Kaspersky Lab.")
