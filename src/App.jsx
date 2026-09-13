import { useState } from "react";
import ChatPanel from "./components/ChatPanel";
import MetricsPanel from "./components/MetricsPanel";
import ApprovalsPanel from "./components/ApprovalsPanel";
import SitesPanel from "./components/SitesPanel";

const TABS = [
  { id: "chat", label: "Chat", color: "bg-brand-purple" },
  { id: "metrics", label: "Metrics", color: "bg-brand-pink" },
  { id: "approvals", label: "MCP Approvals", color: "bg-brand-orange" },
  { id: "sites", label: "Competitor Sites", color: "bg-brand-yellow" },
];

export default function App() {
  const [tab, setTab] = useState("chat");

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-4xl font-extrabold text-center mb-1 bg-clip-text text-transparent bg-gradient-to-r from-brand-orange via-brand-pink to-brand-purple">
        AgentHub
      </h1>
      <p className="text-center text-gray-500 mb-6">Multi-agent AI platform · guardrails · evaluation · scalable</p>

      <div className="flex justify-center gap-2 mb-6 flex-wrap">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-full font-medium text-sm transition ${
              tab === t.id ? `${t.color} text-white shadow-lg` : "bg-white/60 text-gray-600 hover:bg-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "chat" && <ChatPanel />}
      {tab === "metrics" && <MetricsPanel />}
      {tab === "approvals" && <ApprovalsPanel />}
      {tab === "sites" && <SitesPanel />}
    </div>
  );
}
