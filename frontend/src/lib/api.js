/*
One shared place for talking to the backend. Every component imports
from here instead of hardcoding fetch calls — so if the API key or
base URL ever changes, you fix it in exactly one file.
*/
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY || "dev-secret-key-change-me";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "x-api-key": API_KEY,
      ...options.headers,
    },
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export const api = {
  chat: (message) => request("/chat", { method: "POST", body: JSON.stringify({ message }) }),
  getMetrics: () => request("/metrics"),
  getLogs: () => request("/logs"),
  getPendingApprovals: () => request("/mcp/pending"),
  approveCall: (id, password) =>
    request(`/mcp/approve/${id}`, { method: "POST", body: JSON.stringify({ password }) }),
  rejectCall: (id) => request(`/mcp/reject/${id}`, { method: "POST" }),
  getAuditLog: () => request("/mcp/audit-log"),
  getSites: () => request("/competitor/sites"),
  getLatestTrace: () => request("/trace/latest"),
  getEmployees: () => request("/employees"),
  getTasks: () => request("/tasks"),
  registerSite: (site_id, url) =>
    request("/competitor/sites", { method: "POST", body: JSON.stringify({ site_id, url }) }),
};
