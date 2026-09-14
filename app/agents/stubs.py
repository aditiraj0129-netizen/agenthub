from app.agents.competitor.agent import competitor_agent
from app.agents.mcp.agent import mcp_agent
from app.agents.receptionist.agent import receptionist_agent
from app.agents.onboarding.agent import onboarding_agent
from app.agents.invoice.agent import invoice_agent

AGENT_REGISTRY = {
    "receptionist": receptionist_agent,
    "competitor": competitor_agent,
    "mcp": mcp_agent,
    "onboarding": onboarding_agent,
    "invoice": invoice_agent,
}
