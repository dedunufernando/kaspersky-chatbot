-- Run this once against your PostgreSQL database
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS kb_chunks (
    id          SERIAL PRIMARY KEY,
    url         TEXT NOT NULL,
    title       TEXT,
    applies_to  TEXT[],
    last_modified TEXT,
    chunk_index INTEGER,
    content     TEXT NOT NULL,
    embedding   vector(3072),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS kb_chunks_embedding_idx
    ON kb_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS kb_chunks_url_idx ON kb_chunks (url);
