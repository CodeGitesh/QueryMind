"""
Tests for the self-healing loop.
"""
from __future__ import annotations
import pytest
from app.core.self_healer import run_self_healing_loop, HealingResult


@pytest.mark.asyncio
async def test_success_on_first_attempt():
    """Query succeeds on first try — no healing needed."""
    async def execute_ok(sql: str):
        return (["id", "name"], [[1, "Alice"], [2, "Bob"]])

    async def generate(conv):
        return "SELECT * FROM customers"

    result = await run_self_healing_loop(
        initial_sql="SELECT * FROM customers",
        execute_sql=execute_ok,
        generate_sql=generate,
        conversation_history=[],
        max_attempts=3,
    )

    assert result.success is True
    assert result.total_attempts == 1
    assert result.was_healed is False
    assert len(result.rows) == 2


@pytest.mark.asyncio
async def test_heals_on_second_attempt():
    """First query fails, second succeeds — self-healing triggered."""
    call_count = [0]

    async def execute_maybe(sql: str):
        call_count[0] += 1
        if call_count[0] == 1:
            raise Exception("column does not exist")
        return (["total"], [[42]])

    async def generate(conv):
        return "SELECT COUNT(*) AS total FROM customers"

    result = await run_self_healing_loop(
        initial_sql="SELECT bad_col FROM customers",
        execute_sql=execute_maybe,
        generate_sql=generate,
        conversation_history=[{"role": "user", "content": "count customers"}],
        max_attempts=3,
    )

    assert result.success is True
    assert result.total_attempts == 2
    assert result.was_healed is True


@pytest.mark.asyncio
async def test_exhausts_all_attempts():
    """All 3 attempts fail — returns failure result."""
    async def execute_always_fails(sql: str):
        raise Exception("always fails")

    async def generate(conv):
        return "SELECT * FROM nonexistent"

    result = await run_self_healing_loop(
        initial_sql="SELECT * FROM bad_table",
        execute_sql=execute_always_fails,
        generate_sql=generate,
        conversation_history=[],
        max_attempts=3,
    )

    assert result.success is False
    assert result.total_attempts == 3
    assert len(result.attempts) == 3
    assert all(not a.success for a in result.attempts)


@pytest.mark.asyncio
async def test_error_messages_captured():
    """Verify each attempt's error message is recorded."""
    errors = ["syntax error", "column missing", "table not found"]
    call_count = [0]

    async def execute_with_errors(sql: str):
        e = errors[call_count[0] % len(errors)]
        call_count[0] += 1
        raise Exception(e)

    async def generate(conv):
        return f"SELECT * FROM table_{call_count[0]}"

    result = await run_self_healing_loop(
        initial_sql="SELECT * FROM bad",
        execute_sql=execute_with_errors,
        generate_sql=generate,
        conversation_history=[],
        max_attempts=3,
    )

    assert result.success is False
    assert len(result.attempts) == 3
    for a in result.attempts:
        assert a.error is not None
