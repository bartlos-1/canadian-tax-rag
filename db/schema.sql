-- One table holds dense vectors, full-text (BM25-ish) search and metadata.
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id            TEXT PRIMARY KEY,           -- e.g. 'ITA 118.5(1)#0'
    source_type   TEXT NOT NULL,              -- legislation | regulation | folio | guide | reference
    source_id     TEXT NOT NULL,              -- 'ITA 118.5(1)', 'S1-F2-C2 ¶2.14', 't4044 p.12'
    title         TEXT,                       -- marginal note / heading
    breadcrumb    TEXT,                       -- prepended to text before embedding
    text          TEXT NOT NULL,
    url           TEXT,                       -- deep link for clickable citations
    tax_year_from INT,
    tax_year_to   INT,
    t1_lines      TEXT[],                     -- e.g. {'32300'}: links the law to the return
    meta          JSONB DEFAULT '{}'::jsonb,
    -- 1024 dims fits voyage-3 / bge-m3. Change it to match your embedding model.
    embedding     vector(1024),
    tsv           tsvector GENERATED ALWAYS AS (
                    to_tsvector('english', coalesce(title,'') || ' ' || coalesce(source_id,'') || ' ' || text)
                  ) STORED
);

CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING gin (tsv);
CREATE INDEX IF NOT EXISTS chunks_emb_idx ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_src_idx ON chunks (source_type, source_id);

-- Cross-references ("see paragraph 60(b)") used for retrieval expansion
CREATE TABLE IF NOT EXISTS xrefs (
    from_id TEXT NOT NULL,
    to_id   TEXT NOT NULL,
    kind    TEXT,                             -- 'refers_to' | 'defines'
    PRIMARY KEY (from_id, to_id)
);
