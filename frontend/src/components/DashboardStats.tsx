"use client";

import { TelemetryStats } from "@/types";

interface DashboardStatsProps {
  stats: TelemetryStats | null;
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="glass-card p-4 flex flex-col gap-1">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-lg font-bold" style={{ color }}>{value}</span>
    </div>
  );
}

export default function DashboardStats({ stats }: DashboardStatsProps) {
  if (!stats) return null;

  const totalQueries = stats.total_queries ?? 0;
  const totalTokensSaved = stats.total_tokens_saved ?? 0;
  const totalCostSaved = stats.total_cost_saved_usd ?? 0;
  const avgLatency = stats.avg_latency_ms ?? 0;

  return (
    <div className="grid grid-cols-2 gap-3">
      <StatCard label="Total Queries" value={totalQueries.toLocaleString()} color="#22d3ee" />
      <StatCard label="Tokens Saved" value={totalTokensSaved.toLocaleString()} color="#a855f7" />
      <StatCard label="Cost Saved" value={`$${totalCostSaved.toFixed(4)}`} color="#10b981" />
      <StatCard label="Avg Latency" value={`${avgLatency.toFixed(0)} ms`} color="#f59e0b" />
    </div>
  );
}
