from typing import Dict, List, Any
from pydantic_settings import BaseSettings

class ModelPricing:
    def __init__(self, prompt_per_1m: float, completion_per_1m: float, provider: str, display_name: str):
        self.prompt_per_1m = prompt_per_1m
        self.completion_per_1m = completion_per_1m
        self.provider = provider
        self.display_name = display_name

class Settings(BaseSettings):
    PROJECT_NAME: str = "EAIN Gateway"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "*"

    # API Keys
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Database & Cache (PostgreSQL + Redis with zero-cost fallbacks)
    DATABASE_URL: str = "sqlite+aiosqlite:///./eain.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Model Pricing Registry ($ per 1 Million tokens)
    MODEL_REGISTRY: Dict[str, ModelPricing] = {
        "gemini/gemini-1.5-flash": ModelPricing(
            prompt_per_1m=0.075,
            completion_per_1m=0.30,
            provider="Google",
            display_name="Gemini 1.5 Flash"
        ),
        "gemini/gemini-1.5-pro": ModelPricing(
            prompt_per_1m=1.25,
            completion_per_1m=5.00,
            provider="Google",
            display_name="Gemini 1.5 Pro"
        ),
        "gpt-4o-mini": ModelPricing(
            prompt_per_1m=0.15,
            completion_per_1m=0.60,
            provider="OpenAI",
            display_name="GPT-4o Mini"
        ),
        "gpt-4o": ModelPricing(
            prompt_per_1m=2.50,
            completion_per_1m=10.00,
            provider="OpenAI",
            display_name="GPT-4o"
        ),
        "claude-3-5-sonnet-20241022": ModelPricing(
            prompt_per_1m=3.00,
            completion_per_1m=15.00,
            provider="Anthropic",
            display_name="Claude 3.5 Sonnet"
        ),
        "claude-3-5-haiku-20241022": ModelPricing(
            prompt_per_1m=0.80,
            completion_per_1m=4.00,
            provider="Anthropic",
            display_name="Claude 3.5 Haiku"
        ),
        "groq/llama-3.3-70b-versatile": ModelPricing(
            prompt_per_1m=0.59,
            completion_per_1m=0.79,
            provider="Groq",
            display_name="Llama 3.3 70B (Groq LPU)"
        ),
    }

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
