"use client";

const STRATEGIES = [
  { id: "none",          label: "None",          desc: "No optimization" },
  { id: "balanced",      label: "Balanced",       desc: "Distill + Window (recommended)" },
  { id: "sliding_window",label: "Sliding Window", desc: "Keep recent turns" },
  { id: "semantic_dedup",label: "Semantic Dedup", desc: "Remove repetitive text" },
  { id: "map_reduce",    label: "Map Reduce",     desc: "Heavy compression" },
  { id: "token_distill", label: "Token Distill",  desc: "Strip formatting bloat" },
];

interface ContextOptimizerProps {
  strategy: string;
  onStrategyChange: (s: string) => void;
  optimization: {
    tokens_saved: number;
    percent_saved: number;
    cost_saved_usd: number;
  } | null;
}

export default function ContextOptimizer({ strategy, onStrategyChange, optimization }: ContextOptimizerProps) {
  return (
    <div className="glass-card p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-300">Context Optimizer</span>
          <span className="text-xs px-2 py-0.5 rounded-full font-medium"
            style={{ background: "rgba(168,85,247,0.15)", color: "#a855f7" }}>
            EAIN Engine
          </span>
        </div>
        {optimization && optimization.tokens_saved > 0 && (
          <div className="flex items-center gap-3 text-xs">
            <span style={{ color: "#10b981" }}>
              ↓ {optimization.tokens_saved} tokens saved ({optimization.percent_saved}%)
            </span>
            <span style={{ color: "#10b981" }}>
              ${optimization.cost_saved_usd.toFixed(6)} saved
            </span>
          </div>
        )}
      </div>

      {/* Strategy Pills */}
      <div className="flex flex-wrap gap-2">
        {STRATEGIES.map((s) => (
          <button
            key={s.id}
            onClick={() => onStrategyChange(s.id)}
            className={`opt-pill text-xs px-3 py-1.5 rounded-full font-medium ${strategy === s.id ? "active" : "text-slate-400"}`}
            title={s.desc}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
