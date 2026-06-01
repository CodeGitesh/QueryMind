"use client";

import { useState } from "react";
import type { QueryResponse } from "@/lib/types";
import { SQLViewer } from "./SQLViewer";
import { ChartRenderer } from "./ChartRenderer";
import {
  CheckCircle2, XCircle, Clock, Rows, Zap, ChevronDown, ChevronUp,
  Sparkles, RefreshCw,
} from "lucide-react";

interface Props {
  response: QueryResponse;
}

export function ResultCard({ response }: Props) {
  const [sqlOpen, setSqlOpen] = useState(false);
  const [explainOpen, setExplainOpen] = useState(true);

  if (!response.success) {
    return (
      <div className="glass-card p-5 animate-slide-up" style={{ borderColor: "rgba(244,63,94,0.3)" }}>
        <div className="flex items-center gap-2 mb-3">
          <XCircle size={16} style={{ color: "var(--accent-rose)" }} />
          <span className="font-semibold text-sm" style={{ color: "var(--accent-rose)" }}>
            Query Failed
          </span>
        </div>
        <p className="text-sm mb-4" style={{ color: "var(--text-secondary)" }}>
          {response.error}
        </p>

        {response.attempts && response.attempts.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-xs font-semibold" style={{ color: "var(--text-muted)" }}>ATTEMPTS</p>
            {response.attempts.map((a) => (
              <div
                key={a.attempt}
                className="rounded-lg p-3 text-xs"
                style={{ background: "rgba(244,63,94,0.08)", border: "1px solid rgba(244,63,94,0.2)" }}
              >
                <p className="font-mono mb-1" style={{ color: "var(--accent-rose)" }}>
                  Attempt {a.attempt}: {a.error}
                </p>
                <pre className="sql-code text-xs overflow-auto" style={{ color: "var(--text-muted)" }}>
                  {a.sql}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  const wasHealed = (response.attempt_count ?? 1) > 1;

  return (
    <div className="glass-card overflow-hidden animate-slide-up">
      {/* Header */}
      <div
        className="flex items-center justify-between px-5 py-3 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <div className="flex items-center gap-2">
          <CheckCircle2 size={15} style={{ color: "var(--accent-emerald)" }} />
          <span className="text-sm font-semibold" style={{ color: "var(--accent-emerald)" }}>
            Success
          </span>
          {wasHealed && (
            <div className="badge badge-amber">
              <RefreshCw size={10} />
              Fixed in {response.attempt_count} attempts
            </div>
          )}
          {response.cached && (
            <div className="badge badge-cyan">
              <Zap size={10} /> Cached
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
          {response.execution_time_ms != null && (
            <span className="flex items-center gap-1">
              <Clock size={11} /> {response.execution_time_ms}ms
            </span>
          )}
          {response.result?.row_count != null && (
            <span className="flex items-center gap-1">
              <Rows size={11} /> {response.result.row_count.toLocaleString()} rows
            </span>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="p-5 flex flex-col gap-4">
        {/* SQL Viewer (collapsible) */}
        <div>
          <button
            id="toggle-sql"
            className="flex items-center gap-2 text-xs font-semibold mb-2 w-full text-left"
            style={{ color: "var(--accent-purple-light)" }}
            onClick={() => setSqlOpen(!sqlOpen)}
          >
            {sqlOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            Generated SQL
          </button>
          {sqlOpen && response.generated_sql && (
            <div className="animate-fade-in">
              <SQLViewer sql={response.generated_sql} />
            </div>
          )}
        </div>

        {/* Chart / Table (main area) */}
        {response.result && response.chart_config && (
          <ChartRenderer
            result={response.result}
            chartConfig={response.chart_config}
          />
        )}

        {/* Explanation (collapsible) */}
        {response.explanation && (
          <div>
            <button
              id="toggle-explanation"
              className="flex items-center gap-2 text-xs font-semibold mb-2 w-full text-left"
              style={{ color: "var(--text-secondary)" }}
              onClick={() => setExplainOpen(!explainOpen)}
            >
              {explainOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              <Sparkles size={12} style={{ color: "var(--accent-cyan)" }} />
              Explanation
            </button>
            {explainOpen && (
              <p
                className="text-sm animate-fade-in rounded-lg p-3"
                style={{
                  color: "var(--text-secondary)",
                  background: "rgba(6,182,212,0.06)",
                  border: "1px solid rgba(6,182,212,0.15)",
                  lineHeight: 1.7,
                }}
              >
                {response.explanation}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
