"""
RAG pipeline: query → retrieve → generate with Groq (free LLM).
Supports multi-turn conversation with context-aware retrieval.
"""
import sys
from pathlib import Path
from typing import Generator

from groq import Groq

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import GROQ_API_KEY, LLM_MODEL
from rag.retriever import retrieve, Chunk

groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a Kaspersky-certified support expert assistant.

Rules you must follow without exception:
1. Base every answer STRICTLY on the retrieved official Kaspersky documentation provided below. Do not use any outside knowledge.
2. Always provide numbered step-by-step instructions. Never give vague advice.
3. Always cite the source URL at the end of your answer like: Source: <url>
4. If a step involves a potentially risky action (registry edit, uninstall, disabling a feature), add a safety warning before that step.
5. NEVER suggest disabling real-time protection or the antivirus engine.
6. If the retrieved documents do not clearly answer the question, say exactly: "I could not find a verified answer in the official Kaspersky knowledge base. Please contact Kaspersky support directly: https://support.kaspersky.com"
7. For follow-up messages like "i did those steps", "it didn't work", "still not working" — refer back to the conversation context and suggest the next troubleshooting step.
8. Keep answers concise but complete. Use markdown formatting."""


def _build_context(chunks: list[Chunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"--- Document {i} ---\n"
            f"Title: {chunk.title}\n"
            f"URL: {chunk.url}\n"
            f"Last modified: {chunk.last_modified or 'unknown'}\n\n"
            f"{chunk.content}"
        )
    return "\n\n".join(parts)


def _build_retrieval_query(query: str, history: list[dict] | None) -> str:
    """
    For short follow-up messages, combine with recent history
    so the retriever has enough context to find relevant chunks.
    e.g. "i did those steps" + previous "Kaspersky won't update" → better search
    """
    SHORT_QUERY_THRESHOLD = 10  # words
    if len(query.split()) >= SHORT_QUERY_THRESHOLD:
        return query  # long enough, use as-is

    if not history:
        return query

    # Grab last user message from history for context
    recent_user_msgs = [
        m["content"] for m in history[-6:]
        if m["role"] == "user"
    ]
    if recent_user_msgs:
        # Combine last user message with current query
        combined = f"{recent_user_msgs[-1]} {query}"
        return combined

    return query


def ask(query: str, history: list[dict] | None = None) -> Generator[str, None, None]:
    """
    Stream a response. Yields text chunks.
    history: list of {"role": "user"|"assistant", "content": str}
    """
    # Use context-aware query for retrieval
    retrieval_query = _build_retrieval_query(query, history)
    chunks = retrieve(retrieval_query)

    # Build messages for LLM
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Inject conversation history (last 6 turns for context)
    if history:
        messages.extend(history[-6:])

    if chunks:
        context = _build_context(chunks)
        messages.append({
            "role": "user",
            "content": (
                f"<retrieved_documents>\n{context}\n</retrieved_documents>\n\n"
                f"User question: {query}"
            ),
        })
    else:
        # No KB results — still pass the question with history, LLM will use rule 7
        messages.append({
            "role": "user",
            "content": query,
        })

    stream = groq_client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        max_tokens=1024,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def ask_sync(query: str, history: list[dict] | None = None) -> str:
    return "".join(ask(query, history))
