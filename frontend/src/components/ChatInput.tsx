"use client";

import { useRef, KeyboardEvent } from "react";

interface ChatInputProps {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  isStreaming: boolean;
}

export default function ChatInput({ value, onChange, onSend, isStreaming }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isStreaming && value.trim()) onSend();
    }
  };

  const autoResize = () => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  };

  return (
    <div className="glass-card input-glow flex items-end gap-3 p-3">
      <textarea
        ref={textareaRef}
        className="flex-1 resize-none bg-transparent text-sm text-slate-200 placeholder:text-slate-600 outline-none leading-relaxed min-h-[40px] max-h-[160px]"
        placeholder="Message EAIN… (Enter to send, Shift+Enter for new line)"
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          autoResize();
        }}
        onKeyDown={handleKeyDown}
        disabled={isStreaming}
        rows={1}
      />

      {/* Send Button */}
      <button
        onClick={onSend}
        disabled={isStreaming || !value.trim()}
        className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center font-bold text-white transition-all duration-200 hover:scale-105 disabled:opacity-40 disabled:cursor-not-allowed disabled:scale-100"
        style={{
          background: isStreaming
            ? "rgba(100,116,139,0.3)"
            : "linear-gradient(135deg, #6366f1, #a855f7)",
        }}
      >
        {isStreaming ? (
          <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19V5m-7 7l7-7 7 7" />
          </svg>
        )}
      </button>
    </div>
  );
}
