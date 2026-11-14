"""Retrieval.

Planned modules:
  dense.py      embed query -> pgvector cosine top-k
  sparse.py     Postgres full-text search (ts_rank_cd) top-k; exact ids like '118.5' and 'line 21900'
  hybrid.py     reciprocal rank fusion of dense + sparse
  expand.py     follow xrefs to pull in definitions and referenced provisions
  rerank.py     cross-encoder rerank to the final top ~8
  rewrite.py    LLM query rewrite: lay terms -> legal terms, extract tax_year
"""
