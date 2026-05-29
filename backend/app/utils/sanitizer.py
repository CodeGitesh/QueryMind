"""
SQL Injection prevention and query validation.
CRITICAL security layer — runs on EVERY query, no exceptions.
"""
from __future__ import annotations

import re
import structlog

log = structlog.get_logger(__name__)

# ── Custom exception ──────────────────────────────────────────────────────────

class SQLInjectionError(ValueError):
    """Raised when a query fails security validation."""
    def __init__(self, reason: str, query: str = "") -> None:
        self.reason = reason
        self.query = query
        super().__init__(f"Query blocked: {reason}")


# ── Patterns ──────────────────────────────────────────────────────────────────

# Non-SELECT statements (case-insensitive, word boundary)
_FORBIDDEN_STATEMENTS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|EXEC(?:UTE)?|GRANT|REVOKE|COPY|VACUUM|ANALYZE)\b",
    re.IGNORECASE,
)

# SQL comment starters
_COMMENTS = re.compile(r"(--|\/\*|\*\/)", re.IGNORECASE)

# Stacked queries (statement terminator not at very end)
_STACKED = re.compile(r";(?!\s*$)", re.IGNORECASE)

# UNION-based injection
_UNION = re.compile(r"\bUNION\s+(ALL\s+)?SELECT\b", re.IGNORECASE)

# System / internal schema access
_SYSTEM_SCHEMAS = re.compile(
    r"\b(information_schema|pg_catalog|pg_toast|sys|sysobjects|sqlite_master|sqlite_schema)\b",
    re.IGNORECASE,
)

# CSV injection: cells starting with formula characters
_CSV_INJECTION = re.compile(r'(?:^|,)\s*[=+\-@\t\r]', re.MULTILINE)

# Must start with SELECT (after stripping whitespace/WITH)
_VALID_START = re.compile(r"^\s*(WITH\s+\w|\bSELECT\b)", re.IGNORECASE)


def validate_sql(sql: str, client_ip: str = "unknown") -> str:
    """
    Validate and sanitize a SQL query string.
    Returns the (possibly modified) query if safe.
    Raises SQLInjectionError if blocked.
    """
    if not sql or not sql.strip():
        raise SQLInjectionError("Empty query", sql)

    stripped = sql.strip()

    # 1. Must start with SELECT or WITH
    if not _VALID_START.match(stripped):
        log.warning("Blocked non-SELECT query", ip=client_ip, query=stripped[:200])
        raise SQLInjectionError("Only SELECT statements are allowed", stripped)

    # 2. Block forbidden DML/DDL
    if _FORBIDDEN_STATEMENTS.search(stripped):
        match = _FORBIDDEN_STATEMENTS.search(stripped)
        log.warning("Blocked forbidden statement", ip=client_ip, keyword=match.group() if match else "?")
        raise SQLInjectionError(
            f"Statement contains forbidden keyword: {match.group() if match else 'unknown'}",
            stripped,
        )

    # 3. Block SQL comments
    if _COMMENTS.search(stripped):
        log.warning("Blocked query with SQL comments", ip=client_ip)
        raise SQLInjectionError("SQL comments are not allowed in queries", stripped)

    # 4. Block stacked queries
    if _STACKED.search(stripped):
        log.warning("Blocked stacked query", ip=client_ip)
        raise SQLInjectionError("Multiple statements (stacked queries) are not allowed", stripped)

    # 5. Block UNION injections
    if _UNION.search(stripped):
        log.warning("Blocked UNION-based injection attempt", ip=client_ip)
        raise SQLInjectionError("UNION SELECT patterns are not allowed", stripped)

    # 6. Block system table access
    if _SYSTEM_SCHEMAS.search(stripped):
        log.warning("Blocked system schema access", ip=client_ip)
        raise SQLInjectionError("Access to system schemas is not allowed", stripped)

    # 7. Enforce row limit — append LIMIT if missing
    sanitized = _enforce_row_limit(stripped)

    log.debug("Query passed sanitization", ip=client_ip)
    return sanitized


def _enforce_row_limit(sql: str, max_rows: int = 1000) -> str:
    """Append LIMIT 1000 to queries that don't already have a LIMIT clause."""
    limit_pattern = re.compile(r"\bLIMIT\s+\d+", re.IGNORECASE)
    if not limit_pattern.search(sql):
        # Remove trailing semicolon if present before appending
        cleaned = sql.rstrip().rstrip(";")
        return f"{cleaned} LIMIT {max_rows}"
    return sql


def sanitize_column_name(name: str) -> str:
    """Sanitize a column name for safe use in dynamic SQL."""
    # Remove non-alphanumeric/underscore chars, lowercase, strip leading digits
    clean = re.sub(r"[^a-z0-9_]", "_", name.lower())
    clean = re.sub(r"_+", "_", clean).strip("_")
    if clean and clean[0].isdigit():
        clean = "col_" + clean
    return clean or "col_unknown"


def validate_csv_cell(value: str) -> str:
    """Detect and neutralize CSV injection in cell values."""
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value
