"""Core building blocks for an AI-powered Spotify SQL learning platform.

Every function is intentionally small and heavily documented so learners can see
how each feature works and what output it produces.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from statistics import mean
from typing import Any
from zipfile import ZipFile


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


# Feature 7: Active local analytics platform bootstrapped from archive.zip.
# Language usage:
# - Python handles file I/O (zip + CSV parsing) and application flow.
# - SQLite SQL creates tables/views and powers query execution.
ARCHIVE_TABLE_SQL = {
    "spotify_data clean.csv": """
        CREATE TABLE IF NOT EXISTS spotify_data_clean (
            track_id TEXT,
            track_name TEXT,
            track_number INTEGER,
            track_popularity INTEGER,
            explicit TEXT,
            artist_name TEXT,
            artist_popularity REAL,
            artist_followers INTEGER,
            artist_genres TEXT,
            album_id TEXT,
            album_name TEXT,
            album_release_date TEXT,
            album_total_tracks INTEGER,
            album_type TEXT,
            track_duration_min REAL
        );
    """,
    "track_data_final.csv": """
        CREATE TABLE IF NOT EXISTS track_data_final (
            track_id TEXT,
            track_name TEXT,
            track_number INTEGER,
            track_popularity INTEGER,
            track_duration_ms INTEGER,
            explicit TEXT,
            artist_name TEXT,
            artist_popularity REAL,
            artist_followers INTEGER,
            artist_genres TEXT,
            album_id TEXT,
            album_name TEXT,
            album_release_date TEXT,
            album_total_tracks INTEGER,
            album_type TEXT
        );
    """,
}


def _create_archive_tables(conn: sqlite3.Connection) -> None:
    """Create SQL tables that receive rows from archive.zip CSV files."""

    for ddl in ARCHIVE_TABLE_SQL.values():
        conn.execute(ddl)

    # This view normalizes fields used by analytics queries so downstream SQL
    # always targets one stable dataset.
    conn.execute(
        """
        CREATE VIEW IF NOT EXISTS v_track_analytics AS
        SELECT
            COALESCE(t.track_id, s.track_id) AS track_id,
            COALESCE(NULLIF(t.track_name, ''), NULLIF(s.track_name, '')) AS track_name,
            COALESCE(t.artist_name, s.artist_name) AS artist_name,
            COALESCE(t.album_name, s.album_name) AS album_name,
            COALESCE(t.track_popularity, s.track_popularity) AS track_popularity,
            COALESCE(t.artist_popularity, s.artist_popularity) AS artist_popularity,
            COALESCE(t.artist_followers, s.artist_followers) AS artist_followers,
            COALESCE(t.explicit, s.explicit) AS explicit,
            COALESCE(t.album_release_date, s.album_release_date) AS album_release_date
        FROM track_data_final t
        LEFT JOIN spotify_data_clean s ON s.track_id = t.track_id
        UNION ALL
        SELECT
            s.track_id,
            s.track_name,
            s.artist_name,
            s.album_name,
            s.track_popularity,
            s.artist_popularity,
            s.artist_followers,
            s.explicit,
            s.album_release_date
        FROM spotify_data_clean s
        WHERE NOT EXISTS (
            SELECT 1 FROM track_data_final t WHERE t.track_id = s.track_id
        );
        """
    )
    conn.commit()


def _load_csv_from_zip(
    conn: sqlite3.Connection,
    archive_path: str,
    csv_name: str,
    table_name: str,
) -> int:
    """Load one CSV file from zip into a SQLite table and return inserted row count."""

    with ZipFile(archive_path) as zf:
        with zf.open(csv_name) as raw_file:
            text_file = (line.decode("utf-8-sig") for line in raw_file)
            reader = csv.DictReader(text_file)
            if not reader.fieldnames:
                return 0

            columns = [col.strip() for col in reader.fieldnames]
            placeholders = ", ".join("?" for _ in columns)
            quoted_columns = ", ".join(f'"{col}"' for col in columns)
            sql = f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES ({placeholders})'

            inserted = 0
            batch: list[tuple[Any, ...]] = []
            for row in reader:
                batch.append(tuple(row.get(col) for col in columns))
                if len(batch) >= 2000:
                    conn.executemany(sql, batch)
                    inserted += len(batch)
                    batch.clear()

            if batch:
                conn.executemany(sql, batch)
                inserted += len(batch)
            conn.commit()
            return inserted


def bootstrap_active_platform(archive_path: str, db_path: str) -> dict[str, int]:
    """Build a runnable local analytics database from archive.zip.

    Step-by-step feature build:
    1) Create SQL tables for raw Spotify CSV datasets.
    2) Load both CSV files from the zip archive into SQLite tables.
    3) Expose one analytics-ready SQL view for dashboards and NL queries.
    """

    with closing(sqlite3.connect(db_path)) as conn:
        _create_archive_tables(conn)
        conn.execute("DELETE FROM spotify_data_clean;")
        conn.execute("DELETE FROM track_data_final;")
        conn.commit()

        spotify_rows = _load_csv_from_zip(conn, archive_path, "spotify_data clean.csv", "spotify_data_clean")
        track_rows = _load_csv_from_zip(conn, archive_path, "track_data_final.csv", "track_data_final")
        return {"spotify_data_clean": spotify_rows, "track_data_final": track_rows}


def nl_to_sql_active(question: str) -> str:
    """Translate common analytics questions into SQLite SQL for archive-backed data."""

    q = question.lower().strip()

    if "top" in q and ("popular" in q or "popularity" in q):
        return (
            "SELECT track_name, artist_name, track_popularity "
            "FROM v_track_analytics "
            "WHERE track_name IS NOT NULL "
            "ORDER BY track_popularity DESC "
            "LIMIT 10;"
        )
    if "explicit" in q:
        return (
            "SELECT explicit, COUNT(*) AS track_count "
            "FROM v_track_analytics "
            "GROUP BY explicit "
            "ORDER BY track_count DESC;"
        )
    if "artist" in q and "follower" in q:
        return (
            "SELECT artist_name, MAX(artist_followers) AS followers "
            "FROM v_track_analytics "
            "WHERE artist_name IS NOT NULL "
            "GROUP BY artist_name "
            "ORDER BY followers DESC "
            "LIMIT 10;"
        )
    return (
        "SELECT 'Unsupported question. Try: top tracks by popularity, explicit breakdown, or top artists by followers.' AS message;"
    )


def run_active_query(db_path: str, question: str) -> list[dict[str, Any]]:
    """Execute a natural-language analytics question against the active platform."""

    sql = nl_to_sql_active(question)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql).fetchall()
    return [dict(row) for row in rows]


def main() -> None:
    """CLI entrypoint that runs the platform as an active local analytics app."""

    parser = argparse.ArgumentParser(description="Bootstrap and query the Spotifysql active platform.")
    parser.add_argument(
        "--archive",
        default="archive.zip",
        help="Path to archive.zip containing spotify_data clean.csv and track_data_final.csv.",
    )
    parser.add_argument(
        "--db",
        default="spotifysql.db",
        help="Path to SQLite database file used by the active platform.",
    )
    parser.add_argument(
        "--question",
        default="top tracks by popularity",
        help="Natural-language analytics question to run after data load.",
    )
    args = parser.parse_args()

    # Step 1: Build tables + load zip data into SQLite.
    counts = bootstrap_active_platform(args.archive, args.db)
    print(f"Loaded rows: {counts}")

    # Step 2: Convert NL question to SQL and execute analytics query.
    rows = run_active_query(args.db, args.question)
    print(f"Question: {args.question}")
    for row in rows[:10]:
        print(row)


if __name__ == "__main__":
    main()
