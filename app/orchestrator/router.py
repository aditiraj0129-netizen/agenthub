INTENT_KEYWORDS = {
    "receptionist": ["book", "appointment", "schedule a call", "call me", "slot", "reservation",
                      "assign", "task", "work", "customer needs", "boss wants", "new work",
                      "free employee", "who is free"],
    "competitor": ["competitor", "rival", "pricing page", "track", "watch site", "changes on"],
    "mcp": ["tool", "run the tool", "mcp", "execute", "approve", "notification", "notify",
            "what time", "current time", "send a message", "delete", "remove tracking",
            "add team member", "add employee", "new team member", "hire", "remove team member",
            "delete employee", "fire", "remove employee"],
}


def classify_intent(user_input: str) -> str:
    text = user_input.lower()
    scores = {agent: sum(1 for kw in kws if kw in text) for agent, kws in INTENT_KEYWORDS.items()}
    best_agent = max(scores, key=scores.get)

    if scores[best_agent] == 0:
        return "receptionist"

    return best_agent
