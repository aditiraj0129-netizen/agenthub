import { useState, useRef, useEffect } from "react";
import { api } from "../lib/api";

const AGENT_COLORS = {
  receptionist: "bg-brand-orange",
  competitor: "bg-brand-pink",
  mcp: "bg-brand-purple",
  blocked: "bg-red-500",
};

export default function ChatPanel() {
  const [messages, setMessages] = useState([
    { role: "system", text: "Ask me to book something, track a competitor, or run a tool." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    if (!input.trim() || loading) return;
    const userMsg = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const result = await api.chat(userMsg.text);
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          text: result.response,
          intent: result.was_blocked ? "blocked" : result.intent,
        },
      ]);
    } catch (e) {
      setMessages((prev) => [...prev, { role: "agent", text: "Error reaching the server.", intent: "blocked" }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[70vh] bg-white/70 backdrop-blur rounded-2xl shadow-xl p-4">
      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[75%] px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap ${
                m.role === "user"
                  ? "bg-brand-purple text-white rounded-br-sm"
                  : m.role === "system"
                  ? "bg-gray-100 text-gray-500 italic"
                  : "bg-white shadow rounded-bl-sm"
              }`}
            >
              {m.intent && (
                <span
                  className={`inline-block text-[10px] uppercase tracking-wide text-white px-2 py-0.5 rounded-full mb-1 ${AGENT_COLORS[m.intent] || "bg-gray-400"}`}
                >
                  {m.intent}
                </span>
              )}
              <div>{m.text}</div>
            </div>
          </div>
        ))}
        {loading && <div className="text-sm text-gray-400 italic">Agent is thinking…</div>}
        <div ref={bottomRef} />
      </div>

      <div className="mt-3 flex gap-2">
        <input
          className="flex-1 rounded-xl border border-gray-200 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-brand-purple"
          placeholder="Type a message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button
          onClick={send}
          className="bg-brand-purple text-white px-5 py-2 rounded-xl font-medium hover:opacity-90 transition"
        >
          Send
        </button>
      </div>
    </div>
  );
}
