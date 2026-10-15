import tiktoken
from typing import List, Dict, Any, Optional
from app.core.config import settings

# Cached encoder
try:
    _encoder = tiktoken.get_encoding("cl100k_base")
except Exception:
    _encoder = None

def count_text_tokens(text: str) -> int:
    """Returns exact token count for text using cl100k_base or standard heuristic fallback."""
    if not text:
        return 0
    if _encoder:
        try:
            return len(_encoder.encode(text))
        except Exception:
            pass
    # Fallback heuristic: roughly ~4 characters per token
    return max(1, len(text) // 4)

def count_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    """Calculates total input tokens for a list of conversation messages."""
    total = 3  # baseline priming tokens
    for msg in messages:
        total += 4  # message overhead: role + tags
        content = msg.get("content", "")
        if isinstance(content, str):
            total += count_text_tokens(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    total += count_text_tokens(part["text"])
    return total

def calculate_query_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculates cost in USD for the query based on model registry pricing."""
    pricing = settings.MODEL_REGISTRY.get(model_name)
    if not pricing:
        # Check if stripped model name matches (e.g. without prefix)
        for key, p in settings.MODEL_REGISTRY.items():
            if key in model_name or model_name in key:
                pricing = p
                break

    if not pricing:
        # Default fallback to budget model tier (~$0.15/1M prompt, $0.60/1M completion)
        return round((prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060), 6)

    prompt_cost = (prompt_tokens / 1_000_000.0) * pricing.prompt_per_1m
    completion_cost = (completion_tokens / 1_000_000.0) * pricing.completion_per_1m
    return round(prompt_cost + completion_cost, 6)
