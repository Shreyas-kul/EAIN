from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import router as api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FAANG-grade Universal Enterprise LLM Gateway with Context Window Optimizer and Telemetry"
)

# Enable CORS for universal global access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ORIGINS == "*" else settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} ⚡",
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_STR}/health",
        "models_url": f"{settings.API_V1_STR}/models"
    }
