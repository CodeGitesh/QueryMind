"""
Schema selector: uses sentence-transformers to find the top-K most relevant
tables for a user query via cosine similarity — prevents context window overflow.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

import numpy as np
import structlog

from app.config import settings

log = structlog.get_logger(__name__)

# ── Schema definitions (table descriptions used for embedding) ─────────────────

SCHEMA_DEFINITIONS: dict[str, list[dict]] = {
    "ecommerce": [
        {"table": "customers", "description": "Customer accounts with name email phone country city. Buyer information."},
        {"table": "products",  "description": "Product catalog with name price stock SKU category seller. Items for sale."},
        {"table": "categories","description": "Product categories taxonomy. Electronics Clothing Books Sports Beauty etc."},
        {"table": "sellers",   "description": "Seller marketplace accounts with rating total sales country."},
        {"table": "orders",    "description": "Purchase orders with customer total amount status payment method ordered date shipped delivered."},
        {"table": "order_items","description": "Individual line items in orders with product quantity unit price total price."},
        {"table": "reviews",   "description": "Product reviews by customers with rating title body text."},
    ],
    "hr": [
        {"table": "employees",          "description": "Employee records with name email department role hire date status gender."},
        {"table": "departments",        "description": "Company departments with name budget location. Engineering Product Sales Marketing HR Finance."},
        {"table": "roles",              "description": "Job roles and titles with level salary range. Junior mid senior lead manager."},
        {"table": "salaries",           "description": "Employee compensation salary amounts currency effective dates."},
        {"table": "performance_reviews","description": "Employee performance evaluation scores quarterly reviews feedback."},
        {"table": "leave_requests",     "description": "Employee leave absence requests annual sick maternity paternity status approval."},
        {"table": "projects",           "description": "Company projects with name status budget start end dates."},
        {"table": "project_assignments","description": "Employee project assignments role hours per week contribution."},
    ],
    "finance": [
        {"table": "accounts",          "description": "Bank financial accounts checking savings investment credit currency balance."},
        {"table": "transactions",      "description": "Financial transactions debits credits amounts merchant description date."},
        {"table": "categories",        "description": "Transaction categories income expense transfer. Salary rent groceries entertainment."},
        {"table": "budgets",           "description": "Monthly quarterly annual budget allocations by category."},
        {"table": "monthly_summaries", "description": "Monthly aggregated income expenses savings net balance per account."},
        {"table": "investments",       "description": "Investment portfolio stocks ETF bonds crypto symbols quantity price."},
        {"table": "loans",             "description": "Loan accounts mortgage auto personal student outstanding balance interest rate."},
    ],
}


@dataclass
class TableMatch:
    table: str
    description: str
    score: float


class SchemaSelector:
    """Embeds table descriptions at startup; at query time selects top-K relevant tables."""

    def __init__(self) -> None:
        self._model = None
        self._embeddings: dict[str, dict[str, np.ndarray]] = {}
        self._ready = False

    async def initialise(self) -> None:
        """Load model and pre-compute all table embeddings (called once at startup)."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_and_embed)
        self._ready = True
        log.info("SchemaSelector ready", schemas=list(SCHEMA_DEFINITIONS.keys()))

    def _load_and_embed(self) -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore
        log.info("Loading sentence-transformer model", model=settings.EMBEDDING_MODEL)
        self._model = SentenceTransformer(settings.EMBEDDING_MODEL)

        for schema_name, tables in SCHEMA_DEFINITIONS.items():
            self._embeddings[schema_name] = {}
            for table_info in tables:
                text = f"{table_info['table']} {table_info['description']}"
                emb = self._model.encode(text, normalize_embeddings=True)
                self._embeddings[schema_name][table_info["table"]] = emb

        log.info("Schema embeddings computed", total_tables=sum(
            len(v) for v in self._embeddings.values()
        ))

    async def get_relevant_tables(
        self,
        query: str,
        schema_name: str,
        top_k: Optional[int] = None,
    ) -> list[TableMatch]:
        """Return top-K most relevant tables for the user query."""
        if not self._ready:
            # Fallback: return all tables if not yet ready
            return [
                TableMatch(t["table"], t["description"], 1.0)
                for t in SCHEMA_DEFINITIONS.get(schema_name, [])
            ]

        k = top_k or settings.TOP_K_TABLES
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._rank_tables, query, schema_name, k)

    def _rank_tables(self, query: str, schema_name: str, k: int) -> list[TableMatch]:
        if schema_name not in self._embeddings:
            return []

        query_emb = self._model.encode(query, normalize_embeddings=True)
        schema_embs = self._embeddings[schema_name]
        schema_tables = {t["table"]: t["description"] for t in SCHEMA_DEFINITIONS[schema_name]}

        scores: list[TableMatch] = []
        for table, emb in schema_embs.items():
            score = float(np.dot(query_emb, emb))
            scores.append(TableMatch(table, schema_tables[table], score))

        scores.sort(key=lambda x: x.score, reverse=True)
        return scores[:k]

    def get_all_tables(self, schema_name: str) -> list[dict]:
        return SCHEMA_DEFINITIONS.get(schema_name, [])


schema_selector = SchemaSelector()
