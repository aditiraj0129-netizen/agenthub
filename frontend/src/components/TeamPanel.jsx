import { useEffect, useState } from "react";
import { api } from "../lib/api";

function timeUntil(isoString) {
  if (!isoString) return null;
  const diffMs = new Date(isoString + "Z") - new Date();
  if (diffMs <= 0) return "any moment now";
  const mins = Math.ceil(diffMs / 60000);
  return `~${mins} min left`;
}

export default function TeamPanel() {
  const [employees, setEmployees] = useState([]);
  const [tasks, setTasks] = useState([]);

  async function load() {
    try {
      setEmployees(await api.getEmployees());
      setTasks(await api.getTasks());
    } catch {}
  }

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-bold text-lg mb-2 text-gray-800">Team (10)</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {employees.map((emp) => (
            <div
              key={emp.employee_id}
              className={`bg-white border-l-4 rounded-xl shadow-sm p-3 ${
                emp.status === "free" ? "border-l-green-500" : "border-l-red-400"
              }`}
            >
              <p className="font-semibold text-sm text-gray-800">{emp.name}</p>
              <p className="text-xs text-gray-400">{emp.department}</p>
              <p className={`text-xs mt-1 font-bold uppercase ${emp.status === "free" ? "text-green-600" : "text-red-500"}`}>
                {emp.status}
              </p>
              {emp.status === "busy" && (
                <p className="text-[10px] text-gray-400">{timeUntil(emp.free_at)}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="font-bold text-lg mb-2 text-gray-800">Task Log</h3>
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm divide-y max-h-64 overflow-y-auto">
          {tasks.length === 0 && <p className="text-gray-400 italic p-4">No tasks assigned yet.</p>}
          {tasks.map((t) => (
            <div key={t.id} className="p-3 text-sm">
              <span
                className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border-2 bg-white mr-2 ${
                  t.status === "completed" ? "border-green-500 text-green-600" : "border-brand-orange text-brand-orange"
                }`}
              >
                {t.status}
              </span>
              <span className="text-gray-400 text-xs">[{t.requester_type}]</span> {t.description}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
