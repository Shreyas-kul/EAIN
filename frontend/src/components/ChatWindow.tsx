"use client";

import { ChatMessage } from "@/types";
import { useEffect, useRef } from "react";

interface ChatWindowProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  streamingContent: string;
}

function UserBubble({ content }: { content: string }) {
  return (
    <div className="flex justify-end mb-4 animate-fade-up">
      <div className="bubble-user px-4 py-3 max-w-[75%] text-sm text-white leading-relaxed">
        {content}
      </div>
    </div>
  );
}

function AiBubble({ content, isStreaming }: { content: string; isStreaming?: boolean }) {
  return (
    <div className="flex justify-start mb-4 animate-fade-up">
      <div className="flex gap-3 max-w-[82%]">
        {/* Avatar */}
        <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-0.5"
          style={{ background: "linear-gradient(135deg, #22d3ee, #a855f7)" }}>
          <span className="text-xs font-black text-white">E</span>
        </div>
        {/* Bubble */}
        <div className={`bubble-ai px-4 py-3 text-sm text-slate-200 leading-relaxed whitespace-pre-wrap ${isStreaming ? "streaming-cursor" : ""}`}>
          {content || <span className="text-slate-500 italic text-xs">Thinking…</span>}
        </div>
      </div>
    </div>
  );
}

export default function ChatWindow({ messages, isStreaming, streamingContent }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-1">
      {messages.length === 0 && !isStreaming && (
        <div className="flex flex-col items-center justify-center h-full text-center space-y-4 pt-20">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, rgba(34,211,238,0.2), rgba(168,85,247,0.2))", border: "1px solid rgba(168,85,247,0.3)" }}>
            <span className="text-3xl font-black gradient-text">E</span>
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-200">EAIN Universal AI Gateway</h2>
            <p className="text-sm text-slate-500 mt-1">Multi-model · Context Optimizer · Real-time Telemetry</p>
          </div>
          <div className="flex flex-wrap gap-2 justify-center mt-4">
            {["Summarize a document", "Write Python code", "Explain quantum computing", "Vision analysis"].map((s) => (
              <span key={s}
                className="text-xs px-3 py-1.5 rounded-full cursor-pointer transition-all duration-200 hover:scale-105"
                style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", color: "#94a3b8" }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {messages.map((msg) =>
        msg.role === "user" ? (
          <UserBubble key={msg.id} content={msg.content} />
        ) : msg.role === "assistant" ? (
          <AiBubble key={msg.id} content={msg.content} />
        ) : null
      )}

      {isStreaming && <AiBubble content={streamingContent} isStreaming />}

      <div ref={bottomRef} />
    </div>
  );
}
