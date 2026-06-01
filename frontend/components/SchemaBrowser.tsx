"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import { fetchSchema } from "@/lib/api";
import { useStore } from "@/lib/store";
import type { SchemaInfo } from "@/lib/types";
import { Database, Table2, ChevronDown, ChevronRight, Search, Tag } from "lucide-react";

export function SchemaBrowser() {
  const { activeSchema, setCurrentQuery, currentQuery, schemas, setSchema } = useStore();
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState("");

  const { data, isLoading } = useSWR<SchemaInfo>(
    `schema:${activeSchema}`,
    () => fetchSchema(activeSchema),
    { revalidateOnFocus: false, dedupingInterval: 60000 }
  );

  useEffect(() => {
    if (data) setSchema(activeSchema, data);
  }, [data, activeSchema, setSchema]);

  const schemaData = schemas[activeSchema] ?? data;
  const tables = schemaData?.tables ?? {};
  const tableNames = Object.keys(tables).filter((t) =>
    filter === "" || t.toLowerCase().includes(filter.toLowerCase())
  );

  function toggleTable(name: string) {
    setExpandedTables((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  function insertTableName(name: string) {
    const newQuery = currentQuery + (currentQuery ? " " : "") + name;
    setCurrentQuery(newQuery);
  }

  return (
    <div className="flex flex-col h-full p-3 gap-3">
      {/* Header */}
      <div className="flex items-center gap-2 px-1">
        <Database size={14} style={{ color: "var(--accent-purple)" }} />
        <span className="text-xs font-semibold" style={{ color: "var(--accent-purple-light)" }}>
          {activeSchema}
        </span>
        <span className="badge badge-purple ml-auto">{tableNames.length} tables</span>
      </div>

      {/* Search */}
      <div className="relative">
        <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: "var(--text-muted)" }} />
        <input
          id="schema-search"
          className="qm-input text-xs py-1.5"
          style={{ paddingLeft: "2rem" }}
          placeholder="Filter tables…"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </div>

      {/* Table tree */}
      <div className="flex-1 overflow-auto flex flex-col gap-0.5">
        {isLoading && (
          <div className="flex flex-col gap-2 p-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton h-7 rounded-md" />
            ))}
          </div>
        )}

        {!isLoading && tableNames.length === 0 && (
          <p className="text-xs p-2" style={{ color: "var(--text-muted)" }}>No tables found</p>
        )}

        {tableNames.map((tableName) => {
          const tableInfo = tables[tableName];
          const isExpanded = expandedTables.has(tableName);

          return (
            <div key={tableName}>
              <button
                id={`table-${tableName}`}
                className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-left text-xs transition-colors"
                style={{ color: "var(--text-secondary)" }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = "rgba(139,92,246,0.1)";
                  (e.currentTarget as HTMLButtonElement).style.color = "var(--text-primary)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLButtonElement).style.background = "";
                  (e.currentTarget as HTMLButtonElement).style.color = "var(--text-secondary)";
                }}
                onClick={() => toggleTable(tableName)}
              >
                {isExpanded ? <ChevronDown size={11} /> : <ChevronRight size={11} />}
                <Table2 size={12} style={{ color: "var(--accent-purple)", flexShrink: 0 }} />
                <span className="font-medium truncate">{tableName}</span>
                {tableInfo.row_count > 0 && (
                  <span className="ml-auto text-xs" style={{ color: "var(--text-muted)", flexShrink: 0 }}>
                    {tableInfo.row_count.toLocaleString()}
                  </span>
                )}
              </button>

              {/* Columns */}
              {isExpanded && (
                <div className="ml-4 pl-3 border-l mb-0.5" style={{ borderColor: "var(--border)" }}>
                  {/* Click to insert table name */}
                  <button
                    className="text-xs py-0.5 px-2 mb-1"
                    style={{ color: "var(--accent-cyan)", cursor: "pointer" }}
                    onClick={() => insertTableName(tableName)}
                    title="Insert table name into query"
                  >
                    + insert name
                  </button>
                  {tableInfo.columns.map((col) => (
                    <div
                      key={col.name}
                      className="flex items-center gap-2 py-1 px-2 rounded"
                      style={{ fontSize: "0.7rem" }}
                    >
                      <Tag size={9} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
                      <span style={{ color: "var(--text-secondary)" }}>{col.name}</span>
                      <span
                        className="ml-auto font-mono"
                        style={{ color: "var(--text-muted)", fontSize: "0.65rem" }}
                      >
                        {col.type.split("(")[0].toLowerCase()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
