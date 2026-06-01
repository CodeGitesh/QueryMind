"""
Tests for the SQL sanitizer — critical security component.
"""
import pytest
from app.utils.sanitizer import validate_sql, SQLInjectionError, sanitize_column_name


class TestValidateSQL:
    def test_valid_select(self):
        sql = "SELECT id, name FROM ecommerce.customers"
        result = validate_sql(sql)
        assert "SELECT" in result.upper()

    def test_auto_appends_limit(self):
        sql = "SELECT * FROM ecommerce.customers"
        result = validate_sql(sql)
        assert "LIMIT 1000" in result

    def test_existing_limit_preserved(self):
        sql = "SELECT * FROM ecommerce.customers LIMIT 50"
        result = validate_sql(sql)
        assert "LIMIT 50" in result
        assert "LIMIT 1000" not in result

    def test_blocks_insert(self):
        with pytest.raises(SQLInjectionError):
            validate_sql("INSERT INTO users VALUES (1, 'evil')")

    def test_blocks_update(self):
        with pytest.raises(SQLInjectionError):
            validate_sql("UPDATE users SET password='hacked'")

    def test_blocks_delete(self):
        with pytest.raises(SQLInjectionError):
            validate_sql("DELETE FROM users")

    def test_blocks_drop(self):
        with pytest.raises(SQLInjectionError):
            validate_sql("DROP TABLE users")

    def test_blocks_sql_comments(self):
        with pytest.raises(SQLInjectionError):
            validate_sql("SELECT * FROM users -- comment")

    def test_blocks_stacked_queries(self):
        with pytest.raises(SQLInjectionError):
            validate_sql("SELECT * FROM users; DROP TABLE users")

    def test_blocks_union_injection(self):
        with pytest.raises(SQLInjectionError):
            validate_sql("SELECT * FROM users UNION SELECT * FROM passwords")

    def test_blocks_system_schema(self):
        with pytest.raises(SQLInjectionError):
            validate_sql("SELECT * FROM information_schema.tables")

    def test_blocks_pg_catalog(self):
        with pytest.raises(SQLInjectionError):
            validate_sql("SELECT * FROM pg_catalog.pg_tables")

    def test_blocks_empty_query(self):
        with pytest.raises(SQLInjectionError):
            validate_sql("")

    def test_allows_with_cte(self):
        sql = "WITH cte AS (SELECT id FROM orders) SELECT * FROM cte"
        result = validate_sql(sql)
        assert result  # Should not raise

    def test_semicolon_at_end_allowed(self):
        sql = "SELECT * FROM customers;"
        # Trailing semicolon should be OK (not stacked query)
        result = validate_sql(sql)
        assert result


class TestSanitizeColumnName:
    def test_normal_name(self):
        assert sanitize_column_name("customer_id") == "customer_id"

    def test_spaces_to_underscore(self):
        assert sanitize_column_name("Customer Name") == "customer_name"

    def test_special_chars_removed(self):
        assert sanitize_column_name("price ($)") == "price___"

    def test_leading_digit_prefixed(self):
        assert sanitize_column_name("123abc") == "col_123abc"

    def test_empty_string(self):
        assert sanitize_column_name("") == "col_unknown"
