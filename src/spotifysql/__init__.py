"""Public API for spotifysql learning components."""

from .platform import (
    DashboardQuery,
    automated_insights,
    dashboard_queries,
    nl_to_sql,
    query_performance_summary,
    trivia_question,
    upload_instruction,
    warehouse_schema_sql,
)

__all__ = [
    "DashboardQuery",
    "warehouse_schema_sql",
    "upload_instruction",
    "nl_to_sql",
    "dashboard_queries",
    "automated_insights",
    "query_performance_summary",
    "trivia_question",
]
