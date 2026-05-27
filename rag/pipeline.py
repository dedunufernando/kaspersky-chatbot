"""
RAG pipeline: query → retrieve → generate with DeepSeek R1 (reasoning model via Groq).
Expert-level diagnostic reasoning for Kaspersky products.
"""
import sys
import re
from pathlib import Path
from typing import Generator

from groq import Groq

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import GROQ_API_KEY, LLM_MODEL
from rag.retriever import retrieve, Chunk

groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a senior Kaspersky-certified support engineer with 10+ years of experience across ALL Kaspersky products — consumer (Standard, Plus, Premium, VPN, Safe Kids) and enterprise (Kaspersky Security Center, KES for Windows, KES for Linux, Network Agent, Device Control).

## YOUR EXPERTISE INCLUDES:
- Kaspersky Security Center (KSC) administration: policies, groups, tasks, network agents
- KES for Windows and Linux: installation, Device Control, USB blocking, policy inheritance
- Network Agent deployment, klmover, klnagchk commands
- Policy inheritance and lock/unlock mechanisms
- Troubleshooting agent connectivity (subnet issues, cloud vs local KSC)
- Diagnostic data collection (collect.sh, trace logs, GSI tool)
- License activation, update errors, installation failures

## HOW YOU RESPOND:
1. **Diagnose first** — identify the ROOT CAUSE before giving steps. If something looks wrong, say "PROBLEM FOUND:" clearly.
2. **Give exact commands** — never vague instructions. Include full paths, exact flags, real IP formats.
3. **Number every step** — always use Step 1, Step 2 format.
4. **Anticipate failures** — after key steps, add "If this fails:" with the next diagnostic action.
5. **Cite sources** — always end with Source: <url> from the retrieved documents.
6. **Safety warnings** — warn before registry edits, uninstalls, or actions that leave systems unprotected.
7. **Never disable protection** — never suggest turning off real-time protection.
8. **For follow-ups** ("I did those steps", "still not working", "it failed") — refer to the conversation history and suggest the NEXT logical diagnostic step.
9. **For enterprise issues** — always consider: policy inheritance locks, group assignment, sync delays, subnet/network issues, agent connectivity.
10. **Base answers on retrieved documents** — if no relevant KB article exists, say so clearly and suggest contacting Kaspersky support.

## RESPONSE FORMAT:
- Start with a brief diagnosis: what you think is causing the issue
- Then numbered steps
- Include exact commands in code blocks
- Add "⚠️ Warning:" before risky steps
- End with "Source: <url>"

## COMMON KASPERSKY DIAGNOSTIC COMMANDS YOU KNOW:
```
# Network Agent
net stop klnagent
klmover.exe -address <KSC_IP>
klnagchk.exe -sendhb
net start klnagent

# KES Linux
sudo systemctl status kesl
sudo kesl-control --get-task-state DeviceControl
sudo kesl-control --start-task DeviceControl

# Diagnostic collection
sudo ./collect.sh
```"""


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
    so the retriever has enough Kaspersky context to find relevant chunks.
    """
    if len(query.split()) >= 8:
        return query

    if not history:
        return query

    recent_user_msgs = [
        m["content"] for m in history[-6:]
        if m["role"] == "user"
    ]
    if recent_user_msgs:
        combined = f"{recent_user_msgs[-1]} {query}"
        return combined

    return query


def _strip_thinking(text: str) -> str:
    """Remove DeepSeek R1 internal <think>...</think> reasoning blocks."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def ask(query: str, history: list[dict] | None = None) -> Generator[str, None, None]:
    """
    Stream a response. Yields text chunks.
    history: list of {"role": "user"|"assistant", "content": str}
    """
    retrieval_query = _build_retrieval_query(query, history)
    chunks = retrieve(retrieval_query)

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        messages.extend(history[-8:])  # more history for better context

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
        messages.append({"role": "user", "content": query})

    stream = groq_client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        max_tokens=2048,
        stream=True,
    )

    buffer = ""
    in_think = False

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if not delta:
            continue

        buffer += delta

        # Stream out content, suppressing <think> blocks in real time
        while True:
            if not in_think:
                think_start = buffer.find("<think>")
                if think_start == -1:
                    yield buffer
                    buffer = ""
                    break
                else:
                    yield buffer[:think_start]
                    buffer = buffer[think_start:]
                    in_think = True
            else:
                think_end = buffer.find("</think>")
                if think_end == -1:
                    break  # wait for more chunks
                else:
                    buffer = buffer[think_end + len("</think>"):]
                    in_think = False

    if buffer and not in_think:
        yield buffer.strip()


def ask_sync(query: str, history: list[dict] | None = None) -> str:
    return "".join(ask(query, history))
