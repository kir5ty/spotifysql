"""Core building blocks for an AI-powered Spotify SQL learning platform.

Every function is intentionally small and heavily documented so learners can see
how each feature works and what output it produces.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any


# Feature 1: PostgreSQL warehouse schema for Spotify data (2009-2025).
# This SQL creates dimension + fact tables that are easy to query for analytics.
WAREHOUSE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS dim_artist (
    artist_id TEXT PRIMARY KEY,
    artist_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_album (
    album_id TEXT PRIMARY KEY,
    album_name TEXT NOT NULL,
    release_year INTEGER NOT NULL CHECK (release_year BETWEEN 2009 AND 2025)
);

CREATE TABLE IF NOT EXISTS dim_track (
    track_id TEXT PRIMARY KEY,
    track_name TEXT NOT NULL,
    artist_id TEXT NOT NULL REFERENCES dim_artist(artist_id),
    album_id TEXT NOT NULL REFERENCES dim_album(album_id),
    duration_ms INTEGER NOT NULL CHECK (duration_ms > 0)
);

CREATE TABLE IF NOT EXISTS fact_streaming (
    stream_date DATE NOT NULL,
    track_id TEXT NOT NULL REFERENCES dim_track(track_id),
    streams BIGINT NOT NULL CHECK (streams >= 0),
    popularity INTEGER NOT NULL CHECK (popularity BETWEEN 0 AND 100),
    energy NUMERIC(4,3) NOT NULL CHECK (energy BETWEEN 0 AND 1),
    danceability NUMERIC(4,3) NOT NULL CHECK (danceability BETWEEN 0 AND 1),
    PRIMARY KEY (stream_date, track_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_streaming_track ON fact_streaming(track_id);
CREATE INDEX IF NOT EXISTS idx_fact_streaming_date ON fact_streaming(stream_date);
""".strip()


@dataclass(frozen=True)
class DashboardQuery:
    """Represents one SQL query that powers a dashboard chart."""

    title: str
    sql: str


def warehouse_schema_sql() -> str:
    """Return the PostgreSQL DDL used to build the Spotify warehouse."""

    return WAREHOUSE_SCHEMA_SQL


def upload_instruction(csv_path: str, target_table: str) -> str:
    """Return a safe COPY instruction string used during data loading.

    The output is a teaching aid: it shows the exact SQL command a user can run
    in psql to ingest a local CSV file into a selected table.
    """

    # We keep the allowed table names explicit to avoid generating SQL for
    # unexpected targets.
    allowed = {"dim_artist", "dim_album", "dim_track", "fact_streaming"}
    if target_table not in allowed:
        raise ValueError(f"Unsupported target_table: {target_table}")
    return (
        f"\\copy {target_table} FROM '{csv_path}' "
        "WITH (FORMAT csv, HEADER true, DELIMITER ',');"
    )


def nl_to_sql(question: str) -> str:
    """Translate common analytics questions to SQL.

    This is a deterministic rules-first translator so learners can inspect how
    natural-language phrases map to SQL patterns.
    """

    q = question.lower().strip()

    # Top songs by streams.
    if "top" in q and "stream" in q:
        return (
            "SELECT t.track_name, SUM(f.streams) AS total_streams "
            "FROM fact_streaming f "
            "JOIN dim_track t ON t.track_id = f.track_id "
            "GROUP BY t.track_name "
            "ORDER BY total_streams DESC "
            "LIMIT 10;"
        )

    # Average popularity over time.
    if "average" in q and "popularity" in q:
        return (
            "SELECT DATE_TRUNC('month', stream_date) AS month, "
            "AVG(popularity) AS avg_popularity "
            "FROM fact_streaming "
            "GROUP BY month "
            "ORDER BY month;"
        )

    # Fallback so the system remains transparent when it cannot infer intent.
    return "SELECT 'Unsupported question. Try asking about top streams or average popularity.' AS message;"


def dashboard_queries() -> list[DashboardQuery]:
    """Return curated SQL queries used by interactive dashboards."""

    return [
        DashboardQuery(
            title="Monthly Stream Trend",
            sql=(
                "SELECT DATE_TRUNC('month', stream_date) AS month, "
                "SUM(streams) AS monthly_streams "
                "FROM fact_streaming GROUP BY month ORDER BY month;"
            ),
        ),
        DashboardQuery(
            title="Top 10 Tracks",
            sql=(
                "SELECT t.track_name, SUM(f.streams) AS total_streams "
                "FROM fact_streaming f JOIN dim_track t ON t.track_id = f.track_id "
                "GROUP BY t.track_name ORDER BY total_streams DESC LIMIT 10;"
            ),
        ),
    ]


def automated_insights(rows: list[dict[str, Any]]) -> list[str]:
    """Generate simple textual insights from aggregated query outputs.

    Input format example: [{"label": "2025-01", "value": 1200}, ...]
    Output: short insights that can be rendered directly in a UI panel.
    """

    if not rows:
        return ["No data available yet. Upload Spotify records to generate insights."]

    values = [float(r["value"]) for r in rows]
    labels = [str(r["label"]) for r in rows]
    max_index = values.index(max(values))
    min_index = values.index(min(values))

    return [
        f"Peak value is {values[max_index]:.2f} at {labels[max_index]}.",
        f"Lowest value is {values[min_index]:.2f} at {labels[min_index]}.",
        f"Average value across the series is {mean(values):.2f}.",
    ]


def query_performance_summary(explain_rows: list[dict[str, Any]]) -> dict[str, float]:
    """Summarize query-performance metrics from EXPLAIN ANALYZE output.

    Expected row format includes keys such as planning_time_ms and execution_time_ms.
    The result is a compact dictionary suitable for performance comparison charts.
    """

    if not explain_rows:
        return {"planning_time_ms": 0.0, "execution_time_ms": 0.0, "total_time_ms": 0.0}

    planning = sum(float(row.get("planning_time_ms", 0.0)) for row in explain_rows)
    execution = sum(float(row.get("execution_time_ms", 0.0)) for row in explain_rows)
    return {
        "planning_time_ms": round(planning, 3),
        "execution_time_ms": round(execution, 3),
        "total_time_ms": round(planning + execution, 3),
    }


def trivia_question(top_tracks: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a simple gamified trivia question from analytics data.

    Input rows should include track_name and total_streams.
    Output includes a prompt, choices, and the correct answer.
    """

    if len(top_tracks) < 2:
        raise ValueError("Need at least two tracks to build trivia choices")

    ordered = sorted(top_tracks, key=lambda row: float(row["total_streams"]), reverse=True)
    answer = ordered[0]["track_name"]
    choices = [ordered[0]["track_name"], ordered[1]["track_name"]]

    return {
        "prompt": "Which track has the highest streams in this dataset?",
        "choices": choices,
        "answer": answer,
    }
