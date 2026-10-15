from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.services.token_service import count_messages_tokens, count_text_tokens, calculate_query_cost
from app.services.optimizer import optimize_context
from app.services.llm_router import stream_llm_response

router = APIRouter()

class Message(BaseModel):
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text content")

class OptimizePreviewRequest(BaseModel):
    messages: List[Message]
    strategy: str = Field("balanced", description="none | sliding_window | semantic_dedup | map_reduce | token_distill | balanced")
    target_tokens: int = Field(2000, description="Target token budget for sliding window")
    model: str = Field("gemini/gemini-1.5-flash", description="Model used for cost projection")

class ChatStreamRequest(BaseModel):
    messages: List[Message]
    model: str = Field("gemini/gemini-1.5-flash", description="Target model identifier")
    strategy: str = Field("balanced", description="Context optimization strategy")
    target_tokens: int = Field(2000, description="Target token budget")
    temperature: float = Field(0.7, ge=0.0, le=2.0)

@router.get("/health")
def health_check():
    """Service health verification."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@router.get("/models")
def get_supported_models():
    """Returns list of all available models with pricing metadata."""
    models_data = []
    for model_id, pricing in settings.MODEL_REGISTRY.items():
        models_data.append({
            "id": model_id,
            "name": pricing.display_name,
            "provider": pricing.provider,
            "prompt_per_1m": pricing.prompt_per_1m,
            "completion_per_1m": pricing.completion_per_1m,
        })
    return {"models": models_data}

@router.post("/optimize-preview")
def preview_context_optimization(payload: OptimizePreviewRequest):
    """
    Simulates real-time context reduction without calling LLM.
    Returns token deltas, compressed message structure, and projected savings.
    """
    raw_msgs = [m.model_dump() for m in payload.messages]
    optimized_msgs, meta = optimize_context(
        messages=raw_msgs,
        strategy=payload.strategy,
        target_tokens=payload.target_tokens
    )

    # Cost savings projection assuming standard ~300 output tokens
    cost_before = calculate_query_cost(payload.model, meta["tokens_before"], 300)
    cost_after = calculate_query_cost(payload.model, meta["tokens_after"], 300)
    cost_saved = max(0.0, round(cost_before - cost_after, 6))

    return {
        "metadata": {
            **meta,
            "cost_before_est_usd": cost_before,
            "cost_after_est_usd": cost_after,
            "cost_saved_usd": cost_saved,
        },
        "optimized_messages": optimized_msgs
    }

@router.post("/chat/stream")
async def chat_stream(payload: ChatStreamRequest):
    """
    Executes real-time SSE streaming with automatic context optimization
    and micro-telemetry (TTFT, TPS, Cost/Query).
    """
    raw_msgs = [m.model_dump() for m in payload.messages]
    
    # 1. Apply context optimization pipeline
    optimized_msgs, opt_meta = optimize_context(
        messages=raw_msgs,
        strategy=payload.strategy,
        target_tokens=payload.target_tokens
    )

    # 2. Return SSE Streaming Response
    return StreamingResponse(
        stream_llm_response(
            model=payload.model,
            messages=optimized_msgs,
            temperature=payload.temperature
        ),
        media_type="text/event-stream"
    )
