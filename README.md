AgentHub — A production-style multi-agents AI platform with guardrails, evaluation, and human-in-the-loop MCP tool approval

A production-style multi-agent AI system built for a fictional 10-person startup, **Nimbus Solutions**. Instead of one general-purpose chatbot, three specialist agents each handle a different job with a model suited to that job — all sitting behind a shared, hardened pipeline that enforces security, validation, and observability identically no matter which agent is called.

## Why multi-agent, not one LLM

A single generic LLM handling everything is the common student-project pattern. This project instead treats routing as an infrastructure problem: a request for "book a task" doesn't need the same model, latency budget, or trust level as a request that could delete data. Splitting agents by responsibility means each one can be tuned, evaluated, and secured independently — and the system can grow by adding agents, not by making one model do more things.

## Architecture
Client (React dashboard)
│ HTTPS + API key
▼

Gateway (FastAPI) ── auth · rate limiting · request logging
▼

Input Guardrail ── regex heuristics + local ML prompt-injection classifier
▼

Orchestrator (LangGraph) ── routes by intent
▼

┌────────────┬──────────────────┬─────────────────┐
▼ ▼ ▼
Receptionist Competitor Watcher MCP Tool Agent
(no LLM — (RAG: crawl → store (tool-calling +
rules engine) → diff → summarize) human-approval gate)
│ │ │
└────────────┴──────────────────┘
▼

Output Guardrail ── PII redaction
▼
SQLite ── employees · tasks · sites/snapshots · audit log · metrics · pipeline traces

The three agents

| Agent | Model | Job |
|---|---|---|
| **Receptionist** | None (deterministic logic) | Assigns incoming work (from the boss or a customer) to a free employee out of 10, tracks estimated completion time, and auto-releases them back to "free" on a background schedule. |
| **Competitor Watcher** | `groq/openai/gpt-oss-20b` (fast) | Crawls registered competitor pages, stores snapshots, and asks the LLM to summarize only *meaningful* changes between the last two snapshots — scored for faithfulness with RAGAS so hallucinated claims are visible, not hidden. |
| **MCP Tool Agent** | `groq/openai/gpt-oss-120b` (precise) | Decides which internal tool a request maps to. Read-only tools execute immediately; any tool that writes/changes data is queued and requires explicit human approval before it runs — the LLM can decide, but it can never act alone. |

Model choice is intentionally different per agent: the receptionist needs zero LLM cost since it's a rules problem, the watcher needs speed over depth, and the tool agent needs precision over speed. This is set via `.env`, not hardcoded, so any model can be swapped without touching agent logic.

## Security & robustness

- **Two-layer prompt-injection defense**: instant regex heuristics catch obvious attacks; a local ML classifier (`protectai/deberta-v3-base-prompt-injection-v2`) catches reworded/subtle ones. Both run before any agent or LLM ever sees the input.
- **Output guardrail**: every agent response passes through PII redaction before reaching the user.
- **API-key auth + rate limiting** on every endpoint via the gateway.
- **Human-in-the-loop approval gate** on all write-capable tools, with an immutable audit log distinguishing automated (read-only) actions from human-approved ones — and a write action can only ever be approved once (verified: a second approval attempt on a consumed ID fails).
- **Full request tracing**: every request is logged stage-by-stage (gateway → input guard → router → agent → output guard → response) into `pipeline_trace`, so any request's exact path — including where and why it was blocked — is queryable after the fact.

## Evaluation

- Per-agent latency, success rate, and call volume, tracked in real time via `/metrics`.
- Injection block rate, measured against actual adversarial test inputs, not just assumed.
- RAGAS faithfulness scoring for the Competitor Watcher's RAG summaries — with a deliberate fix for a known limitation: the metric scores near-zero on "no change detected" answers since there's no factual claim to verify, so scoring is skipped for those cases rather than showing a misleading number.

## Data

Real persisted SQLite (`agenthub.db`), not in-memory state — every table (employees, tasks, competitor sites/snapshots, MCP audit log, metrics, pipeline traces) survives a server restart and can be inspected directly with any SQLite browser.

## Scalability

Adding a new agent requires exactly two changes: write the agent function, and add one line to `AGENT_REGISTRY` in `app/agents/stubs.py` plus its routing keywords. Nothing else in the gateway, guardrails, orchestrator, or evaluation layer needs to change — that separation is the actual design goal of this project, not an afterthought.

## Tech stack

FastAPI · LangGraph · SQLite · React + Vite + Tailwind · Groq (LiteLLM) · HuggingFace Transformers · RAGAS · APScheduler

## Running it

**Backend:**
```bash
cd agenthub
source venv/bin/activate
uvicorn app.gateway.main:app --reload --port 8000
```

**Frontend:**
```bash
cd agenthub/frontend
npm run dev
```

Open `http://localhost:5173`. Requires a free [Groq API key](https://console.groq.com) in `.env`.

## Known limitations (honest, not hidden)

- Receptionist matching uses keyword-based intent classification, not a learned classifier — a good next iteration.
- RAGAS adds real dependency fragility (encountered and documented during build); a lighter self-scored groundedness check is a viable fallback if this ever needs to run somewhere without full ML dependencies.
- Rate limiting and auth are single-key/demo-grade; a real deployment would need per-user keys and OAuth.
