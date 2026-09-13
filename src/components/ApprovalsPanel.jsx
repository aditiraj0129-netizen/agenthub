import { useEffect, useState } from "react";
import { api } from "../lib/api";

export default function ApprovalsPanel() {
  const [pending, setPending] = useState({});
  const [auditLog, setAuditLog] = useState([]);

  async function load() {
    try {
      setPending(await api.getPendingApprovals());
      setAuditLog(await api.getAuditLog());
    } catch {}
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 4000);
    return () => clearInterval(interval);
  }, []);

  async function handleApprove(id) {
    await api.approveCall(id);
    load();
  }

  async function handleReject(id) {
    await api.rejectCall(id);
    load();
  }

  const pendingEntries = Object.entries(pending);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-bold text-lg mb-2 text-brand-purple">Pending Approvals</h3>
        {pendingEntries.length === 0 ? (
          <p className="text-gray-400 italic">Nothing waiting on approval right now.</p>
        ) : (
          <div className="space-y-2">
            {pendingEntries.map(([id, call]) => (
              <div key={id} className="bg-white/80 rounded-xl shadow p-4 flex justify-between items-center">
                <div>
                  <p className="font-mono text-sm text-gray-500">{id}</p>
                  <p className="font-semibold">{call.tool}</p>
                  <p className="text-xs text-gray-500">{JSON.stringify(call.params)}</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => handleApprove(id)} className="bg-green-500 text-white px-3 py-1 rounded-lg text-sm hover:opacity-90">
                    Approve
                  </button>
                  <button onClick={() => handleReject(id)} className="bg-red-400 text-white px-3 py-1 rounded-lg text-sm hover:opacity-90">
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h3 className="font-bold text-lg mb-2 text-brand-purple">Audit Log</h3>
        <div className="bg-white/80 rounded-xl shadow divide-y max-h-64 overflow-y-auto">
          {auditLog.length === 0 && <p className="text-gray-400 italic p-4">No tool calls yet.</p>}
          {auditLog.slice().reverse().map((entry, i) => (
            <div key={i} className="p-3 text-sm">
              <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full text-white mr-2 ${entry.approved === "human" ? "bg-brand-purple" : entry.approved === "rejected" ? "bg-red-400" : "bg-brand-orange"}`}>
                {entry.approved}
              </span>
              <strong>{entry.tool}</strong>: {String(entry.result)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
