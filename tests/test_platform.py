import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from spotifysql.platform import (
    automated_insights,
    bootstrap_active_platform,
    dashboard_queries,
    nl_to_sql,
    nl_to_sql_active,
    query_performance_summary,
    run_active_query,
    trivia_question,
    upload_instruction,
    warehouse_schema_sql,
)


class PlatformTests(unittest.TestCase):
    ARCHIVE_PATH = str(Path(__file__).resolve().parents[1] / "archive.zip")

    def test_schema_contains_core_tables(self):
        ddl = warehouse_schema_sql()
        self.assertIn("CREATE TABLE IF NOT EXISTS fact_streaming", ddl)
        self.assertIn("CHECK (release_year BETWEEN 2009 AND 2025)", ddl)

    def test_upload_instruction_validates_table(self):
        sql = upload_instruction("/tmp/s.csv", "dim_artist")
        self.assertIn("\\copy dim_artist", sql)
        with self.assertRaises(ValueError):
            upload_instruction("/tmp/s.csv", "other_table")

    def test_nl_to_sql_top_streams(self):
        sql = nl_to_sql("show top tracks by streams")
        self.assertIn("ORDER BY total_streams DESC", sql)

    def test_dashboard_queries_present(self):
        queries = dashboard_queries()
        self.assertGreaterEqual(len(queries), 2)

    def test_automated_insights(self):
        insights = automated_insights([
            {"label": "Jan", "value": 10},
            {"label": "Feb", "value": 20},
        ])
        self.assertEqual(len(insights), 3)
        self.assertIn("Peak value", insights[0])

    def test_query_performance_summary(self):
        summary = query_performance_summary([
            {"planning_time_ms": 1.1, "execution_time_ms": 3.2},
            {"planning_time_ms": 0.5, "execution_time_ms": 4.3},
        ])
        self.assertEqual(summary["total_time_ms"], 9.1)

    def test_trivia_question(self):
        question = trivia_question([
            {"track_name": "Track A", "total_streams": 500},
            {"track_name": "Track B", "total_streams": 100},
        ])
        self.assertEqual(question["answer"], "Track A")

    def test_archive_bootstrap_loads_rows(self):
        with TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "platform.db")
            counts = bootstrap_active_platform(self.ARCHIVE_PATH, db_path)
            self.assertGreater(counts["spotify_data_clean"], 0)
            self.assertGreater(counts["track_data_final"], 0)

    def test_active_nl_query_returns_rows(self):
        with TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "platform.db")
            bootstrap_active_platform(self.ARCHIVE_PATH, db_path)
            rows = run_active_query(db_path, "top tracks by popularity")
            self.assertGreater(len(rows), 0)
            self.assertIn("track_name", rows[0])

    def test_active_nl_to_sql_contains_view(self):
        sql = nl_to_sql_active("show explicit breakdown")
        self.assertIn("FROM v_track_analytics", sql)


if __name__ == "__main__":
    unittest.main()
