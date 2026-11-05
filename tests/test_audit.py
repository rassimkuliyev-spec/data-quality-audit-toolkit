"""Tests for edge cases and basic checks."""
import unittest
import pandas as pd
from src.audit import analyze_dataframe


class TestAudit(unittest.TestCase):
    def test_detects_duplicates_and_nulls(self):
        df = pd.DataFrame({"id": ["A", "A", "B"], "city": ["Almaty", "Almaty", "  "]})
        result = analyze_dataframe(df, ["id"])
        self.assertEqual(result["summary"]["exact_duplicate_rows"], 1)
        self.assertEqual(result["summary"]["duplicate_key_rows"], 1)
        self.assertEqual(result["column_checks"][1]["missing_count"], 1)

    def test_strips_whitespace_and_case_warning(self):
        df = pd.DataFrame({"category": ["Books", " books ", "BOOKS"]})
        result = analyze_dataframe(df)
        self.assertEqual(result["column_checks"][0]["leading_trailing_whitespace_rows"], 1)
        self.assertTrue(result["column_checks"][0]["possible_case_inconsistency"])

    def test_empty_data(self):
        result = analyze_dataframe(pd.DataFrame({"a": pd.Series(dtype="string")}))
        self.assertEqual(result["summary"]["rows"], 0)
        self.assertEqual(result["column_checks"][0]["missing_pct"], 0)

    def test_key_validation(self):
        with self.assertRaisesRegex(ValueError, "Key columns not found"):
            analyze_dataframe(pd.DataFrame({"a": [1]}), ["missing"])

    def test_outlier_detection(self):
        df = pd.DataFrame({"revenue": [10, 10, 11, 12, 1000]})
        result = analyze_dataframe(df)
        self.assertEqual(result["column_checks"][0]["numeric_outliers_iqr"], 1)


if __name__ == "__main__":
    unittest.main()
