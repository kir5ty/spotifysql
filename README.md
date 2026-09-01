# spotifysql

A minimal starter implementation for an **AI-powered music analytics platform** built around a PostgreSQL Spotify warehouse.

## Included features

- PostgreSQL warehouse schema for Spotify data (2009-2025)
- Rule-based natural-language-to-SQL translator
- Dashboard SQL query catalog
- Automated insight generation from aggregated query results
- Query-performance summary helper for `EXPLAIN ANALYZE` metrics
- Basic gamified trivia question generator from analytics output

## Code layout

- `/home/runner/work/spotifysql/spotifysql/src/spotifysql/platform.py` - core platform features
- `/home/runner/work/spotifysql/spotifysql/tests/test_platform.py` - focused tests

## Run tests

```bash
cd /home/runner/work/spotifysql/spotifysql
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Note on learning-oriented comments

Per requirement, each feature in `platform.py` includes explanatory comments/docstrings that describe what the code does and what outputs it produces.
