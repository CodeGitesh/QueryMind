"use client";

import { useState, useCallback } from "react";
import type { ChartConfig, ResultData } from "@/lib/types";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { Download } from "lucide-react";

const COLORS = [
  "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#f43f5e",
  "#a78bfa", "#67e8f9", "#6ee7b7", "#fcd34d", "#fda4af",
];

interface Props {
  result: ResultData;
  chartConfig: ChartConfig;
}

function buildChartData(result: ResultData): Record<string, string | number>[] {
  return result.rows.map((row) => {
    const obj: Record<string, string | number> = {};
    result.columns.forEach((col, i) => {
      const val = row[i];
      obj[col] = typeof val === "number" ? val : (val != null ? String(val) : "");
    });
    return obj;
  });
}

function downloadCSV(columns: string[], rows: (string | number | boolean | null)[][]) {
  const csv = [columns.join(","), ...rows.map((r) => r.map((v) => JSON.stringify(v ?? "")).join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "querymind_result.csv"; a.click();
  URL.revokeObjectURL(url);
}

// Sortable data table
function DataTable({ result }: { result: ResultData }) {
  const [sortCol, setSortCol] = useState<number | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(0);
  const pageSize = 50;

  const handleSort = useCallback((colIdx: number) => {
    if (sortCol === colIdx) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortCol(colIdx); setSortDir("asc"); }
  }, [sortCol]);

  const sorted = sortCol !== null
    ? [...result.rows].sort((a, b) => {
        const av = a[sortCol], bv = b[sortCol];
        if (av == null) return 1;
        if (bv == null) return -1;
        const cmp = typeof av === "number" && typeof bv === "number"
          ? av - bv
          : String(av).localeCompare(String(bv));
        return sortDir === "asc" ? cmp : -cmp;
      })
    : result.rows;

  const paginated = sorted.slice(page * pageSize, (page + 1) * pageSize);
  const totalPages = Math.ceil(sorted.length / pageSize);

  return (
    <div>
      <div className="overflow-auto rounded-lg" style={{ border: "1px solid var(--border)", maxHeight: "400px" }}>
        <table className="qm-table">
          <thead>
            <tr>
              {result.columns.map((col, i) => (
                <th key={col} onClick={() => handleSort(i)}>
                  {col} {sortCol === i ? (sortDir === "asc" ? "↑" : "↓") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginated.map((row, ri) => (
              <tr key={ri}>
                {row.map((cell, ci) => (
                  <td key={ci} title={String(cell ?? "")}>
                    {cell == null ? <span style={{ color: "var(--text-muted)" }}>null</span> : String(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* Pagination + download */}
      <div className="flex items-center justify-between mt-2">
        <div className="flex gap-2">
          <button className="btn-ghost text-xs" onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}>← Prev</button>
          <span className="text-xs self-center" style={{ color: "var(--text-muted)" }}>
            {page + 1} / {Math.max(1, totalPages)} ({result.row_count.toLocaleString()} rows)
          </span>
          <button className="btn-ghost text-xs" onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}>Next →</button>
        </div>
        <button
          className="btn-ghost text-xs flex items-center gap-1"
          onClick={() => downloadCSV(result.columns, result.rows)}
        >
          <Download size={11} /> CSV
        </button>
      </div>
    </div>
  );
}

export function ChartRenderer({ result, chartConfig }: Props) {
  if (!result || result.rows.length === 0) {
    return (
      <div className="rounded-lg p-8 text-center text-sm" style={{ background: "rgba(139,92,246,0.05)", color: "var(--text-muted)" }}>
        No data returned
      </div>
    );
  }

  // SCALAR — big number display
  if (chartConfig.type === "scalar") {
    return (
      <div className="text-center py-8">
        <p className="text-5xl font-bold gradient-text mb-2">
          {typeof chartConfig.value === "number"
            ? chartConfig.value.toLocaleString(undefined, { maximumFractionDigits: 2 })
            : String(chartConfig.value ?? result.rows[0]?.[0] ?? "—")}
        </p>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{chartConfig.label ?? chartConfig.title}</p>
      </div>
    );
  }

  // TABLE
  if (chartConfig.type === "table") {
    return <DataTable result={result} />;
  }

  const data = buildChartData(result);
  const title = chartConfig.title;

  // LINE CHART
  if (chartConfig.type === "line") {
    const yKeys = chartConfig.y_keys ?? (chartConfig.y_key ? [chartConfig.y_key] : []);
    return (
      <div>
        {title && <p className="text-xs font-semibold mb-3" style={{ color: "var(--text-secondary)" }}>{title}</p>}
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data} margin={{ top: 5, right: 20, bottom: 30, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={chartConfig.x_key} tick={{ fontSize: 11 }} angle={-35} textAnchor="end" interval="preserveStartEnd" />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border-bright)", borderRadius: 8 }} />
            <Legend />
            {yKeys.map((key, i) => (
              <Line key={key} type="monotone" dataKey={key} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // PIE CHART
  if (chartConfig.type === "pie") {
    return (
      <div>
        {title && <p className="text-xs font-semibold mb-3" style={{ color: "var(--text-secondary)" }}>{title}</p>}
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie data={data} dataKey={chartConfig.y_key ?? result.columns[1]} nameKey={chartConfig.x_key ?? result.columns[0]} cx="50%" cy="50%" outerRadius={100} label={({ name, percent }) => `${name} ${percent ? (percent * 100).toFixed(0) : '0'}%`}>
              {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border-bright)", borderRadius: 8 }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // BAR CHART (vertical or horizontal for LIST)
  const isHorizontal = chartConfig.layout === "horizontal";
  return (
    <div>
      {title && <p className="text-xs font-semibold mb-3" style={{ color: "var(--text-secondary)" }}>{title}</p>}
      <ResponsiveContainer width="100%" height={280}>
        <BarChart
          data={data}
          layout={isHorizontal ? "vertical" : "horizontal"}
          margin={{ top: 5, right: 20, bottom: isHorizontal ? 5 : 30, left: isHorizontal ? 120 : 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          {isHorizontal
            ? <><YAxis dataKey={chartConfig.x_key} type="category" tick={{ fontSize: 10 }} width={110} /><XAxis type="number" tick={{ fontSize: 11 }} /></>
            : <><XAxis dataKey={chartConfig.x_key} tick={{ fontSize: 11 }} angle={-35} textAnchor="end" interval={0} /><YAxis tick={{ fontSize: 11 }} /></>}
          <Tooltip contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border-bright)", borderRadius: 8 }} />
          <Bar dataKey={chartConfig.y_key ?? result.columns[1]} fill="url(#barGradient)" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
