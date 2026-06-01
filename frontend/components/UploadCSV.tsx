"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { uploadCSV } from "@/lib/api";
import type { UploadResponse } from "@/lib/types";
import { useStore } from "@/lib/store";
import {
  Upload, FileText, CheckCircle2, AlertCircle, Loader2, Database,
} from "lucide-react";

export function UploadCSV() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { sessionId, setUploadedSchema } = useStore();

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setUploading(true);
      setError(null);
      setResult(null);

      try {
        const response = await uploadCSV(file, sessionId);
        setResult(response);
        setUploadedSchema(response.schema_name);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [sessionId, setUploadedSchema]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"], "text/plain": [".csv"] },
    maxSize: 50 * 1024 * 1024,
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold gradient-text mb-2">Upload CSV</h1>
      <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
        Upload a CSV file to query it instantly with natural language. Max 50MB.
      </p>

      {/* Dropzone */}
      <div
        {...getRootProps()}
        id="csv-dropzone"
        className="glass-card p-10 text-center cursor-pointer transition-all"
        style={{
          borderColor: isDragActive
            ? "var(--accent-purple)"
            : isDragReject
            ? "var(--accent-rose)"
            : undefined,
          borderStyle: "dashed",
          background: isDragActive ? "rgba(139,92,246,0.08)" : undefined,
        }}
      >
        <input {...getInputProps()} id="csv-file-input" />

        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 size={40} className="animate-spin" style={{ color: "var(--accent-purple)" }} />
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Processing CSV…</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center"
              style={{ background: "rgba(139,92,246,0.15)", border: "1px solid var(--border-bright)" }}
            >
              <Upload size={28} style={{ color: "var(--accent-purple)" }} />
            </div>
            <div>
              <p className="text-sm font-medium mb-1" style={{ color: "var(--text-primary)" }}>
                {isDragActive ? "Drop to upload" : "Drag & drop your CSV here"}
              </p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                or <span style={{ color: "var(--accent-purple)" }}>browse</span> — max 50MB
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div
          className="mt-4 rounded-lg p-3 flex items-center gap-2 text-sm animate-fade-in"
          style={{ background: "rgba(244,63,94,0.1)", border: "1px solid rgba(244,63,94,0.3)", color: "var(--accent-rose)" }}
        >
          <AlertCircle size={15} />
          {error}
        </div>
      )}

      {/* Success result */}
      {result && (
        <div className="mt-4 glass-card p-5 animate-slide-up">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 size={16} style={{ color: "var(--accent-emerald)" }} />
            <span className="font-semibold text-sm" style={{ color: "var(--accent-emerald)" }}>
              Upload Successful
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-4">
            {[
              { label: "Table", value: result.table_name, icon: <Database size={12} /> },
              { label: "Rows", value: result.row_count.toLocaleString() },
              { label: "Columns", value: result.column_count },
              { label: "File", value: result.original_filename, icon: <FileText size={12} /> },
            ].map(({ label, value, icon }) => (
              <div key={label} className="rounded-lg p-3" style={{ background: "rgba(139,92,246,0.07)" }}>
                <p className="text-xs mb-1 flex items-center gap-1" style={{ color: "var(--text-muted)" }}>
                  {icon} {label}
                </p>
                <p className="text-sm font-semibold truncate" style={{ color: "var(--text-primary)" }}>
                  {String(value)}
                </p>
              </div>
            ))}
          </div>

          {/* Columns preview */}
          <div>
            <p className="text-xs font-semibold mb-2" style={{ color: "var(--text-muted)" }}>
              DETECTED COLUMNS
            </p>
            <div className="flex flex-wrap gap-1.5">
              {result.columns.map((col) => (
                <div key={col.name} className="badge badge-purple">
                  {col.name}
                  <span style={{ opacity: 0.6, marginLeft: "0.25rem" }}>{col.sql_type}</span>
                </div>
              ))}
            </div>
          </div>

          <div
            className="mt-4 rounded-lg p-3 text-xs"
            style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)", color: "var(--accent-emerald)" }}
          >
            Schema <strong>{result.schema_name}</strong> is now available. Go back to the main page and select it in the schema dropdown.
          </div>
        </div>
      )}
    </div>
  );
}
