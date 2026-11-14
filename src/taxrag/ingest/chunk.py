"""Turn provision units / documents into retrievable chunks.

Input:  data/processed/*_units.jsonl  (from parse_legislation.py), parsed folios and guides
Output: data/processed/chunks.jsonl   (rows that match db/schema.sql `chunks`)

TODO (keep each strategy so you can A/B them in evals):
  1. chunk_fixed(text, size=512, overlap=64)       -- naive baseline
  2. chunk_structural(unit, max_tokens=600)        -- one unit = one chunk; split long units
     at the (a)/(b) paragraph lines (they are already one per line), and repeat the
     unit's lead-in text in each piece
  3. Prepend context before embedding, e.g.
     "ITA 118.5(1) — Tuition credit | PART I > DIVISION E > SUBDIVISION A\n<text>"
Stats from the current ITA parse: words/unit p50≈96, p90≈332, p99≈1071, max≈14.5k, so (2) matters.
"""
