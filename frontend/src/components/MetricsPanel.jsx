import { useEffect, useState } from "react";
import { api } from "../lib/api";

const CARD_COLORS = ["border-brand-orange", "border-brand-pink", "border-brand-purple", "border-brand-yellow"];

export default function MetricsPanel() {
  const [metrics, setMetrics] = useState(null);

  async function load() {
    try {
      setMetrics(await api.getMetrics());
    } catch {
      setMetrics(null);
    }
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000); // auto-refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (!metrics) return <p className="text-gray-400 italic">No metrics yet — send a chat message first.</p>;
  if (metrics.message) return <p className="text-gray-400 italic">{metrics.message}</p>;

  const agentKeys = Object.keys(metrics).filter((k) => k !== "_overall");

  return (
    <div className="space-y-6">
      {metrics._overall && (
        <div className="grid grid-cols-3 gap-4">
          <StatCard label="Total Calls" value={metrics._overall.total_calls} color="border-brand-purple" />
          <StatCard label="Success Rate" value={`${metrics._overall.success_rate}%`} color="border-brand-pink" />
          <StatCard label="Injection Block Rate" value={`${metrics._overall.injection_block_rate}%`} color="border-brand-orange" />
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        {agentKeys.map((agent, i) => (
          <div key={agent} className={`bg-white border-t-4 rounded-2xl shadow-sm p-4 ${CARD_COLORS[i % CARD_COLORS.length]}`}>
            <h3 className="text-sm font-bold uppercase tracking-wide mb-2 text-gray-700">
              {agent}
            </h3>
            <p className="text-2xl font-bold">{metrics[agent].avg_latency_ms} ms</p>
            <p className="text-xs text-gray-500">avg latency</p>
            <p className="text-sm mt-2">
              {metrics[agent].total_calls} calls · {metrics[agent].success_rate}% success
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div className={`bg-white border-t-4 ${color} rounded-2xl shadow-sm p-4 text-center`}>
      <p className="text-3xl font-extrabold text-gray-800">{value}</p>
      <p className="text-xs uppercase tracking-wide text-gray-400">{label}</p>
    </div>
  );
}
