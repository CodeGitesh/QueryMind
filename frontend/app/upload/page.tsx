import type { Metadata } from "next";
import { UploadCSV } from "@/components/UploadCSV";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export const metadata: Metadata = {
  title: "Upload CSV — QueryMind",
  description: "Upload a CSV file and query it instantly with natural language",
};

export default function UploadPage() {
  return (
    <div className="min-h-screen p-8 bg-grid" style={{ background: "var(--bg-primary)" }}>
      <div className="max-w-2xl mx-auto">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs mb-6 btn-ghost"
        >
          <ArrowLeft size={12} /> Back to QueryMind
        </Link>
        <UploadCSV />
      </div>
    </div>
  );
}
