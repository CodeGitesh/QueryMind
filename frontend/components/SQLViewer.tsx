"use client";

import { Copy, Check } from "lucide-react";
import { useState } from "react";

interface Props {
  sql: string;
}

// Simple SQL syntax highlighting without heavy deps
function highlightSQL(sql: string): string {
  const keywords = [
    "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
    "ON", "AND", "OR", "NOT", "IN", "LIKE", "IS", "NULL", "ORDER", "BY",
    "GROUP", "HAVING", "LIMIT", "OFFSET", "AS", "DISTINCT", "COUNT", "SUM",
    "AVG", "MAX", "MIN", "CASE", "WHEN", "THEN", "ELSE", "END", "WITH",
    "UNION", "ALL", "INTERSECT", "EXCEPT", "DESC", "ASC", "ROUND", "COALESCE",
    "EXTRACT", "DATE_TRUNC", "NOW", "CURRENT_DATE",
  ];
  const keywordRegex = new RegExp(`\\b(${keywords.join("|")})\\b`, "gi");

  return sql
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/'[^']*'/g, (m) => `<span style="color:#6ee7b7">${m}</span>`)
    .replace(/--[^\n]*/g, (m) => `<span style="color:#6b7280;font-style:italic">${m}</span>`)
    .replace(/\b(\d+\.?\d*)\b/g, `<span style="color:#fcd34d">$1</span>`)
    .replace(keywordRegex, (m) => `<span style="color:#a78bfa;font-weight:600">${m.toUpperCase()}</span>`);
}

export function SQLViewer({ sql }: Props) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div
      className="rounded-lg overflow-hidden"
      style={{ background: "var(--bg-primary)", border: "1px solid var(--border)" }}
    >
      {/* Toolbar */}
      <div
        className="flex items-center justify-between px-4 py-2 border-b"
        style={{ borderColor: "var(--border)", background: "rgba(139,92,246,0.07)" }}
      >
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full" style={{ background: "rgba(244,63,94,0.6)" }} />
          <div className="w-3 h-3 rounded-full" style={{ background: "rgba(245,158,11,0.6)" }} />
          <div className="w-3 h-3 rounded-full" style={{ background: "rgba(16,185,129,0.6)" }} />
        </div>
        <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>SQL</span>
        <button
          id="copy-sql"
          onClick={copy}
          className="btn-ghost text-xs flex items-center gap-1 py-1 px-2"
        >
          {copied ? <Check size={11} style={{ color: "var(--accent-emerald)" }} /> : <Copy size={11} />}
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>

      {/* Code */}
      <pre
        className="sql-code p-4 overflow-auto"
        style={{ color: "var(--text-secondary)", maxHeight: "320px", whiteSpace: "pre-wrap" }}
        dangerouslySetInnerHTML={{ __html: highlightSQL(sql) }}
        aria-label="Generated SQL"
      />
    </div>
  );
}
