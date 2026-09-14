"""
NVIDIA NeMo Guardrails as a second, independent opinion alongside the
regex heuristics + local ML classifier in input_guard.py. This uses
LLM-based reasoning ("does this message try to manipulate the system?")
rather than pattern matching, so it can catch attacks phrased in ways
neither the regex nor the classifier has seen before — the tradeoff is
it's slower and costs an LLM call, which is why it's lazy-loaded and
only used as a secondary check, not the first line of defense.
"""
import os

_rails_app = None


def _get_rails():
    global _rails_app
    if _rails_app is None:
        from nemoguardrails import LLMRails, RailsConfig
        config_path = os.path.join(os.path.dirname(__file__), "nemo_config")
        config = RailsConfig.from_path(config_path)
        _rails_app = LLMRails(config)
    return _rails_app


def nemo_check_input(user_text: str) -> dict:
    try:
        rails = _get_rails()
        response = rails.generate(messages=[{"role": "user", "content": user_text}])
        blocked = "I'm sorry" in response.get("content", "") or "blocked" in response.get("content", "").lower()
        return {"safe": not blocked, "reason": "NeMo self-check flagged this input" if blocked else "clean"}
    except Exception as e:
        # If NeMo itself fails (network issue, model hiccup), don't let that
        # take down the whole guardrail layer — fall back to "safe" here
        # since the regex + local classifier layers already ran first.
        return {"safe": True, "reason": f"NeMo check unavailable: {e}"}
