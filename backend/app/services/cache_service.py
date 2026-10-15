import json
import hashlib
import time
from typing import Optional, Dict, Any
from app.core.config import settings

class CacheService:
    """
    Hybrid Redis + In-Memory Cache Service.
    - Connects to Redis if available.
    - Gracefully falls back to In-Memory TTL cache if Redis server is offline.
    """

    def __init__(self):
        self.redis_client = None
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._init_redis()

    def _init_redis(self):
        try:
            import redis
            client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=0.2
            )
            client.ping()
            self.redis_client = client
        except Exception:
            # Fall back to in-memory cache smoothly
            self.redis_client = None

    def _make_key(self, prompt: str, model: str) -> str:
        h = hashlib.sha256(f"{model}:{prompt.strip()}".encode()).hexdigest()
        return f"eain:cache:{h}"

    def get_cached_response(self, prompt: str, model: str) -> Optional[Dict[str, Any]]:
        """Checks for cached query result to return instant 0-cost response."""
        key = self._make_key(prompt, model)

        # 1. Check Redis
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception:
                pass

        # 2. Check Memory Fallback
        entry = self._memory_cache.get(key)
        if entry:
            if time.time() < entry["expires_at"]:
                return entry["data"]
            else:
                del self._memory_cache[key]

        return None

    def set_cached_response(self, prompt: str, model: str, response_text: str, telemetry: Dict[str, Any], ttl_seconds: int = 3600):
        """Caches query response and telemetry for future instant 0-cost retrieval."""
        key = self._make_key(prompt, model)
        payload = {
            "response": response_text,
            "telemetry": {
                **telemetry,
                "cost_usd": 0.0,
                "latency_ms": 4.5,
                "ttft_ms": 2.1,
                "mode": "cache_hit"
            }
        }

        # 1. Try Redis
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl_seconds, json.dumps(payload))
                return
            except Exception:
                pass

        # 2. Memory Fallback
        self._memory_cache[key] = {
            "expires_at": time.time() + ttl_seconds,
            "data": payload
        }

cache_service = CacheService()
