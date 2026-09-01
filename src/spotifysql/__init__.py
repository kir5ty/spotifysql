"""Public API for spotifysql learning components."""

from .platform import (
    DashboardQuery,
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

__all__ = [
    "DashboardQuery",
    "warehouse_schema_sql",
    "upload_instruction",
    "nl_to_sql",
    "nl_to_sql_active",
    "dashboard_queries",
    "automated_insights",
    "query_performance_summary",
    "trivia_question",
    "bootstrap_active_platform",
    "run_active_query",
]
