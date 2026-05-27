"""
RAG pipeline: query → retrieve → generate with Claude Sonnet 4.6.
Uses prompt caching to reduce API costs on repeated system prompts.
"""
import sys
from pathlib import Path
from typing import Generator

import anthropic

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY, LLM_MODEL, CONFIDENCE_THRESHOLD
from rag.retriever import retrieve, Chunk

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a Kaspersky-certified support expert assistant.

Rules you must follow without exception:
1. Base every answer STRICTLY on the retrieved official Kaspersky documentation provided below. Do not use any outside knowledge.
2. Always provide numbered step-by-step instructions. Never give vague advice.
3. Always cite the source URL at the end of your answer like: Source: <url>
4. If a step involves a potentially risky action (registry edit, uninstall, disabling a feature), add a safety warning before that step.
5. NEVER suggest disabling real-time protection or the antivirus engine.
6. If the retrieved documents do not clearly answer the question, say exactly: "I could not find a verified answer in the official Kaspersky knowledge base. Please contact Kaspersky support directly: https://support.kaspersky.com"
7. Keep answers concise but complete. Use markdown formatting."""


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


def ask(query: str, history: list[dict] | None = None) -> Generator[str, None, None]:
    """
    Stream a response. Yields text chunks.
    history: list of {"role": "user"|"assistant", "content": str}
    """
    chunks = retrieve(query)

    # No confident results → escalate immediately
    if not chunks:
        yield (
            "I could not find a verified answer in the official Kaspersky knowledge base. "
            "Please contact Kaspersky support directly: https://support.kaspersky.com"
        )
        return

    context = _build_context(chunks)

    messages: list[dict] = []

    # Inject conversation history (last 6 turns max to keep context tight)
    if history:
        messages.extend(history[-6:])

    messages.append({
        "role": "user",
        "content": (
            f"<retrieved_documents>\n{context}\n</retrieved_documents>\n\n"
            f"User question: {query}"
        ),
    })

    # Use prompt caching on the system prompt (saves ~80% on repeated calls)
    with claude.messages.stream(
        model=LLM_MODEL,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text


def ask_sync(query: str, history: list[dict] | None = None) -> str:
    return "".join(ask(query, history))
