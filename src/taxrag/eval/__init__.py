"""Eval harness.

  run_eval.py  for each question in eval/gold.jsonl: run a pipeline config, log retrieved ids + answer
  metrics.py   recall@k / MRR against expected_sources; LLM-judge correctness + faithfulness;
               citation accuracy; abstention precision on answerable=false items
Record every run (config, git sha, metrics) in eval/results/ so you can build the ablation table.
"""
