"""
Result classifier: determines chart type from SQL query shape + result data.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any

import structlog

log = structlog.get_logger(__name__)

DATE_PATTERNS = re.compile(
    r"\b(date|time|timestamp|year|month|week|day|period|quarter|created_at|updated_at|ordered_at)\b",
    re.IGNORECASE,
)


class ResultType(str, Enum):
    SCALAR = "scalar"
    LIST = "list"
    TIMESERIES = "timeseries"
    COMPARISON = "comparison"
    TABLE = "table"


def classify_result(
    columns: list[str],
    rows: list[list[Any]],
    sql: str = "",
) -> tuple[ResultType, dict[str, Any]]:
    """
    Classify query results and return chart configuration.

    Returns:
        (ResultType, chart_config dict)
    """
    if not rows:
        return ResultType.TABLE, _table_config(columns, [])

    num_rows = len(rows)
    num_cols = len(columns)

    # ── SCALAR: single cell ────────────────────────────────────────────────────
    if num_rows == 1 and num_cols == 1:
        value = rows[0][0]
        label = columns[0].replace("_", " ").title()
        return ResultType.SCALAR, {
            "type": "scalar",
            "value": value,
            "label": label,
            "title": label,
        }

    # ── TIMESERIES: has a date/time column ────────────────────────────────────
    time_col = _find_time_column(columns)
    if time_col and num_cols >= 2:
        value_cols = [c for c in columns if c != time_col]
        return ResultType.TIMESERIES, {
            "type": "line",
            "x_key": time_col,
            "y_key": value_cols[0],
            "y_keys": value_cols,
            "title": f"{value_cols[0].replace('_', ' ').title()} Over Time",
        }

    # ── COMPARISON: two columns, one categorical, one numeric ────────────────
    if num_cols == 2:
        cat_col, num_col = _detect_categorical_numeric(columns, rows)
        if cat_col and num_col:
            if num_rows <= 10:
                chart_type = "bar"
            else:
                chart_type = "bar"
            return ResultType.COMPARISON, {
                "type": chart_type,
                "x_key": cat_col,
                "y_key": num_col,
                "title": f"{num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
            }

    # ── LIST: single numeric + single label column, many rows ────────────────
    if num_cols == 2 and num_rows > 1:
        return ResultType.LIST, {
            "type": "bar",
            "layout": "horizontal",
            "x_key": columns[1],
            "y_key": columns[0],
            "title": "Ranked Results",
        }

    # ── TABLE: fallback ───────────────────────────────────────────────────────
    return ResultType.TABLE, _table_config(columns, rows)


def _find_time_column(columns: list[str]) -> str | None:
    for col in columns:
        if DATE_PATTERNS.search(col):
            return col
    return None


def _detect_categorical_numeric(
    columns: list[str],
    rows: list[list[Any]],
) -> tuple[str | None, str | None]:
    """Return (categorical_column, numeric_column) or (None, None)."""
    if len(columns) != 2:
        return None, None

    c0, c1 = columns[0], columns[1]
    sample = rows[:10]

    def is_numeric(col_idx: int) -> bool:
        for row in sample:
            val = row[col_idx]
            if val is not None and not isinstance(val, (int, float)):
                try:
                    float(val)
                except (TypeError, ValueError):
                    return False
        return True

    col0_numeric = is_numeric(0)
    col1_numeric = is_numeric(1)

    if col1_numeric and not col0_numeric:
        return c0, c1
    if col0_numeric and not col1_numeric:
        return c1, c0
    if col1_numeric:
        return c0, c1
    return None, None


def _table_config(columns: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    return {
        "type": "table",
        "columns": columns,
        "title": "Query Results",
    }
