import json
import base64
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from app.core.config import settings
from app.services.token_service import count_messages_tokens, count_text_tokens, calculate_query_cost
from app.services.optimizer import optimize_context
from app.services.llm_router import stream_llm_response
from app.services.vision_service import compress_image_opencv
from app.services.jev_router import JevEngine
from app.services.cache_service import cache_service
from app.db.session import AsyncSessionLocal
from app.db.models import ChatMessage, TelemetryLog

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
    session_id: str = Field("default", description="Unique conversation session ID")
    messages: List[Message]
    model: str = Field("gemini/gemini-1.5-flash", description="Target model identifier")
    strategy: str = Field("balanced", description="Context optimization strategy")
    target_tokens: int = Field(2000, description="Target token budget")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    use_cache: bool = Field(True, description="Enable Redis / Memory semantic query caching")

@router.get("/health")
def health_check():
    """Service health verification."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected (PostgreSQL / SQLite)",
        "cache": "connected (Redis / In-Memory)"
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

async def cached_stream_wrapper(
    session_id: str,
    model: str,
    last_user_query: str,
    optimized_msgs: List[Dict[str, Any]],
    temperature: float,
    opt_meta: Dict[str, Any],
    use_cache: bool
):
    """
    Streams response with Redis cache check, caching, and DB persistence.
    """
    # 1. Check Cache
    if use_cache:
        cached = cache_service.get_cached_response(last_user_query, model)
        if cached:
            response_text = cached.get("response", "")
            telemetry = cached.get("telemetry", {})
            words = response_text.split(" ")
            for word in words:
                yield f"event: token\ndata: {json.dumps({'delta': word + ' '})}\n\n"
            yield f"event: telemetry\ndata: {json.dumps(telemetry)}\n\n"
            return

    # 2. Stream Live / Simulation
    accumulated_text = ""
    telemetry_data = {}

    async for chunk in stream_llm_response(model=model, messages=optimized_msgs, temperature=temperature):
        yield chunk
        if chunk.startswith("event: token"):
            try:
                line = chunk.split("data: ", 1)[1].strip()
                parsed = json.loads(line)
                accumulated_text += parsed.get("delta", "")
            except Exception:
                pass
        elif chunk.startswith("event: telemetry"):
            try:
                line = chunk.split("data: ", 1)[1].strip()
                telemetry_data = json.loads(line)
            except Exception:
                pass

    # 3. Cache Result if successful
    if accumulated_text and telemetry_data and use_cache:
        cache_service.set_cached_response(last_user_query, model, accumulated_text, telemetry_data)

    # 4. Save to Database (PostgreSQL / SQLite)
    try:
        async with AsyncSessionLocal() as db:
            # User message
            user_msg = ChatMessage(
                session_id=session_id,
                role="user",
                content=last_user_query,
                model=model,
                tokens_in=opt_meta.get("tokens_after", 0)
            )
            # Assistant response
            asst_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=accumulated_text,
                model=model,
                tokens_out=telemetry_data.get("tokens_out", 0),
                cost_usd=telemetry_data.get("cost_usd", 0.0),
                latency_ms=telemetry_data.get("latency_ms", 0.0)
            )
            # Telemetry Log
            cost_before = calculate_query_cost(model, opt_meta.get("tokens_before", 0), telemetry_data.get("tokens_out", 0))
            cost_after = telemetry_data.get("cost_usd", 0.0)
            cost_saved = max(0.0, round(cost_before - cost_after, 6))

            t_log = TelemetryLog(
                session_id=session_id,
                model=model,
                strategy=opt_meta.get("strategy", "none"),
                tokens_saved=opt_meta.get("tokens_saved", 0),
                cost_saved=cost_saved,
                total_cost_usd=cost_after,
                total_latency_ms=telemetry_data.get("latency_ms", 0.0)
            )

            db.add_all([user_msg, asst_msg, t_log])
            await db.commit()
    except Exception:
        # DB failure should never break the stream to client
        pass

@router.post("/chat/stream")
async def chat_stream(payload: ChatStreamRequest):
    """
    Executes real-time SSE streaming with automatic context optimization,
    Redis caching, micro-telemetry (TTFT, TPS, Cost/Query), and Database logging.
    """
    raw_msgs = [m.model_dump() for m in payload.messages]
    last_user_msg = raw_msgs[-1]["content"] if raw_msgs else ""

    # 1. Context optimization
    optimized_msgs, opt_meta = optimize_context(
        messages=raw_msgs,
        strategy=payload.strategy,
        target_tokens=payload.target_tokens
    )

    # 2. SSE streaming with Redis caching and DB persistence
    return StreamingResponse(
        cached_stream_wrapper(
            session_id=payload.session_id,
            model=payload.model,
            last_user_query=last_user_msg,
            optimized_msgs=optimized_msgs,
            temperature=payload.temperature,
            opt_meta=opt_meta,
            use_cache=payload.use_cache
        ),
        media_type="text/event-stream"
    )

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Retrieves conversation history stored in PostgreSQL / SQLite."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
        )
        messages = result.scalars().all()
        return {
            "session_id": session_id,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "model": m.model,
                    "cost_usd": m.cost_usd,
                    "latency_ms": m.latency_ms,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in messages
            ]
        }

@router.get("/telemetry/stats")
async def get_telemetry_stats():
    """Aggregated enterprise metrics: total queries, tokens saved, and dollars saved."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(
                func.count(TelemetryLog.id).label("total_queries"),
                func.sum(TelemetryLog.tokens_saved).label("total_tokens_saved"),
                func.sum(TelemetryLog.cost_saved).label("total_cost_saved"),
                func.sum(TelemetryLog.total_cost_usd).label("total_spent_usd"),
                func.avg(TelemetryLog.total_latency_ms).label("avg_latency_ms")
            )
        )
        row = result.one()
        return {
            "total_queries": row.total_queries or 0,
            "total_tokens_saved": row.total_tokens_saved or 0,
            "total_cost_saved_usd": round(row.total_cost_saved or 0.0, 4),
            "total_spent_usd": round(row.total_spent_usd or 0.0, 4),
            "avg_latency_ms": round(row.avg_latency_ms or 0.0, 1)
        }

class VisionOptimizeRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded input image string")
    max_dimension: int = Field(768, description="Maximum width/height dimension")
    jpeg_quality: int = Field(80, description="JPEG compression quality (1-100)")

@router.post("/vision/optimize")
def optimize_vision_tokens(payload: VisionOptimizeRequest):
    """
    OpenCV Vision Token Compressor:
    Downscales images and reduces vision tokens by up to 70% before sending to Multimodal LLMs.
    """
    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        image_bytes = base64.b64decode(raw_b64)
        compressed_bytes, metadata = compress_image_opencv(
            image_bytes=image_bytes,
            max_dimension=payload.max_dimension,
            jpeg_quality=payload.jpeg_quality
        )
        compressed_b64 = base64.b64encode(compressed_bytes).decode("utf-8")
        return {
            "metadata": metadata,
            "optimized_image_base64": f"data:image/jpeg;base64,{compressed_b64}"
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Image compression failed: {str(exc)}")

class JevEvaluateRequest(BaseModel):
    prompt: str = Field(..., description="User prompt or state string to evaluate")
    custom_questions: Optional[Dict[str, Any]] = Field(None, description="Optional custom Jev questions")

@router.post("/jev/evaluate")
def evaluate_jev(payload: JevEvaluateRequest):
    """
    System-1 Fast Decision Evaluator (TypeSafe Jev inspired).
    Instantly classifies intent, checks vision requirements, and routes to the cheapest/free model.
    """
    decision = JevEngine.evaluate_intent(payload.prompt)
    custom_results = {}
    if payload.custom_questions:
        custom_results = JevEngine.evaluate_custom(payload.prompt, payload.custom_questions)
    
    return {
        "system_1_evaluation": decision,
        "custom_questions": custom_results
    }
