"""
Self-healing agent loop.
On SQL execution failure, injects error context back into conversation
and retries — up to MAX_RETRY_ATTEMPTS times.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

import structlog

from app.config import settings
from app.core.prompt_builder import build_error_correction_message

log = structlog.get_logger(__name__)


@dataclass
class AttemptRecord:
    attempt: int
    sql: str
    error: str | None
    success: bool
    duration_ms: float


@dataclass
class HealingResult:
    success: bool
    final_sql: str
    rows: list[list[Any]]
    columns: list[str]
    attempts: list[AttemptRecord]
    total_attempts: int

    @property
    def was_healed(self) -> bool:
        return self.total_attempts > 1 and self.success


# Type alias for the async SQL executor callable
SQLExecutor = Callable[[str], Coroutine[Any, Any, tuple[list[str], list[list[Any]]]]]
SQLGenerator = Callable[[list[dict]], Coroutine[Any, Any, str]]


async def run_self_healing_loop(
    initial_sql: str,
    execute_sql: SQLExecutor,
    generate_sql: SQLGenerator,
    conversation_history: list[dict],
    max_attempts: int | None = None,
) -> HealingResult:
    """
    Execute SQL with self-healing retry loop.

    Args:
        initial_sql: First generated SQL from the agent
        execute_sql: Async callable that executes SQL → (columns, rows)
        generate_sql: Async callable that takes conversation history → new SQL
        conversation_history: Mutable list of {role, content} messages
        max_attempts: Override max retries (default: settings.MAX_RETRY_ATTEMPTS)

    Returns:
        HealingResult with success status, final SQL, data, and attempt records
    """
    max_attempts = max_attempts or settings.MAX_RETRY_ATTEMPTS
    attempts: list[AttemptRecord] = []
    current_sql = initial_sql

    for attempt_num in range(1, max_attempts + 1):
        log.info(
            "Self-healer attempt",
            attempt=attempt_num,
            max=max_attempts,
            sql_preview=current_sql[:100],
        )

        start = time.perf_counter()
        try:
            columns, rows = await execute_sql(current_sql)
            duration_ms = (time.perf_counter() - start) * 1000

            record = AttemptRecord(
                attempt=attempt_num,
                sql=current_sql,
                error=None,
                success=True,
                duration_ms=round(duration_ms, 2),
            )
            attempts.append(record)

            log.info(
                "Query succeeded",
                attempt=attempt_num,
                rows=len(rows),
                duration_ms=record.duration_ms,
            )

            return HealingResult(
                success=True,
                final_sql=current_sql,
                rows=rows,
                columns=columns,
                attempts=attempts,
                total_attempts=attempt_num,
            )

        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            error_str = str(exc)

            record = AttemptRecord(
                attempt=attempt_num,
                sql=current_sql,
                error=error_str,
                success=False,
                duration_ms=round(duration_ms, 2),
            )
            attempts.append(record)

            log.warning(
                "Query failed — self-healer triggered",
                attempt=attempt_num,
                error=error_str[:200],
            )

            if attempt_num == max_attempts:
                break  # No more retries

            # Inject error into conversation history for the LLM to fix
            correction_msg = build_error_correction_message(
                failed_sql=current_sql,
                error=error_str,
                attempt=attempt_num,
            )
            conversation_history.append({"role": "user", "content": correction_msg})

            # Generate a new (hopefully fixed) SQL
            try:
                current_sql = await generate_sql(conversation_history)
                conversation_history.append({"role": "assistant", "content": current_sql})
            except Exception as gen_exc:
                log.error("SQL generation failed during self-healing", error=str(gen_exc))
                break

    # All attempts exhausted
    log.error("Self-healer exhausted all attempts", attempts=len(attempts))
    return HealingResult(
        success=False,
        final_sql=current_sql,
        rows=[],
        columns=[],
        attempts=attempts,
        total_attempts=len(attempts),
    )
