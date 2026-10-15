// Shared types for EAIN frontend

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
}

export interface TelemetryData {
  model: string;
  ttft_ms: number;
  latency_ms: number;
  tokens_in: number;
  tokens_out: number;
  tokens_per_sec: number;
  cost_usd: number;
  status: string;
  mode: "live" | "demo_simulation" | "cache_hit";
}

export interface OptimizationResult {
  strategy: string;
  tokens_before: number;
  tokens_after: number;
  tokens_saved: number;
  percent_saved: number;
  cost_before_est_usd: number;
  cost_after_est_usd: number;
  cost_saved_usd: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  prompt_per_1m: number;
  completion_per_1m: number;
}

export interface JevEvaluation {
  intent: string;
  complexity_score: number;
  recommended_model: string;
  needs_vision: boolean;
  is_coding: boolean;
  suggested_max_tokens: number;
  decision_latency_ms: number;
}

export interface TelemetryStats {
  total_queries: number;
  total_tokens_saved: number;
  total_cost_saved_usd: number;
  total_spent_usd: number;
  avg_latency_ms: number;
}
