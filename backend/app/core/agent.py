"""
LangChain agent (LCEL-based, NOT deprecated AgentExecutor).
Uses Groq as primary LLM with Gemini fallback.
Tools: execute_sql, get_schema, describe_table.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncIterator

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from app.config import settings
from app.core.prompt_builder import build_system_prompt
from app.core.result_classifier import classify_result
from app.core.schema_selector import schema_selector
from app.core.self_healer import run_self_healing_loop
from app.core.tools import get_db_tools
from app.utils.sanitizer import SQLInjectionError, validate_sql

log = structlog.get_logger(__name__)


def _build_llm():
    """Build primary (Groq) LLM with Gemini fallback."""
    if settings.GROQ_API_KEY:
        from langchain_groq import ChatGroq  # type: ignore
        return ChatGroq(
            model=settings.GROQ_MODEL,
            temperature=settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
            api_key=settings.GROQ_API_KEY,
        )
    elif settings.GOOGLE_API_KEY:
        log.warning("Groq API key missing — falling back to Gemini")
        from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
        return ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            temperature=0.0,
            google_api_key=settings.GOOGLE_API_KEY,
        )
    else:
        raise RuntimeError(
            "No LLM API key configured. Set GROQ_API_KEY or GOOGLE_API_KEY in .env"
        )


class QueryMindAgent:
    """
    NL-to-SQL agent using LCEL pipeline.
    Not using deprecated AgentExecutor — uses direct LLM call + tool wrappers.
    """

    def __init__(self) -> None:
        self._llm = None

    def _get_llm(self):
        # lazy loading the llm so it doesnt crash if keys are missing on boot
        if self._llm is None:
            self._llm = _build_llm()
            # print("llm initialized")
        return self._llm

    async def run(
        self,
        query: str,
        schema_name: str,
        db_execute: Any,
        schema_info: dict,
        stream_callback: Any = None,
    ) -> dict[str, Any]:
        """
        Execute a natural language query end-to-end.

        Returns a structured response dict.
        """
        start_time = time.perf_counter()

        async def _emit(step: str) -> None:
            if stream_callback:
                await stream_callback(step)

        await _emit("Analyzing query...")

        # 1. Select relevant tables
        await _emit("Selecting relevant tables...")
        relevant_tables = await schema_selector.get_relevant_tables(query, schema_name)
        # log.info("Relevant tables selected", tables=[t.table for t in relevant_tables]) # too spammy in logs

        # 2. Build system prompt
        system_prompt = build_system_prompt(schema_name, relevant_tables, schema_info)

        # 3. Initialize conversation history
        conversation: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        # 4. Generate initial SQL
        await _emit("Generating SQL...")
        initial_sql = await self._generate_sql(conversation)
        conversation.append({"role": "assistant", "content": initial_sql})

        if initial_sql.strip().upper() == "CANNOT_ANSWER":
            elapsed = (time.perf_counter() - start_time) * 1000
            return {
                "success": False,
                "error": "This question cannot be answered with the available database schema.",
                "attempts": [],
                "execution_time_ms": round(elapsed),
            }

        # 5. Validate SQL through sanitizer
        try:
            sanitized_sql = validate_sql(initial_sql)
        except SQLInjectionError as exc:
            log.warning("Generated SQL blocked by sanitizer", reason=exc.reason)
            elapsed = (time.perf_counter() - start_time) * 1000
            return {
                "success": False,
                "error": "Generated query was blocked for security reasons.",
                "attempts": [],
                "execution_time_ms": round(elapsed),
            }

        # 6. Self-healing execution loop
        await _emit("Executing query...")

        async def execute_with_schema(sql: str):
            return await db_execute(sql, schema_name)

        attempt_counter = [1]

        async def stream_retry(conv: list[dict]) -> str:
            attempt_counter[0] += 1
            # send message to frontend so user knows it failed but trying again
            await _emit(f"Fixing error (attempt {attempt_counter[0]})...")
            return await self._generate_sql(conv)

        healing_result = await run_self_healing_loop(
            initial_sql=sanitized_sql,
            execute_sql=execute_with_schema,
            generate_sql=stream_retry,
            conversation_history=conversation,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000)

        if not healing_result.success:
            await _emit("Failed")
            return {
                "success": False,
                "error": "Could not generate valid SQL after maximum retry attempts.",
                "attempts": [
                    {
                        "attempt": a.attempt,
                        "sql": a.sql,
                        "error": a.error,
                    }
                    for a in healing_result.attempts
                ],
                "execution_time_ms": elapsed_ms,
            }

        # 7. Classify result and build chart config
        await _emit("Classifying result...")
        result_type, chart_config = classify_result(
            healing_result.columns,
            healing_result.rows,
            healing_result.final_sql,
        )

        # 8. Generate explanation
        explanation = await self._generate_explanation(
            query, healing_result.final_sql, healing_result.columns, healing_result.rows
        )

        await _emit("Done")

        return {
            "success": True,
            "generated_sql": healing_result.final_sql,
            "explanation": explanation,
            "result": {
                "columns": healing_result.columns,
                "rows": healing_result.rows,
                "row_count": len(healing_result.rows),
            },
            "chart_config": chart_config,
            "attempt_count": healing_result.total_attempts,
            "execution_time_ms": elapsed_ms,
        }

    async def _generate_sql(self, conversation: list[dict]) -> str:
        """Call LLM to generate SQL from conversation history."""
        llm = self._get_llm()
        messages = []
        for msg in conversation:
            if msg["role"] == "system":
                messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            # Skip assistant messages as prior context (already in system)

        loop = asyncio.get_event_loop()
        response = await llm.ainvoke(messages)
        sql = response.content.strip()

        # Strip markdown code fences if present
        if sql.startswith("```"):
            lines = sql.split("\n")
            sql = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        return sql.strip()

    async def _generate_explanation(
        self,
        nl_query: str,
        sql: str,
        columns: list[str],
        rows: list[list],
    ) -> str:
        """Generate a plain-English explanation of what the query does."""
        row_count = len(rows)
        sample_rows = rows[:3]

        prompt = (
            f"User asked: '{nl_query}'\n"
            f"SQL generated: {sql}\n"
            f"Result: {row_count} rows, columns: {columns}\n"
            f"Sample data: {sample_rows}\n\n"
            "In 1-2 sentences, explain in plain English what this query does and what the results show."
        )

        llm = self._get_llm()
        try:
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception:
            return f"This query returned {row_count} rows from the {', '.join(columns[:3])} columns."


agent = QueryMindAgent()
