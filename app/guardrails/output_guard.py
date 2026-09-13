"""
This is your OUTPUT guardrail. Every agent response passes through here
BEFORE it's sent back to the user.

Checks:
  1. PII redaction — masks emails/phone numbers/card-like numbers if a model leaks them
  2. Schema validation — makes sure structured agent outputs (like calendar bookings)
     actually match the expected shape, so a broken response can't crash the frontend
"""
import re
from pydantic import BaseModel, ValidationError

PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone": re.compile(r"\b\d{10}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"),
    "card_like": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
}


def redact_pii(text: str) -> str:
    for label, pattern in PII_PATTERNS.items():
        text = pattern.sub(f"[REDACTED_{label.upper()}]", text)
    return text


def validate_schema(data: dict, schema: type[BaseModel]) -> dict:
    """
    Pass any expected pydantic schema (e.g. a BookingSchema) and this
    confirms the agent's structured output actually matches it.
    """
    try:
        validated = schema(**data)
        return {"valid": True, "data": validated.model_dump()}
    except ValidationError as e:
        return {"valid": False, "errors": str(e)}


def check_output(agent_text: str) -> dict:
    cleaned = redact_pii(agent_text)
    return {"clean_text": cleaned, "was_redacted": cleaned != agent_text}
