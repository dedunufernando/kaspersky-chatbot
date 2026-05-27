"""
Reads crawled JSON files, chunks them, embeds with sentence-transformers (free/local),
and upserts into pgvector.
"""
import json
import sys
from pathlib import Path

import psycopg
from sentence_transformers import SentenceTransformer
from rich.console import Console
from rich.progress import track

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    DATABASE_URL,
    EMBEDDING_MODEL, EMBEDDING_DIMENSIONS,
    CHUNK_SIZE, CHUNK_OVERLAP,
)

console = Console()
console.print(f"[cyan]Loading embedding model '{EMBEDDING_MODEL}'...[/cyan]")
embedder = SentenceTransformer(EMBEDDING_MODEL)
console.print("[green]Model loaded.[/green]")

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"


def _split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split on newlines (paragraph/step boundaries),
    merging small paragraphs until we hit chunk_size words.
    Keeps numbered procedures intact.
    """
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        words = len(para.split())
        if current_len + words > chunk_size and current:
            chunks.append("\n".join(current))
            overlap_buf: list[str] = []
            overlap_len = 0
            for p in reversed(current):
                pw = len(p.split())
                if overlap_len + pw > overlap:
                    break
                overlap_buf.insert(0, p)
                overlap_len += pw
            current = overlap_buf
            current_len = overlap_len
        current.append(para)
        current_len += words

    if current:
        chunks.append("\n".join(current))

    return chunks


def _embed_batch(texts: list[str]) -> list[list[float]]:
    vectors = embedder.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


def ingest(force: bool = False) -> None:
    files = list(DATA_DIR.glob("*.json"))
    if not files:
        console.print("[red]No crawled files found. Run the crawler first.[/red]")
        return

    conn = psycopg.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()

    batch_texts: list[str] = []
    batch_meta: list[dict] = []
    BATCH = 32  # sentence-transformers handles batches efficiently

    def flush_batch():
        if not batch_texts:
            return
        vectors = _embed_batch(batch_texts)
        for meta, vec in zip(batch_meta, vectors):
            if not force:
                cur.execute(
                    "SELECT 1 FROM kb_chunks WHERE url=%s AND chunk_index=%s",
                    (meta["url"], meta["chunk_index"]),
                )
                if cur.fetchone():
                    continue
            cur.execute(
                """
                INSERT INTO kb_chunks (url, title, applies_to, last_modified, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT DO NOTHING
                """,
                (
                    meta["url"], meta["title"], meta["applies_to"],
                    meta["last_modified"], meta["chunk_index"],
                    meta["content"], str(vec),
                ),
            )
        batch_texts.clear()
        batch_meta.clear()

    total_chunks = 0
    for fpath in track(files, description="Ingesting articles..."):
        article = json.loads(fpath.read_text(encoding="utf-8"))
        chunks = _split_into_chunks(article["content"], CHUNK_SIZE, CHUNK_OVERLAP)

        for i, chunk in enumerate(chunks):
            batch_texts.append(chunk)
            batch_meta.append({
                "url": article["url"],
                "title": article["title"],
                "applies_to": article.get("applies_to", []),
                "last_modified": article.get("last_modified", ""),
                "chunk_index": i,
                "content": chunk,
            })
            total_chunks += 1
            if len(batch_texts) >= BATCH:
                flush_batch()

    flush_batch()
    cur.close()
    conn.close()
    console.print(f"[bold green]Done! Ingested {total_chunks} chunks from {len(files)} articles.[/bold green]")


if __name__ == "__main__":
    force = "--force" in sys.argv
    ingest(force=force)
