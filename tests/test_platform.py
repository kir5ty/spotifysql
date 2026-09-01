import unittest

from spotifysql.platform import (
    automated_insights,
    dashboard_queries,
    nl_to_sql,
    query_performance_summary,
    trivia_question,
    upload_instruction,
    warehouse_schema_sql,
)


class PlatformTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
