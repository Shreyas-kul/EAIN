import { ChatMessage, TelemetryData, ModelInfo, TelemetryStats } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api";

export async function fetchModels(): Promise<ModelInfo[]> {
  const res = await fetch(`${API_URL}/models`);
  const data = await res.json();
  return data.models;
}

export async function fetchTelemetryStats(): Promise<TelemetryStats> {
  const res = await fetch(`${API_URL}/telemetry/stats`);
  return res.json();
}

export async function fetchChatHistory(sessionId: string): Promise<ChatMessage[]> {
  const res = await fetch(`${API_URL}/history/${sessionId}`);
  const data = await res.json();
  return data.messages.map((m: any) => ({
    id: String(m.id),
    role: m.role,
    content: m.content,
    timestamp: new Date(m.created_at || Date.now()),
  }));
}

export async function previewOptimization(
  messages: { role: string; content: string }[],
  strategy: string,
  model: string
) {
  const res = await fetch(`${API_URL}/optimize-preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, strategy, model }),
  });
  return res.json();
}

export async function streamChat(
  sessionId: string,
  messages: { role: string; content: string }[],
  model: string,
  strategy: string,
  temperature: number,
  onToken: (delta: string) => void,
  onTelemetry: (data: TelemetryData) => void,
  onError: (err: string) => void
) {
  const response = await fetch(`${API_URL}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      messages,
      model,
      strategy,
      temperature,
      use_cache: true,
    }),
  });

  const reader = response.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const payload = JSON.parse(line.slice(6));
          if (payload.delta !== undefined) {
            onToken(payload.delta);
          } else if (payload.model) {
            onTelemetry(payload as TelemetryData);
          } else if (payload.error) {
            onError(payload.error);
          }
        } catch {}
      }
    }
  }
}
