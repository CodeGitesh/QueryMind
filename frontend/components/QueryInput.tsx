"use client";

import { useState, useRef, useEffect } from "react";
import { useStore } from "@/lib/store";
import { Send, Loader2 } from "lucide-react";
import { z } from "zod";

const querySchema = z.object({
  query: z.string().min(1, "Query cannot be empty").max(500, "Max 500 characters"),
});

interface Props {
  onSubmit: (query: string, schemaName: string) => void;
}

const SCHEMAS = ["ecommerce", "hr", "finance"];

const EXAMPLE_QUERIES: Record<string, string[]> = {
  ecommerce: [
    "Show top 5 products by total revenue",
    "Monthly revenue trend for last 12 months",
    "Top 10 customers by number of orders",
    "Average order value by product category",
  ],
  hr: [
    "Show average salary by department",
    "Employees hired per month in 2024",
    "Top 5 departments by headcount",
    "Performance score distribution across roles",
  ],
  finance: [
    "Monthly income vs expenses for 2024",
    "Show investment portfolio breakdown by asset type",
    "Total spending by category this year",
    "Monthly savings trend for all accounts",
  ],
};

export function QueryInput({ onSubmit }: Props) {
  const { activeSchema, setActiveSchema, isLoading, uploadedSchema } = useStore();
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const allSchemas = [...SCHEMAS, ...(uploadedSchema ? [uploadedSchema] : [])];
  const charCount = query.length;
  const isOverLimit = charCount > 500;
  const examples = EXAMPLE_QUERIES[activeSchema] ?? [];

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [query]);

  function handleSubmit() {
    const result = querySchema.safeParse({ query });
    if (!result.success) {
      setError(result.error.issues[0]?.message || "Validation error");
      return;
    }
    setError("");
    onSubmit(query.trim(), activeSchema);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="glass-card p-5">
      {/* Schema selector */}
      <div className="flex items-center gap-3 mb-3">
        <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
          SCHEMA
        </span>
        <div className="relative">
          <select
            id="schema-selector"
            className="qm-select text-xs"
            value={activeSchema}
            onChange={(e) => setActiveSchema(e.target.value)}
          >
            {allSchemas.map((s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, " ")}
              </option>
            ))}
          </select>
        </div>

        {/* Example queries */}
        <div className="flex gap-1.5 flex-wrap ml-auto">
          {examples.slice(0, 2).map((ex) => (
            <button
              key={ex}
              className="btn-ghost text-xs truncate max-w-[200px]"
              onClick={() => setQuery(ex)}
              title={ex}
            >
              {ex.length > 35 ? ex.slice(0, 35) + "…" : ex}
            </button>
          ))}
        </div>
      </div>

      {/* Textarea */}
      <div className="relative">
        <textarea
          ref={textareaRef}
          id="query-input"
          className="qm-input sql-code"
          style={{ minHeight: "80px", maxHeight: "200px", paddingRight: "120px" }}
          placeholder="Ask anything… e.g. 'Show top 10 customers by revenue this year'"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setError(""); }}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          aria-label="Natural language query"
        />

        {/* Submit button */}
        <button
          id="submit-query"
          className="btn-primary absolute right-3 bottom-3 text-xs"
          onClick={handleSubmit}
          disabled={isLoading || isOverLimit || !query.trim()}
        >
          {isLoading ? (
            <><Loader2 size={13} className="animate-spin" /> Running</>
          ) : (
            <><Send size={13} /> Run <span className="opacity-60 ml-0.5 hidden sm:inline">(⌘↵)</span></>
          )}
        </button>
      </div>

      {/* Footer row */}
      <div className="flex items-center justify-between mt-2">
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          {error ? (
            <span style={{ color: "var(--accent-rose)" }}>{error}</span>
          ) : (
            "Ctrl+Enter or ⌘+Enter to run"
          )}
        </span>
        <span
          className="text-xs font-mono"
          style={{ color: isOverLimit ? "var(--accent-rose)" : "var(--text-muted)" }}
        >
          {charCount} / 500
        </span>
      </div>
    </div>
  );
}
