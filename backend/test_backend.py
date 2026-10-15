from fastapi.testclient import TestClient
from app.main import app
from app.services.token_service import count_text_tokens, count_messages_tokens, calculate_query_cost
from app.services.optimizer import optimize_context

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_models_list():
    res = client.get("/api/models")
    assert res.status_code == 200
    models = res.json()["models"]
    assert len(models) >= 5
    model_ids = [m["id"] for m in models]
    assert "gemini/gemini-1.5-flash" in model_ids
    assert "gpt-4o" in model_ids

def test_token_service():
    tokens = count_text_tokens("Enterprise AI Gateway with real-time telemetry.")
    assert tokens > 0
    cost = calculate_query_cost("gemini/gemini-1.5-flash", 1000, 500)
    assert cost > 0

def test_optimize_preview_map_reduce():
    long_doc = "This is an important section of an enterprise document. " * 30
    messages = [
        {"role": "system", "content": "You are a helpful enterprise AI assistant."},
        {"role": "user", "content": long_doc}
    ]
    
    payload = {
        "messages": messages,
        "strategy": "map_reduce",
        "target_tokens": 500,
        "model": "gemini/gemini-1.5-flash"
    }
    
    res = client.post("/api/optimize-preview", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["tokens_saved"] > 0
    assert data["metadata"]["percent_saved"] > 0

def test_optimize_preview_dedup():
    repetitive_text = "Redundant statement.\n\nRedundant statement.\n\nUnique statement."
    messages = [{"role": "user", "content": repetitive_text}]
    
    payload = {
        "messages": messages,
        "strategy": "semantic_dedup",
        "target_tokens": 1000,
        "model": "gpt-4o-mini"
    }
    
    res = client.post("/api/optimize-preview", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["tokens_saved"] > 0

if __name__ == "__main__":
    test_health()
    test_models_list()
    test_token_service()
    test_optimize_preview_map_reduce()
    test_optimize_preview_dedup()
    print("All backend tests PASSED successfully!")
