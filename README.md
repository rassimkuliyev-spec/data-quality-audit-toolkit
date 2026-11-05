# Data Quality Audit Toolkit

A small reproducible **Python + pandas** CLI project that checks common issues in raw CSV datasets before analysis. Built as an independent analytics portfolio demonstration (November 2026).

## What problem does it solve?
Data analysts spend time validating source data before interpreting KPIs. This tool produces a **summary of issues to investigate**, including missing values, duplicate rows, optional duplicate business keys, whitespace, inconsistent casing, mixed numeric/text values, and possible numeric outliers.

## Try it

```bash
python -m pip install -r requirements.txt
python -m src.audit sample_data/orders.csv --keys order_id --output quality_report.json
python -m unittest discover -s tests -v
```

Expected behavior for the included **synthetic sample data**: 6 rows; 1 exact duplicate row; 1 duplicate `order_id`. The output is structured JSON and intentionally contains aggregate metrics, not source records.

## Checks & interpretation

| Check | Approach | Important caveat |
|---|---|---|
| Missing values | pandas nulls + whitespace-only text | Custom missing codes may need normalization |
| Duplicate records | Entire row or `--keys` composite columns | Repeated records may be legitimate |
| Whitespace | Leading/trailing spaces in text fields | Some fields intentionally contain spaces |
| Case differences | Heuristic comparing casefolded uniqueness | A warning, not proof of error |
| Mixed types | Parseable vs non-parseable numeric strings | IDs and categories may contain digits |
| Numeric outliers | 1.5 × IQR rule on numeric-like columns | Statistical anomalies are not necessarily mistakes |

## Project layout

```text
src/audit.py             CLI + pandas audit logic
tests/test_audit.py      Automated unit tests
sample_data/orders.csv  Small synthetic example
.github/workflows/      CI to run tests on pushes
```

## Next iterations
- Schema contracts and configurable business constraints
- Referential integrity checks across tables
- HTML visualization of the audit report
- Larger-dataset performance benchmarks

## Privacy
Use **synthetic or properly anonymized** data in public repositories. Do not commit client datasets, tokens, `.env` files, or private contact information. The report avoids exporting raw rows but **does include column names**; check them before sharing.

## Notes
This tool is intended for triage and education. It does not claim to prove data correctness or work universally across data sources.
