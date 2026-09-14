"""
Defends against INDIRECT prompt injection — the case NeMo/regex/ML input
checks don't cover, because they only ever look at what the USER typed.
Here, the attack vector is different: a competitor's webpage, or a tool's
output, could itself contain text like "ignore previous instructions,"
and if that raw text gets pasted into an LLM prompt (which is exactly
what the Competitor Watcher does with crawled page text), the LLM can't
tell the difference between "text I'm summarizing" and "an instruction
I should follow." This strips/neutralizes suspicious patterns from
EXTERNAL content before it's ever allowed into a prompt.
"""
import re

INJECTION_MARKERS = [
    r"ignore (all|any|previous|the above) instructions",
    r"system prompt",
    r"you are now",
    r"disregard (your|all) (rules|guidelines)",
    r"</?(system|instructions)>",
    r"new (rule|directive|instruction)s?:",
]

_compiled = [re.compile(p, re.IGNORECASE) for p in INJECTION_MARKERS]


def sanitize_external_content(text: str, source_label: str = "external content") -> str:
    """
    Called on ANY text pulled from outside the system — crawled pages,
    tool results, third-party API responses — before it gets embedded
    into an LLM prompt. Doesn't block the whole request (a webpage
    having weird text shouldn't stop legitimate monitoring); instead it
    neutralizes just the suspicious lines so they can't be interpreted
    as instructions, while leaving the rest of the content intact.
    """
    sanitized = text
    found_injection = False

    for pattern in _compiled:
        if pattern.search(sanitized):
            found_injection = True
            sanitized = pattern.sub("[flagged content removed]", sanitized)

    if found_injection:
        print(f"[content_sanitizer] Neutralized suspicious content from {source_label}")

    return sanitized
