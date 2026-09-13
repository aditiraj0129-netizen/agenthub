"""
This is your INPUT guardrail. Every user message passes through here
BEFORE any agent sees it.

Two layers of defense, cheapest check first (fail fast):
  Layer 1: regex heuristics — catches obvious attacks instantly, free, no model needed
  Layer 2: a real ML classifier (protectai/deberta-v3-base-prompt-injection)
           — catches sneaky/reworded injection attempts
"""
import re
from transformers import pipeline

# --- Layer 1: fast heuristic patterns ---
SUSPICIOUS_PATTERNS = [
    r"ignore (all|any|previous|the above) instructions",
    r"you are now",
    r"system prompt",
    r"disregard (your|all) (rules|guidelines)",
    r"act as (if|though) you (have no|are not) restrictions",
    r"reveal your (system|instructions|prompt)",
    r"</?(system|instructions)>",
]

_compiled_patterns = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS]

# --- Layer 2: ML-based detector (loads once, reused for every request) ---
_classifier = pipeline(
    "text-classification",
    model="protectai/deberta-v3-base-prompt-injection-v2",
)


def check_input(user_text: str, max_length: int = 2000) -> dict:
    """
    Returns: {"safe": bool, "reason": str, "risk_score": float}
    """
    # 0. Basic size validation
    if len(user_text) > max_length:
        return {"safe": False, "reason": "Input too long", "risk_score": 1.0}
    if not user_text.strip():
        return {"safe": False, "reason": "Empty input", "risk_score": 1.0}

    # 1. Regex heuristic layer
    for pattern in _compiled_patterns:
        if pattern.search(user_text):
            return {"safe": False, "reason": f"Matched pattern: {pattern.pattern}", "risk_score": 1.0}

    # 2. ML classifier layer
    result = _classifier(user_text[:512])[0]  # model has a token limit
    is_injection = result["label"] == "INJECTION" and result["score"] > 0.85

    if is_injection:
        return {"safe": False, "reason": "ML classifier flagged injection", "risk_score": result["score"]}

    return {"safe": True, "reason": "clean", "risk_score": result["score"] if result["label"] == "INJECTION" else 0.0}
