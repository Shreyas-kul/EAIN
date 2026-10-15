"use client";

import { useState, useEffect, useCallback } from "react";
import { ChatMessage, TelemetryData, ModelInfo, TelemetryStats, OptimizationResult } from "@/types";
import { fetchModels, fetchTelemetryStats, streamChat, previewOptimization } from "@/lib/api";
import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import TelemetryPanel from "@/components/TelemetryPanel";
import ContextOptimizer from "@/components/ContextOptimizer";
import ModelSelector from "@/components/ModelSelector";

type View = "chat" | "dashboard";

export default function HomePage() {
  const [view, setView] = useState<View>("chat");
  const [sessionId, setSessionId] = useState("");
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState("gemini/gemini-1.5-flash");
  const [temperature, setTemperature] = useState(0.7);
  const [strategy, setStrategy] = useState("balanced");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [optimization, setOptimization] = useState<OptimizationResult | null>(null);
  const [stats, setStats] = useState<TelemetryStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState(false);

  // Safe client-only session ID
  useEffect(() => {
    setSessionId(`eain_${Math.random().toString(36).slice(2, 10)}`);
  }, []);

  // Load models + check backend health on mount
  useEffect(() => {
    fetchModels()
      .then((m) => {
        setModels(Array.isArray(m) ? m : []);
        setBackendOnline(true);
        if (m.length > 0) setSelectedModel(m[0].id);
      })
      .catch(() => {
        setModels([]);
        setBackendOnline(false);
      });
  }, []);

  // Refresh telemetry stats periodically
  useEffect(() => {
    if (!backendOnline) return;
    const load = () => fetchTelemetryStats().then(setStats).catch(() => {});
    load();
    const interval = setInterval(load, 15000);
    return () => clearInterval(interval);
  }, [backendOnline]);

  // Debounced optimization preview
  useEffect(() => {
    if (messages.length === 0 || strategy === "none" || !backendOnline) return;
    const timeout = setTimeout(() => {
      const rawMsgs = messages.map((m) => ({ role: m.role, content: m.content }));
      previewOptimization(rawMsgs, strategy, selectedModel)
        .then((data) => setOptimization(data?.metadata ?? null))
        .catch(() => {});
    }, 600);
    return () => clearTimeout(timeout);
  }, [messages, strategy, selectedModel, backendOnline]);

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    const userMsg: ChatMessage = {
      id: `${Date.now()}`,
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);
    setStreamingContent("");
    setTelemetry(null);
    setError(null);

    let accumulated = "";
    const allMsgs = [...messages, userMsg].map((m) => ({ role: m.role, content: m.content }));

    await streamChat(
      sessionId,
      allMsgs,
      selectedModel,
      strategy,
      temperature,
      (delta) => {
        accumulated += delta;
        setStreamingContent(accumulated);
      },
      (tel) => {
        setTelemetry(tel);
        fetchTelemetryStats().then(setStats).catch(() => {});
      },
      (err) => setError(err)
    );

    if (accumulated) {
      setMessages((prev) => [
        ...prev,
        { id: `${Date.now() + 1}`, role: "assistant", content: accumulated, timestamp: new Date() },
      ]);
    }
    setStreamingContent("");
    setIsStreaming(false);
  }, [input, isStreaming, messages, selectedModel, sessionId, strategy, temperature]);

  const clearChat = () => {
    setMessages([]);
    setTelemetry(null);
    setOptimization(null);
    setError(null);
  };

  // Safe stats values
  const safeStats = {
    total_queries: stats?.total_queries ?? 0,
    total_tokens_saved: stats?.total_tokens_saved ?? 0,
    total_cost_saved_usd: stats?.total_cost_saved_usd ?? 0,
    total_spent_usd: stats?.total_spent_usd ?? 0,
    avg_latency_ms: stats?.avg_latency_ms ?? 0,
  };

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "var(--bg-primary)" }}>
      {/* Background Orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute w-[600px] h-[600px] rounded-full -top-40 -left-40 opacity-[0.06]"
          style={{ background: "radial-gradient(circle, #a855f7, transparent 70%)" }} />
        <div className="absolute w-[500px] h-[500px] rounded-full -bottom-20 -right-20 opacity-[0.05]"
          style={{ background: "radial-gradient(circle, #22d3ee, transparent 70%)" }} />
      </div>

      {/* Sidebar */}
      <aside className="w-16 flex flex-col items-center py-5 gap-4 z-10"
        style={{ borderRight: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4"
          style={{ background: "linear-gradient(135deg, #6366f1, #a855f7)" }}>
          <span className="text-base font-black text-white">E</span>
        </div>

        <button onClick={() => setView("chat")} title="Chat"
          className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${view === "chat" ? "sidebar-active" : "hover:bg-white/5"}`}>
          <svg className="w-5 h-5" fill="none" stroke={view === "chat" ? "#22d3ee" : "#64748b"} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </button>

        <button onClick={() => setView("dashboard")} title="Dashboard"
          className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${view === "dashboard" ? "sidebar-active" : "hover:bg-white/5"}`}>
          <svg className="w-5 h-5" fill="none" stroke={view === "dashboard" ? "#a855f7" : "#64748b"} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </button>

        <button onClick={clearChat} title="Clear Chat"
          className="mt-auto w-10 h-10 rounded-xl flex items-center justify-center hover:bg-white/5 transition-all duration-200">
          <svg className="w-5 h-5" fill="none" stroke="#64748b" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </aside>

      {/* Left Config Panel */}
      <div className="w-64 flex flex-col gap-3 p-3 overflow-y-auto z-10"
        style={{ borderRight: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="px-1 pt-1">
          <h1 className="text-base font-black gradient-text">EAIN</h1>
          <p className="text-xs text-slate-600">Enterprise AI Gateway</p>
        </div>

        {/* Backend status */}
        <div className="glass-card px-3 py-2 flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${backendOnline ? "pulse-dot" : ""}`}
            style={{ background: backendOnline ? "#10b981" : "#ef4444" }} />
          <span className="text-xs" style={{ color: backendOnline ? "#10b981" : "#ef4444" }}>
            Backend {backendOnline ? "Online" : "Offline"}
          </span>
        </div>

        <ModelSelector
          models={models}
          selected={selectedModel}
          onSelect={setSelectedModel}
          temperature={temperature}
          onTemperatureChange={setTemperature}
        />

        <div className="glass-card px-3 py-2">
          <p className="text-xs text-slate-500">Session</p>
          <p className="text-xs font-mono text-slate-400 truncate">{sessionId || "initializing…"}</p>
        </div>

        {/* Cumulative stats */}
        <div className="space-y-2">
          <p className="text-xs text-slate-500 px-1">Cumulative Stats</p>
          <div className="grid grid-cols-2 gap-2">
            {[
              { label: "Queries", value: safeStats.total_queries.toLocaleString(), color: "#22d3ee" },
              { label: "Tokens Saved", value: safeStats.total_tokens_saved.toLocaleString(), color: "#a855f7" },
              { label: "Cost Saved", value: `$${safeStats.total_cost_saved_usd.toFixed(4)}`, color: "#10b981" },
              { label: "Avg Latency", value: `${safeStats.avg_latency_ms.toFixed(0)}ms`, color: "#f59e0b" },
            ].map((item) => (
              <div key={item.label} className="glass-card p-2">
                <p className="text-xs text-slate-500">{item.label}</p>
                <p className="text-sm font-bold" style={{ color: item.color }}>{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Area */}
      <main className="flex-1 flex flex-col overflow-hidden z-10">
        {/* Top Bar */}
        <div className="flex items-center justify-between px-5 py-3"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-300">
              {view === "chat" ? "Chat" : "Dashboard"}
            </span>
            {isStreaming && (
              <span className="flex items-center gap-1.5 text-xs" style={{ color: "#22d3ee" }}>
                <span className="w-1.5 h-1.5 rounded-full pulse-dot" style={{ background: "#22d3ee" }} />
                Generating…
              </span>
            )}
          </div>
          {error && (
            <span className="text-xs px-3 py-1 rounded-full"
              style={{ background: "rgba(239,68,68,0.1)", color: "#f87171" }}>
              {error.slice(0, 60)}
            </span>
          )}
        </div>

        {/* Chat View */}
        {view === "chat" && (
          <>
            <ChatWindow messages={messages} isStreaming={isStreaming} streamingContent={streamingContent} />
            <div className="px-4 pb-2">
              <ContextOptimizer strategy={strategy} onStrategyChange={setStrategy} optimization={optimization} />
            </div>
            <div className="px-4 pb-4">
              <ChatInput value={input} onChange={setInput} onSend={handleSend} isStreaming={isStreaming} />
            </div>
          </>
        )}

        {/* Dashboard View */}
        {view === "dashboard" && (
          <div className="flex-1 overflow-y-auto p-5 space-y-5">
            <div>
              <h2 className="text-base font-semibold text-slate-300 mb-3">Cumulative Enterprise Metrics</h2>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {[
                  { label: "Total Queries", value: safeStats.total_queries.toLocaleString(), color: "#22d3ee" },
                  { label: "Tokens Saved", value: safeStats.total_tokens_saved.toLocaleString(), color: "#a855f7" },
                  { label: "Cost Saved", value: `$${safeStats.total_cost_saved_usd.toFixed(4)}`, color: "#10b981" },
                  { label: "Avg Latency", value: `${safeStats.avg_latency_ms.toFixed(0)} ms`, color: "#f59e0b" },
                ].map((item) => (
                  <div key={item.label} className="glass-card p-5 telemetry-card">
                    <p className="text-xs text-slate-500 mb-2">{item.label}</p>
                    <p className="text-2xl font-bold" style={{ color: item.color }}>{item.value}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Model Catalog */}
            <div>
              <h2 className="text-base font-semibold text-slate-300 mb-3">
                Available Models {models.length > 0 && <span className="text-slate-500 text-xs">({models.length})</span>}
              </h2>
              {models.length === 0 ? (
                <div className="glass-card p-4 text-center text-sm text-slate-500">
                  Start the backend to see available models
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-2">
                  {models.map((m) => (
                    <div key={m.id} className="glass-card px-4 py-3 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-slate-200">{m.name ?? m.id}</p>
                        <p className="text-xs text-slate-500">{m.id}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        {(m.prompt_per_1m ?? 0) === 0 && (
                          <span className="text-xs px-2 py-0.5 rounded-full font-bold"
                            style={{ background: "rgba(16,185,129,0.15)", color: "#10b981" }}>FREE</span>
                        )}
                        <span className="text-xs text-slate-500">
                          {(m.prompt_per_1m ?? 0) === 0 ? "Free tier" : `$${m.prompt_per_1m}/1M in`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Last Telemetry */}
            {telemetry && (
              <div>
                <h2 className="text-base font-semibold text-slate-300 mb-3">Last Query Telemetry</h2>
                <div className="glass-card p-4 grid grid-cols-3 gap-4">
                  {[
                    { label: "TTFT", value: `${(telemetry.ttft_ms ?? 0).toFixed(1)} ms`, color: "#22d3ee" },
                    { label: "Tokens/sec", value: `${telemetry.tokens_per_sec ?? 0}`, color: "#a855f7" },
                    { label: "Cost", value: `$${(telemetry.cost_usd ?? 0).toFixed(6)}`, color: "#10b981" },
                    { label: "Tokens In", value: (telemetry.tokens_in ?? 0).toLocaleString(), color: "#6366f1" },
                    { label: "Tokens Out", value: (telemetry.tokens_out ?? 0).toLocaleString(), color: "#ec4899" },
                    { label: "Latency", value: `${(telemetry.latency_ms ?? 0).toFixed(0)} ms`, color: "#f59e0b" },
                  ].map((item) => (
                    <div key={item.label}>
                      <p className="text-xs text-slate-500">{item.label}</p>
                      <p className="text-lg font-bold" style={{ color: item.color }}>{item.value}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Right Telemetry Panel */}
      <aside className="w-60 p-3 overflow-hidden z-10"
        style={{ borderLeft: "1px solid rgba(255,255,255,0.06)" }}>
        <TelemetryPanel telemetry={telemetry} isStreaming={isStreaming} />
      </aside>
    </div>
  );
}
