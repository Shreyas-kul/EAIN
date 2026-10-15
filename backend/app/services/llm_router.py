import os
import time
import json
import asyncio
from typing import AsyncGenerator, List, Dict, Any
import litellm
from app.core.config import settings
from app.services.token_service import count_messages_tokens, count_text_tokens, calculate_query_cost

# Ensure litellm does not crash if optional telemetry tools are missing
litellm.telemetry = False

def setup_environment_keys():
    """Sync settings with os.environ for LiteLLM provider discovery."""
    if settings.GEMINI_API_KEY:
        os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
    if settings.OPENAI_API_KEY:
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    if settings.ANTHROPIC_API_KEY:
        os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
    if settings.GROQ_API_KEY:
        os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
    if settings.OPENROUTER_API_KEY:
        os.environ["OPENROUTER_API_KEY"] = settings.OPENROUTER_API_KEY
    if settings.HUGGINGFACE_API_KEY:
        os.environ["HUGGINGFACE_API_KEY"] = settings.HUGGINGFACE_API_KEY
        os.environ["HF_TOKEN"] = settings.HUGGINGFACE_API_KEY

async def mock_stream_response(model: str, messages: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
    """Fallback high-speed mock streamer when no API keys are provided, allowing instant testability."""
    start_time = time.perf_counter()
    tokens_in = count_messages_tokens(messages)
    
    user_query = messages[-1].get("content", "Hello") if messages else "Hello"
    sample_reply = (
        f"⚡ **[EAIN Universal Engine Response]**\n\n"
        f"Processed query via simulated `{model}` execution.\n\n"
        f"Your context has been validated and parsed through the EAIN high-throughput pipeline. "
        f"To unlock live cloud provider inference across Google Gemini, OpenAI, Claude, or Groq, "
        f"provide your API keys in the `.env` configuration file or in the frontend header.\n\n"
        f"Key metrics for this query are calculated in real-time below."
    )
    
    words = sample_reply.split(" ")
    accumulated_output = ""
    ttft_ms = None

    # Simulate realistic network delay (TTFT ~ 120ms)
    await asyncio.sleep(0.12)
    ttft_ms = round((time.perf_counter() - start_time) * 1000, 2)

    for word in words:
        chunk = word + " "
        accumulated_output += chunk
        yield f"event: token\ndata: {json.dumps({'delta': chunk})}\n\n"
        await asyncio.sleep(0.02) # ~50 words/sec

    total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    tokens_out = count_text_tokens(accumulated_output)
    tps = round(tokens_out / max(0.001, (total_latency_ms / 1000.0)), 1)
    cost_usd = calculate_query_cost(model, tokens_in, tokens_out)

    telemetry = {
        "model": model,
        "ttft_ms": ttft_ms,
        "latency_ms": total_latency_ms,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens_per_sec": tps,
        "cost_usd": cost_usd,
        "status": "success",
        "mode": "demo_simulation"
    }
    yield f"event: telemetry\ndata: {json.dumps(telemetry)}\n\n"

async def stream_llm_response(
    model: str, 
    messages: List[Dict[str, Any]], 
    temperature: float = 0.7
) -> AsyncGenerator[str, None]:
    """
    Streams response from LiteLLM with real-time telemetry (TTFT, TPS, Cost).
    Falls back gracefully to mock demonstration if API keys are not supplied.
    """
    setup_environment_keys()
    
    # Check if a relevant API key exists for the target provider
    has_key = (
        ("gemini" in model and os.getenv("GEMINI_API_KEY")) or
        ("gpt" in model and os.getenv("OPENAI_API_KEY")) or
        ("claude" in model and os.getenv("ANTHROPIC_API_KEY")) or
        ("groq" in model and os.getenv("GROQ_API_KEY")) or
        ("openrouter" in model and os.getenv("OPENROUTER_API_KEY")) or
        ("huggingface" in model and (os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN"))) or
        bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY"))
    )

    if not has_key:
        async for chunk in mock_stream_response(model, messages):
            yield chunk
        return

    start_time = time.perf_counter()
    tokens_in = count_messages_tokens(messages)
    accumulated_output = ""
    ttft_ms = None

    try:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True
        )

        async for chunk in response:
            content = chunk.choices[0].delta.content or ""
            if content:
                if ttft_ms is None:
                    ttft_ms = round((time.perf_counter() - start_time) * 1000, 2)
                accumulated_output += content
                yield f"event: token\ndata: {json.dumps({'delta': content})}\n\n"

        total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        tokens_out = count_text_tokens(accumulated_output)
        tps = round(tokens_out / max(0.001, (total_latency_ms / 1000.0)), 1)
        cost_usd = calculate_query_cost(model, tokens_in, tokens_out)

        telemetry = {
            "model": model,
            "ttft_ms": ttft_ms or round(total_latency_ms * 0.4, 2),
            "latency_ms": total_latency_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "tokens_per_sec": tps,
            "cost_usd": cost_usd,
            "status": "success",
            "mode": "live"
        }
        yield f"event: telemetry\ndata: {json.dumps(telemetry)}\n\n"

    except Exception as exc:
        # If API call fails (e.g. rate limit, bad key), stream error and fall back cleanly
        yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
