"""
6th agent: drafts (never sends) a payment follow-up email. Uses an LLM
because free-text drafting genuinely benefits from one, unlike the
Receptionist/Onboarding agents. Sending is intentionally NOT implemented
here — that would be a write action requiring the same MCP approval
gate as everything else that changes real-world state.
"""
import os
import litellm
from dotenv import load_dotenv

load_dotenv()


def invoice_agent(user_input: str) -> str:
    prompt = f"""Draft a brief, polite payment follow-up email based on this request: "{user_input}"
Keep it under 80 words. Do not include a subject line, just the body."""

    response = litellm.completion(
        model=os.getenv("INVOICE_MODEL", "groq/openai/gpt-oss-20b"),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
    )
    draft = response["choices"][0]["message"]["content"].strip()
    return f"[DRAFT ONLY — not sent] {draft}"
