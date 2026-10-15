import re
from typing import List, Dict, Any, Tuple
from app.services.token_service import count_messages_tokens, count_text_tokens

def sliding_window_prune(messages: List[Dict[str, Any]], target_tokens: int = 1500) -> List[Dict[str, Any]]:
    """Preserves system message and keeps the most recent turns within target token budget."""
    if not messages:
        return []

    system_msgs = [m for m in messages if m.get("role") == "system"]
    conversation = [m for m in messages if m.get("role") != "system"]

    budget = target_tokens - count_messages_tokens(system_msgs)
    if budget <= 100:
        budget = target_tokens // 2

    pruned_conv: List[Dict[str, Any]] = []
    # Work backwards from the newest message
    for msg in reversed(conversation):
        msg_tokens = count_text_tokens(msg.get("content", "")) + 4
        if budget - msg_tokens >= 0 or len(pruned_conv) == 0:
            pruned_conv.insert(0, msg)
            budget -= msg_tokens
        else:
            break

    return system_msgs + pruned_conv

def semantic_dedup_text(text: str, similarity_threshold: float = 0.70) -> str:
    """Removes repetitive sentences or paragraphs based on token set overlap."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) <= 1:
        # Try line by line
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    unique_paragraphs: List[str] = []
    seen_sets: List[set] = []

    for p in paragraphs:
        tokens = set(re.findall(r"\w+", p.lower()))
        if not tokens:
            continue
        
        is_duplicate = False
        for seen in seen_sets:
            overlap = len(tokens.intersection(seen)) / max(len(tokens), len(seen))
            if overlap >= similarity_threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_paragraphs.append(p)
            seen_sets.append(tokens)

    return "\n\n".join(unique_paragraphs)

def token_distill_text(text: str) -> str:
    """Strips excessive markdown indentation, duplicate blank lines, and semantic fluff."""
    # Collapse multiple blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", text)
    # Remove excessive horizontal spaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    # Strip common filler conversational prefixes
    cleaned = re.sub(r"(?i)\b(as an ai language model|in my humble opinion|needless to say|it is important to note that)\b,?", "", cleaned)
    return cleaned.strip()

def map_reduce_compress(text: str, chunk_size_words: int = 250) -> str:
    """Simulates Map-Reduce extractive reduction: chunks input, extracts salient anchor points."""
    words = text.split()
    if len(words) <= chunk_size_words:
        return text

    # Split into chunks
    chunks = [words[i:i + chunk_size_words] for i in range(0, len(words), chunk_size_words)]
    reduced_points: List[str] = []

    for idx, chunk in enumerate(chunks, 1):
        chunk_str = " ".join(chunk)
        # Extract the key sentences (e.g., first, middle, and last sentence of chunk)
        sentences = re.split(r"(?<=[.!?])\s+", chunk_str)
        if len(sentences) <= 2:
            reduced_points.append(chunk_str)
        else:
            salient = [sentences[0]]
            if len(sentences) > 3:
                salient.append(sentences[len(sentences) // 2])
            salient.append(sentences[-1])
            reduced_points.append(f"[Part {idx} Summary]: " + " ".join(salient))

    return "\n\n".join(reduced_points)

def optimize_context(
    messages: List[Dict[str, Any]], 
    strategy: str = "balanced", 
    target_tokens: int = 2000
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Main Context Optimizer Engine.
    Supported strategies:
      - 'none': Pass through
      - 'sliding_window': Recent turns prioritized
      - 'semantic_dedup': Strips redundant repetitive context
      - 'map_reduce': Extreme compression for massive inputs
      - 'token_distill': Strips formatting bloat & stop fluff
      - 'all_in_one': Applies distillation, deduplication, and sliding window
    """
    tokens_before = count_messages_tokens(messages)
    optimized_messages = [msg.copy() for msg in messages]

    if strategy == "sliding_window":
        optimized_messages = sliding_window_prune(optimized_messages, target_tokens=target_tokens)

    elif strategy == "semantic_dedup":
        for msg in optimized_messages:
            if isinstance(msg.get("content"), str):
                msg["content"] = semantic_dedup_text(msg["content"])

    elif strategy == "map_reduce":
        for msg in optimized_messages:
            if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                msg["content"] = map_reduce_compress(msg["content"])

    elif strategy == "token_distill":
        for msg in optimized_messages:
            if isinstance(msg.get("content"), str):
                msg["content"] = token_distill_text(msg["content"])

    elif strategy in ("all_in_one", "balanced"):
        for msg in optimized_messages:
            if isinstance(msg.get("content"), str):
                msg["content"] = token_distill_text(semantic_dedup_text(msg["content"]))
        optimized_messages = sliding_window_prune(optimized_messages, target_tokens=target_tokens)

    tokens_after = count_messages_tokens(optimized_messages)
    tokens_saved = max(0, tokens_before - tokens_after)
    percent_saved = round((tokens_saved / max(1, tokens_before)) * 100, 1)

    metadata = {
        "strategy": strategy,
        "tokens_before": tokens_before,
        "tokens_after": tokens_after,
        "tokens_saved": tokens_saved,
        "percent_saved": percent_saved,
    }

    return optimized_messages, metadata
