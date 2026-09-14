AgentHub — A production-style multi-agents AI platform with guardrails, evaluation, and human-in-the-loop MCP tool approval
LIVE DEMO:https://lnkd.in/p/gb3nBGMj

A production-style multi-agent AI system built for a fictional 10-person startup, **Nimbus Solutions**. Instead of one general-purpose chatbot, three specialist agents each handle a different job with a model suited to that job — all sitting behind a shared, hardened pipeline that enforces security, validation, and observability identically no matter which agent is called.

 Why multi-agent, not one LLM

A single generic LLM handling everything is the common student-project pattern. This project instead treats routing as an infrastructure problem: a request for "book a task" doesn't need the same model, latency budget, or trust level as a request that could delete data. Splitting agents by responsibility means each one can be tuned, evaluated, and secured independently — and the system can grow by adding agents, not by making one model do more things.

 Architecture
 
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
▼ ▼ 
Receptionist  Competitor   Watcher MCP Tool Agent
(no LLM — (RAG: crawl → store (tool-calling  +.    
rules engine) →   diff →    summarize)   human-approval gate)

│ │ │
└────────────┴──────────────────┘
▼

Output Guardrail ── PII redaction
▼

SQLite ── employees · tasks · sites/snapshots · audit log · metrics · pipeline traces


## The five agents

| Agent | Model | Job |
|---|---|---|
| Receptionist | None (deterministic logic) | Assigns incoming work (from the boss or a customer) to a free employee out of 10, tracks estimated completion time, and auto-releases them back to "free" on a background schedule. |
| Competitor Watcher | `groq/openai/gpt-oss-20b` (fast) | Crawls registered competitor pages, stores snapshots, and asks the LLM to summarize only *meaningful* changes between the last two snapshots — scored for faithfulness with RAGAS so hallucinated claims are visible, not hidden. |
| MCP Tool Agent | `groq/openai/gpt-oss-120b` (precise) | Decides which internal tool a request maps to. Read-only tools execute immediately; any tool that writes/changes data — including adding or removing team members — is queued and requires explicit human approval (password-gated) before it runs. |
| Onboarding Agent| None (deterministic logic) | Assigns a new hire a buddy from currently-free employees and returns a standard checklist. Added post-launch to demonstrate one-file agent scalability. |
| Invoice Agent | `groq/openai/gpt-oss-20b` | Drafts a payment follow-up email. Deliberately does not send anything — drafting is read-like; sending would be a write action requiring the same MCP approval gate as everything else. |

Model choice is intentionally different per agent and set via `.env`, not hardcoded, so any model can be swapped without touching agent logic.

Security & robustness

- Three-layer prompt-injection defense**: instant regex heuristics catch obvious attacks, a local ML classifier (`protectai/deberta-v3-base-prompt-injection-v2`) catches reworded/subtle ones, and (in local development) NVIDIA NeMo Guardrails adds an LLM-reasoning-based check for attacks that evade pattern matching entirely.
- NeMo is gated behind `ENABLE_NEMO_GUARDRAILS` and runs locally only — its dependency footprint exceeded what Render's free 512MB tier could hold at runtime, a deliberate, documented scope tradeoff rather than an oversight.
- **Indirect injection defense**: content pulled from outside the system (crawled competitor pages) is sanitized for injection markers before it's ever inserted into an LLM prompt — the same defense the input guardrail applies to user messages, applied to the *other* place untrusted text enters the system.
- **Output guardrail**: every agent response passes through PII redaction before reaching the user.
- **API-key auth + rate limiting** on every endpoint via the gateway.
- **Human-in-the-loop approval gate** on all write-capable tools, requiring a password to confirm a known human is approving — not just any click. Every action is logged with a distinction between automated (read-only) and human-approved actions, and a write action can only ever be approved once.
- **Full request tracing**: every request is logged stage-by-stage (gateway → input guard → router → agent → output guard → response) into a `pipeline_trace` table, so any request's exact path — including where and why it was blocked — is queryable after the fact.

 Evaluation

- Per-agent latency, success rate, and call volume, tracked in real time via `/metrics`.
- Injection block rate, measured against actual adversarial test inputs (jailbreak personas, fake system overrides, translated instructions, spaced-letter evasion), not just assumed.
- RAGAS faithfulness scoring for the Competitor Watcher's RAG summaries — with a deliberate fix for a known limitation: the metric scores near-zero on "no change detected" answers since there's no factual claim to verify, so scoring is skipped for those cases rather than showing a misleading number.

 Data

Real persisted Postgres (via Supabase), not in-memory state or a local file — every table (employees, tasks, competitor sites/snapshots, MCP audit log, metrics, pipeline traces) survives a server restart and redeploy, and is inspectable directly through Supabase's own dashboard. Connection pooling is used to avoid per-query network/TLS handshake overhead.

Scalability

Adding a new agent requires exactly two changes: write the agent function, and add one line to `AGENT_REGISTRY` plus its routing keywords. Nothing else in the gateway, guardrails, orchestrator, or evaluation layer needs to change — proven in practice by adding the Onboarding and Invoice agents after the initial three.

 Tech stack

FastAPI · LangGraph · Postgres (Supabase) · React + Vite + Tailwind · Groq (LiteLLM) · HuggingFace Transformers · RAGAS · NVIDIA NeMo Guardrails (local) · APScheduler

Running it locally

Backend:**
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

Open `http://localhost:5173`. Requires a free [Groq API key](https://console.groq.com) and a [Supabase](https://supabase.com) Postgres connection string in `.env`.

 Deployment

- Backend**: Render (free tier), connected to this repo for auto-deploy on push.
- Frontend**: Vercel, root directory `frontend`, environment variables pointing at the Render backend URL.
- Database**: Supabase Postgres — chosen specifically because Render's free tier has no persistent disk, and SQLite would reset on every service sleep/wake cycle.

 Known limitations (honest, not hidden)

- Receptionist and Onboarding agents use keyword-based intent classification, not a learned classifier — a good next iteration.
- NeMo Guardrails runs locally only, not in the deployed version, due to free-tier memory constraints — see Security section above.
- RAGAS adds real dependency fragility (encountered and resolved multiple times during build, including a version-pinning issue and an import-time crash); worth monitoring on any future dependency upgrade.
- Rate limiting and auth are single-key/demo-grade; a real deployment would need per-user keys and OAuth.
- Render's free tier sleeps after 15 minutes of inactivity; the first request after sleep will be slow while it wakes up.
