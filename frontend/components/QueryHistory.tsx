"use client";

import { useState } from "react";
import useSWR from "swr";
import { fetchHistory, deleteHistory } from "@/lib/api";
import type { HistoryListResponse, HistoryItem } from "@/lib/types";
import { useStore } from "@/lib/store";
import { History, Trash2, PlayCircle, CheckCircle2, XCircle, Clock, ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  onRerun: (query: string, schemaName: string) => void;
}

export function QueryHistory({ onRerun }: Props) {
  const [page, setPage] = useState(1);
  const { activeSchema } = useStore();

  const { data, isLoading, mutate } = useSWR<HistoryListResponse>(
    `history:${page}:${activeSchema}`,
    () => fetchHistory(page, 20, activeSchema),
    { revalidateOnFocus: false }
  );

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    await deleteHistory(id);
    mutate();
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b" style={{ borderColor: "var(--border)" }}>
        <History size={14} style={{ color: "var(--accent-purple)" }} />
        <span className="text-sm font-semibold" style={{ color: "var(--accent-purple-light)" }}>
          Query History
        </span>
        {data && (
          <span className="badge badge-purple ml-auto">{data.total}</span>
        )}
      </div>

      {/* Items */}
      <div className="flex-1 overflow-auto p-3 flex flex-col gap-2">
        {isLoading && (
          <>
            {[1,2,3,4,5].map((i) => <div key={i} className="skeleton h-16 rounded-lg" />)}
          </>
        )}

        {!isLoading && data?.items.length === 0 && (
          <p className="text-xs text-center py-8" style={{ color: "var(--text-muted)" }}>
            No history yet. Run a query to get started.
          </p>
        )}

        {data?.items.map((item: HistoryItem) => (
          <div
            key={item.id}
            className="group rounded-lg p-3 cursor-pointer transition-all"
            style={{
              background: "rgba(139,92,246,0.05)",
              border: "1px solid var(--border)",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-bright)";
              (e.currentTarget as HTMLDivElement).style.background = "rgba(139,92,246,0.1)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border)";
              (e.currentTarget as HTMLDivElement).style.background = "rgba(139,92,246,0.05)";
            }}
          >
            {/* Status + schema */}
            <div className="flex items-center gap-2 mb-1.5">
              {item.success
                ? <CheckCircle2 size={11} style={{ color: "var(--accent-emerald)", flexShrink: 0 }} />
                : <XCircle size={11} style={{ color: "var(--accent-rose)", flexShrink: 0 }} />}
              <span className="badge badge-purple text-xs">{item.schema_used}</span>
              {item.execution_time_ms && (
                <span className="text-xs ml-auto flex items-center gap-0.5" style={{ color: "var(--text-muted)" }}>
                  <Clock size={9} /> {item.execution_time_ms}ms
                </span>
              )}
            </div>

            {/* Query text */}
            <p className="text-xs mb-2 line-clamp-2" style={{ color: "var(--text-secondary)" }}>
              {item.natural_language}
            </p>

            {/* Row count */}
            {item.result_row_count != null && (
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                {item.result_row_count.toLocaleString()} rows returned
              </p>
            )}

            {/* Actions (visible on hover) */}
            <div className="flex gap-1.5 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                id={`rerun-${item.id}`}
                className="btn-ghost text-xs flex items-center gap-1 py-1"
                onClick={() => onRerun(item.natural_language, item.schema_used ?? "ecommerce")}
              >
                <PlayCircle size={10} /> Re-run
              </button>
              <button
                id={`delete-${item.id}`}
                className="btn-ghost text-xs flex items-center gap-1 py-1 ml-auto"
                style={{ color: "var(--accent-rose)", borderColor: "rgba(244,63,94,0.3)" }}
                onClick={(e) => handleDelete(item.id, e)}
              >
                <Trash2 size={10} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      {data && data.total > 20 && (
        <div className="flex items-center justify-between p-3 border-t" style={{ borderColor: "var(--border)" }}>
          <button
            className="btn-ghost text-xs flex items-center gap-1"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            <ChevronLeft size={11} /> Prev
          </button>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            {page} / {Math.ceil(data.total / 20)}
          </span>
          <button
            className="btn-ghost text-xs flex items-center gap-1"
            onClick={() => setPage((p) => p + 1)}
            disabled={!data.has_next}
          >
            Next <ChevronRight size={11} />
          </button>
        </div>
      )}
    </div>
  );
}
