"use client";

import { TelemetryData } from "@/types";

interface TelemetryPanelProps {
  telemetry: TelemetryData | null;
  isStreaming: boolean;
}

function TelemetryCard({
  label,
  value,
  color,
  subtext,
}: {
  label: string;
  value: string;
  color: string;
  subtext?: string;
}) {
  return (
    <div className={`glass-card telemetry-card p-4`} style={{ borderColor: `${color}25` }}>
      <p className="text-xs font-medium mb-1" style={{ color: "#64748b" }}>{label}</p>
      <p className="text-2xl font-bold tracking-tight" style={{ color }}>{value}</p>
      {subtext && <p className="text-xs mt-1" style={{ color: "#475569" }}>{subtext}</p>}
    </div>
  );
}

export default function TelemetryPanel({ telemetry, isStreaming }: TelemetryPanelProps) {
  return (
    <div className="flex flex-col gap-3 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-1">
        <h2 className="text-sm font-semibold text-slate-300">Live Telemetry</h2>
        {isStreaming && (
          <span className="flex items-center gap-1.5 text-xs" style={{ color: "#22d3ee" }}>
            <span className="w-1.5 h-1.5 rounded-full pulse-dot" style={{ background: "#22d3ee" }} />
            Streaming
          </span>
        )}
      </div>

      <TelemetryCard
        label="Time To First Token"
        value={telemetry ? `${telemetry.ttft_ms.toFixed(1)} ms` : "—"}
        color="#22d3ee"
        subtext="Lower is better"
      />
      <TelemetryCard
        label="Tokens / Second"
        value={telemetry ? `${telemetry.tokens_per_sec} tok/s` : "—"}
        color="#a855f7"
        subtext="Generation speed"
      />
      <TelemetryCard
        label="Total Latency"
        value={telemetry ? `${telemetry.latency_ms.toFixed(0)} ms` : "—"}
        color="#f59e0b"
        subtext="End-to-end roundtrip"
      />
      <TelemetryCard
        label="Cost / Query"
        value={telemetry ? `$${telemetry.cost_usd.toFixed(6)}` : "$0.000000"}
        color="#10b981"
        subtext="Based on provider pricing"
      />
      <TelemetryCard
        label="Tokens In"
        value={telemetry ? `${telemetry.tokens_in.toLocaleString()}` : "0"}
        color="#6366f1"
        subtext="Prompt tokens sent"
      />
      <TelemetryCard
        label="Tokens Out"
        value={telemetry ? `${telemetry.tokens_out.toLocaleString()}` : "0"}
        color="#ec4899"
        subtext="Completion tokens"
      />

      {/* Mode badge */}
      {telemetry && (
        <div className="glass-card px-3 py-2 flex items-center gap-2 animate-fade-up">
          <span
            className="text-xs font-medium px-2 py-0.5 rounded-full"
            style={{
              background:
                telemetry.mode === "cache_hit"
                  ? "rgba(16,185,129,0.15)"
                  : telemetry.mode === "live"
                  ? "rgba(34,211,238,0.15)"
                  : "rgba(100,116,139,0.15)",
              color:
                telemetry.mode === "cache_hit"
                  ? "#10b981"
                  : telemetry.mode === "live"
                  ? "#22d3ee"
                  : "#94a3b8",
            }}
          >
            {telemetry.mode === "cache_hit"
              ? "Cache Hit"
              : telemetry.mode === "live"
              ? "Live API"
              : "Simulation"}
          </span>
          <span className="text-xs text-slate-500">{telemetry.model?.split("/").pop()}</span>
        </div>
      )}
    </div>
  );
}
