import { useEffect, useState } from "react";
import { api } from "../lib/api";

const CARD_COLORS = ["bg-brand-orange", "bg-brand-pink", "bg-brand-purple", "bg-brand-yellow"];

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
          <StatCard label="Total Calls" value={metrics._overall.total_calls} color="bg-brand-purple" />
          <StatCard label="Success Rate" value={`${metrics._overall.success_rate}%`} color="bg-brand-pink" />
          <StatCard label="Injection Block Rate" value={`${metrics._overall.injection_block_rate}%`} color="bg-brand-orange" />
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        {agentKeys.map((agent, i) => (
          <div key={agent} className="bg-white/80 rounded-2xl shadow p-4">
            <h3 className={`text-sm font-bold uppercase tracking-wide mb-2 text-white inline-block px-2 py-0.5 rounded-full ${CARD_COLORS[i % CARD_COLORS.length]}`}>
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
    <div className={`${color} text-white rounded-2xl shadow-lg p-4 text-center`}>
      <p className="text-3xl font-extrabold">{value}</p>
      <p className="text-xs uppercase tracking-wide opacity-90">{label}</p>
    </div>
  );
}
