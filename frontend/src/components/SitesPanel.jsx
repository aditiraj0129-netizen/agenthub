import { useEffect, useState } from "react";
import { api } from "../lib/api";

export default function SitesPanel() {
  const [sites, setSites] = useState({});
  const [siteId, setSiteId] = useState("");
  const [url, setUrl] = useState("");

  async function load() {
    try {
      setSites(await api.getSites());
    } catch {}
  }

  useEffect(() => {
    load();
  }, []);

  async function handleAdd() {
    if (!siteId.trim() || !url.trim()) return;
    await api.registerSite(siteId, url);
    setSiteId("");
    setUrl("");
    load();
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          className="flex-1 rounded-xl border border-gray-200 px-3 py-2"
          placeholder="site id (e.g. openai)"
          value={siteId}
          onChange={(e) => setSiteId(e.target.value)}
        />
        <input
          className="flex-1 rounded-xl border border-gray-200 px-3 py-2"
          placeholder="https://example.com/pricing"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button onClick={handleAdd} className="bg-white border-2 border-brand-pink text-brand-pink px-4 py-2 rounded-xl hover:bg-brand-pink hover:text-white transition">
          Add
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {Object.entries(sites).map(([id, info]) => (
          <div key={id} className="bg-white border border-gray-200 border-l-4 border-l-brand-yellow rounded-xl shadow-sm p-4">
            <p className="font-bold text-gray-800">{id}</p>
            <p className="text-xs text-gray-500 truncate">{info.url}</p>
            <p className="text-sm mt-2">{info.last_report || "No report yet."}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
