// Typed API client — all backend calls centralized here

import type {
  HistoryListResponse,
  QueryRequest,
  QueryResponse,
  SchemaInfo,
  UploadResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }

  return res.json() as Promise<T>;
}

// ── Query ─────────────────────────────────────────────────────────────────────

export async function runQuery(payload: QueryRequest): Promise<QueryResponse> {
  return request<QueryResponse>("/query", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ── Schema ────────────────────────────────────────────────────────────────────

export async function fetchSchemas(): Promise<{ schemas: { name: string; table_count: number }[] }> {
  return request("/schema");
}

export async function fetchSchema(schemaName: string): Promise<SchemaInfo> {
  return request<SchemaInfo>(`/schema/${schemaName}`);
}

// ── History ───────────────────────────────────────────────────────────────────

export async function fetchHistory(
  page = 1,
  pageSize = 20,
  schemaName?: string
): Promise<HistoryListResponse> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (schemaName) params.set("schema_name", schemaName);
  return request<HistoryListResponse>(`/history?${params}`);
}

export async function deleteHistory(id: string): Promise<{ success: boolean }> {
  return request(`/history/${id}`, { method: "DELETE" });
}

// ── Upload ────────────────────────────────────────────────────────────────────

export async function uploadCSV(
  file: File,
  sessionId: string
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("session_id", sessionId);

  const res = await fetch(`${API_BASE}/upload-csv`, {
    method: "POST",
    body: formData,
    // Don't set Content-Type — browser sets multipart boundary automatically
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Upload failed: HTTP ${res.status}`);
  }

  return res.json() as Promise<UploadResponse>;
}
