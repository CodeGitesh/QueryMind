"""
Tests for the result classifier.
"""
import pytest
from app.core.result_classifier import classify_result, ResultType


def test_scalar_single_cell():
    rtype, config = classify_result(["count"], [[42]])
    assert rtype == ResultType.SCALAR
    assert config["type"] == "scalar"
    assert config["value"] == 42


def test_timeseries_with_date_column():
    rows = [["2024-01", 1000], ["2024-02", 1500], ["2024-03", 1200]]
    rtype, config = classify_result(["month", "revenue"], rows)
    assert rtype == ResultType.TIMESERIES
    assert config["type"] == "line"
    assert config["x_key"] == "month"


def test_comparison_two_cols():
    rows = [["Electronics", 50000], ["Clothing", 30000], ["Books", 15000]]
    rtype, config = classify_result(["category", "revenue"], rows)
    assert rtype == ResultType.COMPARISON
    assert config["type"] == "bar"
    assert config["x_key"] == "category"
    assert config["y_key"] == "revenue"


def test_table_multi_column():
    columns = ["id", "name", "email", "country", "total"]
    rows = [[1, "Alice", "a@b.com", "USA", 9999.99]]
    rtype, config = classify_result(columns, rows)
    assert rtype == ResultType.TABLE
    assert config["type"] == "table"


def test_empty_rows_returns_table():
    rtype, config = classify_result(["col1", "col2"], [])
    assert rtype == ResultType.TABLE


def test_timeseries_with_ordered_at_column():
    rows = [["2024-01-01", 100], ["2024-01-02", 200]]
    rtype, config = classify_result(["ordered_at", "count"], rows)
    assert rtype == ResultType.TIMESERIES
