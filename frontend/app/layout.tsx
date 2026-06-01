import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "QueryMind — Natural Language to SQL AI Agent",
  description:
    "Talk to your database in plain English. QueryMind converts natural language to SQL with self-healing capabilities and beautiful visualizations.",
  keywords: ["SQL", "AI", "natural language", "database", "LLM", "analytics"],
  authors: [{ name: "QueryMind" }],
  openGraph: {
    title: "QueryMind — NL to SQL AI Agent",
    description: "Query your database in plain English with self-healing AI",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
