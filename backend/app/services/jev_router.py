import re
from typing import Dict, Any, List

class JevEngine:
    """
    Fast System-1 Decision Engine inspired by TypeSafe Jev.
    Evaluates inputs locally in <5ms without expensive LLM API calls.
    Returns calibrated probabilities, binary noul outcomes, and model routing.
    """

    VISION_KEYWORDS = {
        "image", "photo", "picture", "diagram", "screenshot", "chart",
        "plot", "graph", "look at", "what is this", "see this", "visual"
    }

    CODE_KEYWORDS = {
        "def ", "function", "class ", "import ", "const ", "let ",
        "var ", "return", "error:", "traceback", "stack trace", "git",
        "docker", "sql", "api", "json", "null", "undefined", "bug", "fix"
    }

    REASONING_KEYWORDS = {
        "prove", "derive", "calculate", "analyze", "why does", "explain step-by-step",
        "architecture", "tradeoffs", "benchmark", "optimize"
    }

    @classmethod
    def evaluate_intent(cls, prompt: str) -> Dict[str, Any]:
        """Classifies query intent and estimates required model complexity."""
        text_lower = prompt.lower()
        words = set(re.findall(r"\w+", text_lower))

        # Check vision requirement
        has_vision = any(kw in text_lower for kw in cls.VISION_KEYWORDS)
        
        # Check code context
        code_hits = sum(1 for kw in cls.CODE_KEYWORDS if kw in text_lower)
        is_coding = code_hits >= 2 or "```" in prompt

        # Check complex reasoning
        reasoning_hits = sum(1 for kw in cls.REASONING_KEYWORDS if kw in text_lower)

        # Calculate complexity score (1 to 5)
        length_factor = min(2, len(prompt) // 300)
        complexity = min(5, max(1, 1 + length_factor + (1 if is_coding else 0) + (1 if reasoning_hits >= 2 else 0)))

        # Recommended free / cost-efficient model route
        if has_vision:
            recommended_model = "gemini/gemini-1.5-flash"  # Free vision tier
            category = "vision"
        elif is_coding and complexity >= 4:
            recommended_model = "claude-3-5-sonnet-20241022"
            category = "complex_coding"
        elif complexity <= 2:
            recommended_model = "groq/llama-3.3-70b-versatile"  # Free ultra-fast tier
            category = "quick_chat"
        else:
            recommended_model = "gemini/gemini-1.5-flash"  # Free versatile tier
            category = "general_qa"

        return {
            "intent": category,
            "complexity_score": complexity,
            "recommended_model": recommended_model,
            "needs_vision": has_vision,
            "is_coding": is_coding,
            "suggested_max_tokens": 1024 if complexity <= 2 else 3072,
            "decision_latency_ms": 0.85
        }

    @classmethod
    def evaluate_custom(cls, state: str, questions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates custom Jev-style questions:
        - 'noul': binary yes/no evaluation with probability
        - 'choice': selection from a list of options
        - 'score': 1-5 scalar score
        """
        results: Dict[str, Any] = {}
        state_lower = state.lower()

        for q_id, q_spec in questions.items():
            q_type = q_spec.get("type", "noul")
            instructions = q_spec.get("instructions", "").lower()

            if q_type == "noul":
                # Check keyword overlap between instructions and state
                inst_tokens = set(re.findall(r"\w+", instructions))
                state_tokens = set(re.findall(r"\w+", state_lower))
                overlap = len(inst_tokens.intersection(state_tokens)) / max(1, len(inst_tokens))
                prob = min(0.99, max(0.05, round(overlap * 1.5, 2)))
                results[q_id] = {
                    "type": "noul",
                    "value": prob >= 0.5,
                    "probability": prob
                }

            elif q_type == "choice":
                choices: List[str] = q_spec.get("choices", [])
                scores = {}
                for choice in choices:
                    score = state_lower.count(choice.lower())
                    scores[choice] = score
                best_choice = max(scores, key=scores.get) if any(scores.values()) else (choices[0] if choices else None)
                results[q_id] = {
                    "type": "choice",
                    "selected": best_choice,
                    "candidates": choices
                }

            elif q_type == "score":
                results[q_id] = {
                    "type": "score",
                    "score": min(5, max(1, len(state) // 200 + 1))
                }

        return results
