# spotifysql

A minimal starter implementation for an **AI-powered music analytics platform** built around a PostgreSQL Spotify warehouse.

## Included features

- PostgreSQL warehouse schema for Spotify data (2009-2025)
- Rule-based natural-language-to-SQL translator
- Dashboard SQL query catalog
- Automated insight generation from aggregated query results
- Query-performance summary helper for `EXPLAIN ANALYZE` metrics
- Basic gamified trivia question generator from analytics output
- Active SQLite platform bootstrap that loads `archive.zip` and runs live analytics questions

## Code layout

- `/home/runner/work/spotifysql/spotifysql/src/spotifysql/platform.py` - core platform features
- `/home/runner/work/spotifysql/spotifysql/tests/test_platform.py` - focused tests

## Run tests

```bash
cd /home/runner/work/spotifysql/spotifysql
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Run the active platform from `archive.zip`

```bash
cd /home/runner/work/spotifysql/spotifysql
PYTHONPATH=src python -m spotifysql.platform \
  --archive /home/runner/work/spotifysql/spotifysql/archive.zip \
  --db /home/runner/work/spotifysql/spotifysql/spotifysql.db \
  --question "top tracks by popularity"
```

What this does:
- Uses **Python** to extract and parse CSV files from the zip archive.
- Uses **SQLite SQL** to create tables and an analytics view.
- Executes a natural-language question by translating it to SQL and printing results.

## Note on learning-oriented comments

Per requirement, each feature in `platform.py` includes explanatory comments/docstrings that describe what the code does and what outputs it produces.
