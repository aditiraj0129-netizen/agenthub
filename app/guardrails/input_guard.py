"""
This is your INPUT guardrail. Every user message passes through here
BEFORE any agent sees it.

Two layers of defense, cheapest check first (fail fast):
  Layer 1: regex heuristics — catches obvious attacks instantly, free, no model needed
  Layer 2: a real ML classifier (protectai/deberta-v3-base-prompt-injection)
           — catches sneaky/reworded injection attempts
"""
import re
# transformers is NOT imported at module level anymore — importing it alone
# (before even loading a model) pulls in a large chunk of memory. On a
# 512MB-RAM host, that import happening at startup for every agent's module
# chain was enough to OOM the whole app before it could even bind a port.

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

# --- Layer 2: ML-based detector ---
# Loaded LAZILY (on first actual use) instead of at import time. Loading at
# import time blocks the whole app from starting — including binding the
# port that Render/any host needs to see before it considers the service
# "up". On a resource-limited free-tier host, downloading + loading this
# model can take longer than the platform's startup timeout, causing a
# failed deploy even though the app would have worked fine once loaded.
_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        from transformers import pipeline  # imported here, only on first real use
        _classifier = pipeline(
            "text-classification",
            model="protectai/deberta-v3-base-prompt-injection-v2",
        )
    return _classifier


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
    result = _get_classifier()(user_text[:512])[0]  # model has a token limit
    is_injection = result["label"] == "INJECTION" and result["score"] > 0.85

    if is_injection:
        return {"safe": False, "reason": "ML classifier flagged injection", "risk_score": result["score"]}

    # Layer 3: NeMo Guardrails second opinion — LOCAL DEVELOPMENT ONLY.
    # Gated behind an env flag rather than always running, because
    # nemoguardrails' dependency weight caused repeated OOM crashes on
    # Render's free 512MB tier. Rather than keep fighting that limit for
    # a third defense layer, this stays available locally (where it works
    # and can be demoed) and is explicitly disabled in production — a
    # deliberate scope decision, not a bug: knowing which environment can
    # support which dependencies is itself part of shipping responsibly.
    import os
    if os.getenv("ENABLE_NEMO_GUARDRAILS", "false").lower() == "true":
        from app.guardrails.nemo_guard import nemo_check_input
        nemo_result = nemo_check_input(user_text)
        if not nemo_result["safe"]:
            return {"safe": False, "reason": nemo_result["reason"], "risk_score": 0.9}

    return {"safe": True, "reason": "clean", "risk_score": result["score"] if result["label"] == "INJECTION" else 0.0}
