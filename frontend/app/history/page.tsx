import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export const metadata: Metadata = {
  title: "Query History — QueryMind",
  description: "View and re-run past queries",
};

export default function HistoryPage() {
  return (
    <div className="min-h-screen p-8 bg-grid" style={{ background: "var(--bg-primary)" }}>
      <div className="max-w-4xl mx-auto">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs mb-6 btn-ghost"
        >
          <ArrowLeft size={12} /> Back to QueryMind
        </Link>
        <h1 className="text-2xl font-bold gradient-text mb-2">Query History</h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          All past queries — click Re-run to replay any query.
        </p>
        {/* Full history available via the sidebar panel on main page */}
        <div className="glass-card p-8 text-center">
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Query history is accessible from the main page. Click the <strong>History</strong> button in the top navigation.
          </p>
          <Link href="/" className="btn-primary mt-4 inline-flex">Open QueryMind →</Link>
        </div>
      </div>
    </div>
  );
}
