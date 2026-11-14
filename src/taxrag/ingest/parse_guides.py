"""Parse CRA guide PDFs (data/raw/guides/*.pdf) with pypdf.

TODO:
  - Extract text per page and keep the page number, so citations can say 't4044 p.12'.
  - Detect T1 line references ('line 21900', 'line 32300'). Store them in chunks.t1_lines.
    These are what connect an answer to the actual return.
  - Watch for running headers/footers and two-column layouts. Inspect the output by eye.
  - p105 and t4055 are older editions (24/23). Mark them with tax_year so the
    system can warn that the guide may be stale.
"""
