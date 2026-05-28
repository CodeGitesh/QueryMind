"""
System prompt builder for the NL-to-SQL agent.
Injects only the relevant tables (not all) to avoid context overflow.
"""
from __future__ import annotations

from app.core.schema_selector import TableMatch

_RULES = """
RULES (STRICT — violations cause query rejection):
1. Output ONLY a valid SQL SELECT statement. No explanations, no markdown, no backticks.
2. Never use INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE.
3. Never access system tables: information_schema, pg_catalog, sys.
4. Always qualify table names with the schema prefix (e.g., ecommerce.customers).
5. Always include a LIMIT clause (max 1000 rows).
6. Use proper PostgreSQL syntax.
7. If the question cannot be answered with the available tables, output: CANNOT_ANSWER
""".strip()

_FORMAT = """
OUTPUT FORMAT: Return exactly one thing — the raw SQL query. Nothing else.
If uncertain about a column name, use the closest matching column from the schema.
Do not add any prefix like "```sql" or "Answer:".
""".strip()


def build_system_prompt(
    schema_name: str,
    relevant_tables: list[TableMatch],
    full_schema_json: dict,
) -> str:
    """
    Build the system prompt for the NL-to-SQL agent.

    Args:
        schema_name: e.g. "ecommerce"
        relevant_tables: top-K semantically relevant TableMatch objects
        full_schema_json: schema introspection result (tables with columns)
    """
    table_names = {t.table for t in relevant_tables}
    dialect = "PostgreSQL 15"

    # Build schema context — only for relevant tables
    schema_lines: list[str] = []
    tables_info = full_schema_json.get("tables", {})

    for table_name, table_data in tables_info.items():
        if table_name not in table_names:
            continue
        cols = table_data.get("columns", [])
        col_defs = ", ".join(
            f"{c['name']} ({c['type']})" for c in cols
        )
        fks = table_data.get("foreign_keys", [])
        fk_str = ""
        if fks:
            fk_parts = [f"{fk['column']} → {fk['referred_table']}.{fk['referred_column']}" for fk in fks]
            fk_str = f"\n  Foreign keys: {', '.join(fk_parts)}"
        row_count = table_data.get("row_count", "?")
        schema_lines.append(
            f"  TABLE {schema_name}.{table_name} (~{row_count} rows):\n"
            f"    Columns: {col_defs}{fk_str}"
        )

    schema_block = "\n".join(schema_lines) if schema_lines else "  (no schema available)"

    return f"""You are QueryMind, an expert {dialect} query generator.
Database dialect: {dialect}
Active schema: {schema_name}

AVAILABLE TABLES (most relevant to this query):
{schema_block}

{_RULES}

{_FORMAT}"""


def build_error_correction_message(failed_sql: str, error: str, attempt: int) -> str:
    """Message to append to conversation when a query fails (self-healing)."""
    return (
        f"That query failed on attempt {attempt} with this error:\n"
        f"Error: {error}\n"
        f"Failed SQL: {failed_sql}\n\n"
        "Please analyze the error carefully and write a corrected SQL query. "
        "Return ONLY the corrected SQL, nothing else."
    )
