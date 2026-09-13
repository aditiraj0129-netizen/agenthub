"""
Agent registry — the one file the orchestrator reads from.
"""
from app.agents.competitor.agent import competitor_agent
from app.agents.mcp.agent import mcp_agent
from app.agents.receptionist.agent import receptionist_agent

AGENT_REGISTRY = {
    "receptionist": receptionist_agent,
    "competitor": competitor_agent,
    "mcp": mcp_agent,
}
