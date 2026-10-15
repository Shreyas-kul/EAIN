"use client";

import { ModelInfo } from "@/types";

interface ModelSelectorProps {
  models: ModelInfo[];
  selected: string;
  onSelect: (id: string) => void;
  temperature: number;
  onTemperatureChange: (t: number) => void;
}

const PROVIDER_COLORS: Record<string, string> = {
  "Google": "#22d3ee",
  "Groq": "#f59e0b",
  "OpenRouter (Free)": "#10b981",
  "HuggingFace (Free)": "#ec4899",
  "OpenAI": "#10b981",
  "Anthropic": "#a855f7",
};

export default function ModelSelector({ models = [], selected, onSelect, temperature, onTemperatureChange }: ModelSelectorProps) {
  const selectedModel = models.find((m) => m.id === selected);
  const isFree = selectedModel?.prompt_per_1m === 0 && selectedModel?.completion_per_1m === 0;

  return (
    <div className="glass-card p-4 space-y-3">
      {/* Label */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-slate-300">AI Model</span>
        {isFree && (
          <span className="text-xs px-2 py-0.5 rounded-full font-bold"
            style={{ background: "rgba(16,185,129,0.15)", color: "#10b981" }}>
            FREE
          </span>
        )}
      </div>

      {/* Model Dropdown */}
      <select
        className="w-full rounded-xl px-3 py-2 text-sm font-medium text-slate-200 appearance-none cursor-pointer"
        style={{
          background: "rgba(255,255,255,0.06)",
          border: "1px solid rgba(255,255,255,0.1)",
          outline: "none",
        }}
        value={selected}
        onChange={(e) => onSelect(e.target.value)}
      >
        {models.map((m) => (
          <option key={m.id} value={m.id} style={{ background: "#0e0e1a" }}>
            {m.name} ({m.provider})
          </option>
        ))}
      </select>

      {/* Provider + Pricing info */}
      {selectedModel && (
        <div className="flex items-center justify-between text-xs">
          <span className="font-medium px-2 py-0.5 rounded-md"
            style={{
              background: `${PROVIDER_COLORS[selectedModel.provider] || "#64748b"}18`,
              color: PROVIDER_COLORS[selectedModel.provider] || "#94a3b8"
            }}>
            {selectedModel.provider}
          </span>
          <span style={{ color: "#64748b" }}>
            {isFree ? "Free tier" : `In $${selectedModel.prompt_per_1m}/M · Out $${selectedModel.completion_per_1m}/M`}
          </span>
        </div>
      )}

      {/* Temperature */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-slate-400">Temperature</span>
          <span className="text-xs font-mono font-bold" style={{ color: "#a855f7" }}>{temperature.toFixed(1)}</span>
        </div>
        <input
          type="range"
          min={0}
          max={2}
          step={0.1}
          value={temperature}
          onChange={(e) => onTemperatureChange(parseFloat(e.target.value))}
          className="w-full h-1 rounded-full appearance-none cursor-pointer"
          style={{ accentColor: "#a855f7" }}
        />
        <div className="flex justify-between text-xs mt-1" style={{ color: "#475569" }}>
          <span>Precise</span>
          <span>Creative</span>
        </div>
      </div>
    </div>
  );
}
