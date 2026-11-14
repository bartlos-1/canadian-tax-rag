"""Answer generation.

  answer.py   prompt: answer only from the provided sources, cite every claim as [source_id],
              say "not found in sources" when the sources don't cover it
  verify.py   every cited source_id must be in the retrieved set; otherwise retry once, then abstain
"""
