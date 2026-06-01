"use client";

import { CheckCircle2, Loader2, Terminal } from "lucide-react";
import { useEffect, useRef } from "react";

interface Props {
  steps: string[];
  isActive: boolean;
}

const STEP_ICONS: Record<string, string> = {
  "Analyzing query...":         "🔍",
  "Selecting relevant tables...":"🗂️",
  "Generating SQL...":          "⚡",
  "Executing query...":         "🚀",
  "Classifying result...":      "📊",
  "Done":                       "✅",
};

function getStepIcon(step: string): string {
  for (const [key, icon] of Object.entries(STEP_ICONS)) {
    if (step.startsWith(key.replace("...", ""))) return icon;
  }
  if (step.startsWith("Fixing")) return "🔧";
  return "⚙️";
}

export function AgentSteps({ steps, isActive }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest step
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [steps]);

  if (steps.length === 0) return null;

  const isDone = !isActive && steps.at(-1) === "Done";

  return (
    <div
      className="glass-card p-4 animate-fade-in"
      style={{ borderColor: isActive ? "var(--border-bright)" : undefined }}
    >
      <div className="flex items-center gap-2 mb-3">
        <Terminal size={14} style={{ color: "var(--accent-purple)" }} />
        <span className="text-xs font-semibold" style={{ color: "var(--accent-purple-light)" }}>
          Agent Execution
        </span>
        {isActive && (
          <span className="ml-auto">
            <Loader2 size={13} className="animate-spin" style={{ color: "var(--accent-cyan)" }} />
          </span>
        )}
        {isDone && (
          <CheckCircle2 size={13} className="ml-auto" style={{ color: "var(--accent-emerald)" }} />
        )}
      </div>

      <div
        ref={containerRef}
        className="flex flex-col gap-1.5 overflow-auto"
        style={{ maxHeight: "140px" }}
        aria-label="Agent steps"
        aria-live="polite"
      >
        {steps.map((step, i) => {
          const isLast = i === steps.length - 1;
          const isFixed = step.toLowerCase().includes("fixing");
          return (
            <div
              key={`${step}-${i}`}
              className="flex items-center gap-2 text-xs animate-step-in"
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              {/* Timeline dot */}
              <div className="flex flex-col items-center self-stretch">
                <div
                  className="w-5 h-5 rounded-full flex items-center justify-center text-xs flex-shrink-0"
                  style={{
                    background: isFixed
                      ? "rgba(245,158,11,0.2)"
                      : isLast && isActive
                      ? "rgba(139,92,246,0.25)"
                      : "rgba(16,185,129,0.15)",
                    border: `1px solid ${isFixed ? "rgba(245,158,11,0.4)" : isLast && isActive ? "var(--border-bright)" : "rgba(16,185,129,0.3)"}`,
                  }}
                >
                  {getStepIcon(step)}
                </div>
                {i < steps.length - 1 && (
                  <div className="w-px flex-1 mt-1" style={{ background: "var(--border)", minHeight: "8px" }} />
                )}
              </div>

              {/* Step label */}
              <div className="flex items-center gap-2 py-0.5">
                <span
                  style={{
                    color: isFixed
                      ? "var(--accent-amber)"
                      : isLast && isActive
                      ? "var(--text-primary)"
                      : "var(--text-secondary)",
                    fontWeight: isLast ? "500" : "400",
                  }}
                >
                  {step}
                </span>
                {isLast && isActive && (
                  <span className="badge badge-purple text-xs py-0 px-1.5">running</span>
                )}
                {isFixed && (
                  <span className="badge badge-amber text-xs py-0 px-1.5">retry</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
