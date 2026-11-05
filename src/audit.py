"""Reproducible CSV data quality audit; does not export source rows."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def analyze_dataframe(df: pd.DataFrame, key_columns: list[str] | None = None) -> dict:
    """Compute data-quality diagnostics from a pandas dataframe.

    This tool checks structural and syntactic quality, not business correctness.
    It returns only aggregate diagnostics, never raw row values.
    """
    keys = key_columns or []
    missing_keys = [key for key in keys if key not in df.columns]
    if missing_keys:
        raise ValueError(f"Key columns not found: {', '.join(missing_keys)}")

    # Blank or whitespace-only strings count as missing.
    data = df.copy()
    for col in data.columns:
        if pd.api.types.is_object_dtype(data[col]) or pd.api.types.is_string_dtype(data[col]):
            data[col] = data[col].replace(r"^\s*$", pd.NA, regex=True)

    rows = int(len(data))
    columns = []
    for col in data.columns:
        series = data[col]
        present = series.dropna()
        text = present.astype(str)
        stripped = text.str.strip()
        whitespace_count = int((stripped != text).sum())
        numeric = pd.to_numeric(stripped, errors="coerce")
        numeric_count = int(numeric.notna().sum())
        valid_count = int(len(present))
        mixed_numeric_text = numeric_count > 0 and numeric_count < valid_count
        potential_case_variants = int(
            stripped.str.casefold().nunique() < stripped.nunique()
        ) if valid_count else 0

        outlier_count = None
        if (valid_count >= 4 and numeric_count / valid_count >= 0.9
                and "id" not in str(col).lower()):
            numeric_values = numeric.dropna()
            q1, q3 = numeric_values.quantile([0.25, 0.75])
            iqr = q3 - q1
            if iqr > 0:
                outlier_count = int(((numeric_values < q1 - 1.5 * iqr)
                                     | (numeric_values > q3 + 1.5 * iqr)).sum())
            else:
                outlier_count = 0

        missing_count = int(series.isna().sum())
        columns.append({
            "name": str(col),
            "missing_count": missing_count,
            "missing_pct": round(100 * missing_count / rows, 2) if rows else 0.0,
            "unique_non_null": int(present.nunique()),
            "leading_trailing_whitespace_rows": whitespace_count,
            "mixed_numeric_and_text": bool(mixed_numeric_text),
            "possible_case_inconsistency": bool(potential_case_variants),
            "numeric_outliers_iqr": outlier_count,
        })

    key_dupes = int(data.duplicated(subset=keys).sum()) if keys else None
    return {
        "summary": {
            "rows": rows,
            "columns": int(data.shape[1]),
            "exact_duplicate_rows": int(data.duplicated().sum()),
            "duplicate_key_rows": key_dupes,
            "key_columns": keys,
        },
        "column_checks": columns,
        "limitations": [
            "A data-quality flag does not prove an error.",
            "IQR outliers require domain review and can reflect valid rare events.",
            "Business rules and cross-table integrity are not checked.",
            "Case inconsistencies are heuristic signals, not confirmed duplicates.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a CSV file and save aggregate quality metrics.")
    parser.add_argument("csv_path", type=Path, help="Path to CSV file")
    parser.add_argument("--keys", nargs="*", default=[], help="Optional composite key columns")
    parser.add_argument("--output", type=Path, default=Path("quality_report.json"))
    args = parser.parse_args()

    if not args.csv_path.is_file():
        parser.error(f"CSV file not found: {args.csv_path}")
    df = pd.read_csv(args.csv_path, dtype="string", keep_default_na=True)
    result = analyze_dataframe(df, args.keys)
    result["generated_utc"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {args.output}: {result['summary']['rows']} rows, "
          f"{result['summary']['exact_duplicate_rows']} exact duplicates")


if __name__ == "__main__":
    main()
