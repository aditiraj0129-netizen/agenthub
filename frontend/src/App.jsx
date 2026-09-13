import { useState } from "react";
import ChatPanel from "./components/ChatPanel";
import MetricsPanel from "./components/MetricsPanel";
import ApprovalsPanel from "./components/ApprovalsPanel";
import SitesPanel from "./components/SitesPanel";
import PipelineTrace from "./components/PipelineTrace";
import OverviewPanel from "./components/OverviewPanel";
import TeamPanel from "./components/TeamPanel";

const TABS = [
  { id: "overview", label: "Overview", color: "border-gray-400" },
  { id: "chat", label: "Chat", color: "border-brand-purple" },
  { id: "team", label: "Team & Tasks", color: "border-blue-400" },
  { id: "trace", label: "Pipeline Trace", color: "border-green-500" },
  { id: "metrics", label: "Metrics", color: "border-brand-pink" },
  { id: "approvals", label: "MCP Approvals", color: "border-brand-orange" },
  { id: "sites", label: "Competitor Sites", color: "border-brand-yellow" },
];

export default function App() {
  const [tab, setTab] = useState("overview");

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="flex flex-col items-center mb-2">
        <h1 className="text-4xl font-extrabold text-gray-800 border-b-4 border-brand-purple inline-block pb-2">
          AgentHub
        </h1>
        <p className="text-center text-gray-500 mt-2">Multi-agent AI platform · guardrails · evaluation · scalable</p>
        <div className="flex items-center gap-2 mt-4 bg-white border border-gray-200 rounded-full px-4 py-1.5 shadow-sm">
          <span className="text-xs text-gray-500">Built by <span className="font-semibold text-gray-700">Aditi Raj</span></span>
        </div>
      </div>

      <div className="flex justify-center gap-2 mb-6 flex-wrap">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 rounded-full font-medium text-sm transition border-2 ${
              tab === t.id
                ? `${t.color} text-gray-800 bg-white shadow-sm`
                : "border-gray-200 bg-gray-100 text-gray-500 hover:border-gray-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && <OverviewPanel />}
      {tab === "chat" && <ChatPanel />}
      {tab === "team" && <TeamPanel />}
      {tab === "trace" && <PipelineTrace />}
      {tab === "metrics" && <MetricsPanel />}
      {tab === "approvals" && <ApprovalsPanel />}
      {tab === "sites" && <SitesPanel />}
    </div>
  );
}
