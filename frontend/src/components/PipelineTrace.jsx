import { useEffect, useState } from "react";
import { api } from "../lib/api";

const STAGE_ORDER = ["gateway", "input_guard", "router", "agent", "output_guard", "response"];

const STAGE_LABELS = {
  gateway: "Gateway",
  input_guard: "Input Guardrail",
  router: "Router",
  agent: "Agent",
  output_guard: "Output Guardrail",
  response: "Response",
};

const STAGE_COLORS = {
  gateway: "border-gray-400 text-gray-600",
  input_guard: "border-brand-orange text-brand-orange",
  router: "border-brand-purple text-brand-purple",
  agent: "border-brand-pink text-brand-pink",
  output_guard: "border-brand-orange text-brand-orange",
  response: "border-green-500 text-green-600",
};

export default function PipelineTrace() {
  const [trace, setTrace] = useState(null);

  async function load() {
    try {
      const result = await api.getLatestTrace();
      setTrace(result);
    } catch {}
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, []);

  if (!trace || !trace.request_id) {
    return <p className="text-gray-400 italic">Send a chat message first to see it flow through the pipeline.</p>;
  }

  const stageMap = Object.fromEntries(trace.stages.map((s) => [s.stage, s]));
  const wasBlocked = trace.stages.some((s) => s.detail.includes("BLOCKED") || s.detail.includes("blocked"));

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-xl p-3">
        <p className="text-xs text-gray-400">Request ID</p>
        <p className="font-mono text-sm text-gray-700">{trace.request_id}</p>
      </div>

      <div className="flex flex-col gap-2">
        {STAGE_ORDER.map((stageKey, i) => {
          const stage = stageMap[stageKey];
          const isBlockedHere = stage?.detail?.toLowerCase().includes("block");
          const active = !!stage;

          return (
            <div key={stageKey} className="flex items-start gap-3">
              <div className="flex flex-col items-center">
                <div
                  className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold bg-white ${
                    active ? STAGE_COLORS[stageKey] : "border-gray-200 text-gray-300"
                  } ${isBlockedHere ? "border-red-500 text-red-500" : ""}`}
                >
                  {i + 1}
                </div>
                {i < STAGE_ORDER.length - 1 && (
                  <div className={`w-0.5 h-6 ${active ? "bg-gray-300" : "bg-gray-100"}`} />
                )}
              </div>
              <div className={`flex-1 pb-2 ${active ? "" : "opacity-40"}`}>
                <p className={`text-sm font-semibold ${isBlockedHere ? "text-red-500" : "text-gray-800"}`}>
                  {STAGE_LABELS[stageKey]}
                </p>
                {stage && (
                  <>
                    <p className="text-xs text-gray-500">{stage.detail}</p>
                    <p className="text-[10px] text-gray-300">{stage.created_at}</p>
                  </>
                )}
                {!stage && <p className="text-xs text-gray-300">Not reached (request was blocked earlier)</p>}
              </div>
            </div>
          );
        })}
      </div>

      {wasBlocked && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-600">
          This request was stopped by the guardrail layer before reaching any agent — exactly the protection the pipeline is designed to provide.
        </div>
      )}
    </div>
  );
}
