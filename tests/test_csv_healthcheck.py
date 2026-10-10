import tempfile
import unittest
from pathlib import Path

from csv_healthcheck import CSVProfileError, main, profile_csv


class CSVHealthcheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "data.csv"

    def test_profile_missing_duplicates_and_numeric_stats(self):
        self.path.write_text(
            "name,score,team\nAda,10,A\nBo,20,B\nBo,20,B\nCy, ,A\n",
            encoding="utf-8",
        )
        result = profile_csv(self.path)
        self.assertEqual(result["rows"], 4)
        self.assertEqual(result["duplicate_rows"], 1)
        self.assertEqual(result["missing_by_column"]["score"], 1)
        self.assertEqual(result["numeric_columns"]["score"], {
            "count": 3, "min": 10.0, "max": 20.0, "mean": 16.6667
        })
        self.assertNotIn("name", result["numeric_columns"])

    def test_rejects_ragged_rows(self):
        self.path.write_text("a,b\n1\n", encoding="utf-8")
        with self.assertRaisesRegex(CSVProfileError, "record 1"):
            profile_csv(self.path)

    def test_rejects_duplicate_headers(self):
        self.path.write_text("a,a\n1,2\n", encoding="utf-8")
        with self.assertRaisesRegex(CSVProfileError, "unique"):
            profile_csv(self.path)

    def test_mixed_and_nonfinite_columns_are_not_numeric(self):
        self.path.write_text("mixed,nonfinite\n1,2\nx,inf\n", encoding="utf-8")
        self.assertEqual(profile_csv(self.path)["numeric_columns"], {})

    def test_large_finite_values_have_stable_mean(self):
        self.path.write_text("value\n1e308\n1e308\n", encoding="utf-8")
        self.assertEqual(profile_csv(self.path)["numeric_columns"]["value"]["mean"], 1e308)

    def test_cli_exit_status_for_bad_input(self):
        self.path.write_text("", encoding="utf-8")
        self.assertEqual(main([str(self.path)]), 1)


if __name__ == "__main__":
    unittest.main()
