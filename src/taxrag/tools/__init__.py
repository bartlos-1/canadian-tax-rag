"""Tools the LLM can call (Claude tool use).

  get_indexed_amount(tax_year, name) -> value + source_url   (reads data/structured/indexed_amounts.csv)
  calc_federal_tax(taxable_income, tax_year) -> breakdown    (deterministic; unit-test it)
  get_provision(id) -> full text of e.g. 'ITA 8(13)'
  search_corpus(query, filters) -> chunks
"""
