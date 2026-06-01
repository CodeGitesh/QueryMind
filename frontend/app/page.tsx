"use client";

import { SchemaBrowser } from "@/components/SchemaBrowser";
import { QueryInput } from "@/components/QueryInput";
import { ResultCard } from "@/components/ResultCard";
import { AgentSteps } from "@/components/AgentSteps";
import { QueryHistory } from "@/components/QueryHistory";
import { useStore } from "@/lib/store";
import { runQuery } from "@/lib/api";
import type { HistoryItem, QueryResponse } from "@/lib/types";
import { LayoutGrid, History, Database, Zap } from "lucide-react";
import { useState } from "react";

export default function HomePage() {
  const {
    result, setResult,
    isLoading, setIsLoading, streamSteps, addStreamStep,
    clearStreamSteps, schemaBrowserOpen, toggleSchemaBrowser,
    sessionId, prependHistory,
  } = useStore();

  const [activePanel, setActivePanel] = useState<"history" | null>(null);

  async function handleQuery(query: string, schemaName: string) {
    setIsLoading(true);
    setResult(null);
    clearStreamSteps();
    addStreamStep("Analyzing query...");

    try {
      const WS_BASE = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
      const ws = new WebSocket(`${WS_BASE}/ws/query`);

      const wsResult = await new Promise<QueryResponse | null>((resolve, reject) => {
        let settled = false;

        ws.onopen = () => {
          ws.send(JSON.stringify({ query, schema_name: schemaName, session_id: sessionId }));
        };

        ws.onmessage = (e: MessageEvent) => {
          const msg = JSON.parse(e.data as string);
          if (msg.type === "step" && msg.step) {
            addStreamStep(msg.step as string);
          } else if (msg.type === "result") {
            settled = true;
            resolve(msg.data);
            ws.close();
          } else if (msg.type === "error") {
            settled = true;
            reject(new Error(msg.error as string));
            ws.close();
          }
        };

        ws.onerror = () => {
          if (!settled) {
            // WebSocket failed — fall back to HTTP
            settled = true;
            resolve(null);
          }
        };

        ws.onclose = () => {
          if (!settled) resolve(null);
        };

        // Timeout after 60s
        setTimeout(() => {
          if (!settled) { settled = true; resolve(null); ws.close(); }
        }, 60000);
      });

      if (wsResult) {
        setResult(wsResult);
        if (wsResult) {
          const histItem: HistoryItem = {
            id: wsResult.query_id,
            natural_language: query,
            generated_sql: wsResult.generated_sql,
            success: wsResult.success,
            attempt_count: wsResult.attempt_count,
            execution_time_ms: wsResult.execution_time_ms,
            result_row_count: wsResult.result?.row_count,
            schema_used: schemaName,
            created_at: new Date().toISOString(),
          };
          prependHistory(histItem);
        }
        return;
      }

      // HTTP fallback
      addStreamStep("Generating SQL...");
      const httpResult = await runQuery({ query, schema_name: schemaName, session_id: sessionId });
      setResult(httpResult);
      addStreamStep("Done");

      const histItem: HistoryItem = {
        id: httpResult.query_id,
        natural_language: query,
        generated_sql: httpResult.generated_sql,
        success: httpResult.success,
        attempt_count: httpResult.attempt_count,
        execution_time_ms: httpResult.execution_time_ms,
        result_row_count: httpResult.result?.row_count,
        schema_used: schemaName,
        created_at: new Date().toISOString(),
      };
      prependHistory(histItem);

    } catch (err) {
      setResult({
        success: false,
        query_id: "error",
        attempt_count: 1,
        execution_time_ms: 0,
        cached: false,
        error: err instanceof Error ? err.message : "Unknown error",
      });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-grid" style={{ background: "var(--bg-primary)" }}>
      {/* ── Schema Browser Sidebar ── */}
      <div
        className="sidebar flex-shrink-0 border-r"
        style={{
          width: schemaBrowserOpen ? "280px" : "0px",
          borderColor: "var(--border)",
          background: "var(--bg-secondary)",
        }}
      >
        <SchemaBrowser />
      </div>

      {/* ── Main Content ── */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <header
          className="flex items-center justify-between px-6 py-3 border-b flex-shrink-0"
          style={{ borderColor: "var(--border)", background: "var(--bg-secondary)" }}
        >
          <div className="flex items-center gap-3">
            <button
              id="toggle-schema-browser"
              onClick={toggleSchemaBrowser}
              className="btn-ghost p-2"
              title="Toggle Schema Browser"
            >
              <Database size={16} />
            </button>
            <div className="flex items-center gap-2">
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center"
                style={{ background: "var(--gradient-primary)" }}
              >
                <Zap size={14} className="text-white" />
              </div>
              <span className="font-bold text-sm gradient-text">QueryMind</span>
            </div>
          </div>

          <nav className="flex items-center gap-1">
            <button
              id="nav-home"
              onClick={() => setActivePanel(null)}
              className={`btn-ghost text-xs flex items-center gap-1.5 ${!activePanel ? "border-purple-500/40 text-purple-300" : ""}`}
            >
              <LayoutGrid size={13} /> Query
            </button>
            <button
              id="nav-history"
              onClick={() => setActivePanel(activePanel === "history" ? null : "history")}
              className={`btn-ghost text-xs flex items-center gap-1.5 ${activePanel === "history" ? "border-purple-500/40 text-purple-300" : ""}`}
            >
              <History size={13} /> History
            </button>
            <a
              href="/upload"
              id="nav-upload"
              className="btn-ghost text-xs flex items-center gap-1.5"
            >
              Upload CSV
            </a>
          </nav>
        </header>

        {/* Content area */}
        <div className="flex flex-1 overflow-hidden">
          <main className="flex flex-col flex-1 overflow-auto p-6 gap-5">
            <QueryInput onSubmit={handleQuery} />

            {(isLoading || streamSteps.length > 0) && (
              <AgentSteps steps={streamSteps} isActive={isLoading} />
            )}

            {result && !isLoading && (
              <div className="animate-slide-up">
                <ResultCard response={result} />
              </div>
            )}
          </main>

          {/* History panel */}
          {activePanel === "history" && (
            <aside
              className="w-80 flex-shrink-0 border-l overflow-auto"
              style={{ borderColor: "var(--border)", background: "var(--bg-secondary)" }}
            >
              <QueryHistory onRerun={(q, s) => { setActivePanel(null); handleQuery(q, s); }} />
            </aside>
          )}
        </div>
      </div>
    </div>
  );
}
