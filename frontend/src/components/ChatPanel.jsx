import { useState, useRef, useEffect } from "react";
import { api } from "../lib/api";

const AGENT_COLORS = {
  receptionist: "border-brand-orange text-brand-orange",
  competitor: "border-brand-pink text-brand-pink",
  mcp: "border-brand-purple text-brand-purple",
  blocked: "border-red-400 text-red-500",
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
    <div className="flex flex-col h-[70vh] bg-gray-50 border border-gray-200 rounded-2xl shadow-sm p-4">
      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[75%] px-4 py-2 rounded-2xl text-sm whitespace-pre-wrap border ${
                m.role === "user"
                  ? "bg-white border-brand-purple text-gray-800 rounded-br-sm"
                  : m.role === "system"
                  ? "bg-gray-100 border-gray-200 text-gray-500 italic"
                  : "bg-white border-gray-200 rounded-bl-sm"
              }`}
            >
              {m.intent && (
                <span
                  className={`inline-block text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full mb-1 border-2 bg-white ${AGENT_COLORS[m.intent] || "border-gray-300 text-gray-400"}`}
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
          className="bg-white border-2 border-brand-purple text-brand-purple px-5 py-2 rounded-xl font-medium hover:bg-brand-purple hover:text-white transition"
        >
          Send
        </button>
      </div>
    </div>
  );
}
