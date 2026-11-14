# Structured amounts (not RAG)

Year-specific numbers (brackets, rates, basic personal amount, RRSP/TFSA/FHSA limits, YMPE)
go in `indexed_amounts.csv`. The `get_indexed_amount` tool serves them, so the LLM never
supplies these numbers from its own memory.

Fill it from `data/raw/reference/{tax-rates,indexation,plan-limits}.html`. Parse those pages
with code, cite each row's `source_url`, and **check every row by hand**.

Suggested `name` values: `bracket_1_upper`, `rate_1`, ..., `bpa_max`, `bpa_min`, `rrsp_dollar_limit`,
`tfsa_annual_limit`, `fhsa_annual_limit`, `ympe`, `canada_employment_amount`.
