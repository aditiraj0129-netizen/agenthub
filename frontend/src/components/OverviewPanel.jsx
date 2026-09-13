const AGENTS = [
  {
    name: "Receptionist",
    color: "border-l-blue-400",
    model: "No LLM — deterministic business logic",
    does: "Reads incoming work requests (from the boss or a customer), finds a free employee from the 10-person team, assigns the task, and automatically marks them free again once the estimated time is up.",
    why: "Booking/assignment is a concrete rules problem, not a language problem — using an LLM here would add cost and unpredictability for no benefit.",
  },
  {
    name: "Competitor Watcher",
    color: "border-l-pink-400",
    model: "groq/openai/gpt-oss-20b (fast, tuned for summarization)",
    does: "Crawls registered competitor pages, stores each snapshot, compares the latest two versions, and asks the LLM to summarize only meaningful changes (pricing, features, messaging) — ignoring trivial wording differences.",
    why: "This is the RAG-style agent: retrieval (stored snapshots) grounds what the LLM is allowed to say, and a RAGAS faithfulness score checks the summary isn't hallucinating.",
  },
  {
    name: "MCP Tool Agent",
    color: "border-l-purple-400",
    model: "groq/openai/gpt-oss-120b (larger, tuned for precise tool selection)",
    does: "Decides which internal tool a request maps to (checking the time, sending a notification, deleting tracked data, etc). Read-only tools run instantly; anything that WRITES data is queued and requires a human to click Approve first.",
    why: "Separating 'the LLM decides' from 'the system executes' is what makes it safe to let an LLM control real tools — it can be wrong, but it can never act without a human in the loop for anything destructive.",
  },
];

const INFRA = [
  { label: "Gateway", detail: "FastAPI + API-key auth + rate limiting (10 req/min) + request logging" },
  { label: "Input Guardrail", detail: "Regex heuristics + protectai/deberta-v3-base-prompt-injection-v2 (local ML classifier) — blocks prompt injection before any agent sees it" },
  { label: "Output Guardrail", detail: "Regex-based PII redaction (emails, phone numbers) on every agent response" },
  { label: "Orchestration", detail: "LangGraph state machine routes every request through the same pipeline: gateway → input guard → router → agent → output guard → response" },
  { label: "Database", detail: "SQLite — employees, tasks, competitor sites/snapshots, MCP audit log, request metrics, and full pipeline traces, all persisted" },
  { label: "Evaluation", detail: "Per-agent latency & success rate, injection block rate, and RAGAS faithfulness scoring for the RAG agent's summaries" },
];

export default function OverviewPanel() {
  return (
    <div className="space-y-8">
      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5">
        <h2 className="text-lg font-bold text-gray-800 mb-2">What this is</h2>
        <p className="text-sm text-gray-600 leading-relaxed">
          <strong>AgentHub</strong> is a multi-agent AI platform built for a fictional 10-person startup,
          "Nimbus Solutions." Instead of one general-purpose chatbot, three specialist agents each handle
          a different job using a different model suited to that job, all behind a shared, hardened
          pipeline: authentication, rate limiting, prompt-injection defense, output filtering, and
          evaluation metrics apply identically no matter which agent is called. The design is built to
          scale — adding a 4th, 5th, or 10th agent means writing one new agent file and adding it to a
          registry, not rebuilding anything.
        </p>
      </div>

      <div>
        <h2 className="text-lg font-bold text-gray-800 mb-3">The Agents</h2>
        <div className="space-y-3">
          {AGENTS.map((a) => (
            <div key={a.name} className={`bg-white border-l-4 ${a.color} border-t border-r border-b border-gray-200 rounded-xl shadow-sm p-4`}>
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h3 className="font-bold text-gray-800">{a.name}</h3>
                <span className="text-xs font-mono text-gray-400 bg-gray-50 px-2 py-0.5 rounded-full border border-gray-200">
                  {a.model}
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-2">{a.does}</p>
              <p className="text-xs text-gray-400 mt-2 italic">{a.why}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-lg font-bold text-gray-800 mb-3">Shared Infrastructure</h2>
        <div className="grid md:grid-cols-2 gap-3">
          {INFRA.map((item) => (
            <div key={item.label} className="bg-white border border-gray-200 rounded-xl shadow-sm p-4">
              <p className="font-semibold text-sm text-gray-800">{item.label}</p>
              <p className="text-xs text-gray-500 mt-1">{item.detail}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
