# TaxRAG: Canadian personal income tax research assistant

A retrieval-augmented assistant that answers T1 (individual) federal income tax questions.
Every answer cites the *Income Tax Act*, the Regulations, CRA Income Tax Folios and CRA guides.
Year-specific amounts come from a structured table, so the LLM never produces them itself.

> 🚧 **Work in progress.** Only the corpus download and the legislation parser work so far. Retrieval,
> generation, evaluation and the UI are not built yet, so the system cannot answer questions today.

> Not tax advice. This is a research tool. Verify answers with the CRA or a tax professional.

## Quickstart

```bash
git clone https://github.com/bartlos-1/canadian-tax-rag.git && cd canadian-tax-rag
python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"
cp .env.example .env                 # add your ANTHROPIC_API_KEY
python scripts/download_sources.py   # safe to re-run; skips files you already have
python -m taxrag.ingest.parse_legislation data/raw/legislation/ita.xml data/processed/ita_units.jsonl --act ITA
python -m taxrag.ingest.parse_legislation data/raw/legislation/itr.xml data/processed/itr_units.jsonl --act ITR
docker compose up -d                 # Postgres 16 + pgvector; applies db/schema.sql on first start
```

## Corpus (`data/raw/`, ~28 MB, provenance in `manifest.json`)

| Folder | Contents |
|---|---|
| `legislation/` | `ita.xml` Income Tax Act, `itr.xml` Income Tax Regulations. Justice Laws XML, point-in-time 2026-06-18 |
| `guides/` | 5000-G (line-by-line guide), 5000-R (the T1 return), T4040 RRSPs, T4044 employment expenses, T4037 capital gains, RC4064 disability, P105 students (**2024 ed.**), T4055 newcomers (**2023 ed.**), T4002 self-employed, T4036 rental |
| `folios/series-{1,2,3,5}/` | 36 Income Tax Folio chapters: individuals, employment, investments/registered plans, residency |
| `reference/` | Tax rates by year, indexation amounts, RRSP/TFSA/YMPE limits. Use these to fill `data/structured/indexed_amounts.csv` |

Not included: Schedule 1 (5000-S1) and the RC4466 TFSA guide, because CRA has no stable URL for them right now. Tax Court decisions are also excluded, because CanLII's terms forbid bulk scraping.

## Layout

```
config/sources.yaml        what to download (edit to add sources)
scripts/download_sources.py
src/taxrag/
  ingest/   parse_legislation.py (done) · chunk.py · parse_folios.py · parse_guides.py (TODO)
  retrieval/ dense · sparse · hybrid · expand · rerank · rewrite (TODO)
  generation/ answer + citation verification (TODO)
  tools/    get_indexed_amount · calc_federal_tax · get_provision (TODO)
  eval/     harness + metrics (TODO)
db/schema.sql              chunks (vector + tsvector + metadata), xrefs
eval/gold.jsonl            10 seed eval questions (WIP: expected answers still TODO)
data/structured/           year-indexed amounts (not RAG)
app/                       UI (Streamlit, later)
```

## Status (WIP)

- [x] Corpus download with provenance manifest
- [x] Legislation parser (7,307 ITA units, 2,116 ITR units, 1,941 defined terms)
- [ ] Folio and guide parsers, chunking — in progress
- [ ] Retrieval, generation, evaluation, API/UI — not started

## Known parser quirks (things to improve)

- **Stale breadcrumbs:** The Act has no headings for some runs of sections. For example, 118–118.9 still sit under the "Annual Adjustment…" heading that precedes 117.1. Consider overriding it with the marginal note.
- **Definitions in sections without subsections** (e.g. s. 54 "principal residence") stay as one big unit. Only definitions subsections such as 248(1) are split per term.
- **Internal cross-references** ("subsection (1.2)", "paragraph 60(b)") are plain text in the XML. Extract them with a regex in a later cross-reference step.
