"use client";
import { useEffect, useState } from "react";
import { getRecentAlerts, acknowledgeAlert } from "../lib/api";

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const load = async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await getRecentAlerts(120);
      setAlerts(data);
      setLoading(false);
    } catch (e) {
      console.error(e);
      setError(e);
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, []);

  const acknowledge = async (id) => {
    try {
      if (typeof window !== "undefined") {
        const ok = window.confirm("Confirm dispatch to field units? Vehicle will be flagged.");
        if (!ok) return;
      }
      await acknowledgeAlert(id);
      await load();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="rounded-xl border border-muted bg-surface p-3 h-[480px] overflow-auto animate-slide-up">
      <h2 className="text-lg font-semibold mb-2">Recent Alerts</h2>
      {loading && (
        <div className="text-sm mb-2 text-gray-500" aria-live="polite">Loading alerts…</div>
      )}
      {error && (
        <div className="text-sm mb-2" aria-live="assertive" style={{ color: 'var(--danger)' }}>
          Failed to load alerts: {String(error.message || error)}
        </div>
      )}
      <div className="space-y-2" aria-live="polite">
        {alerts.map((a) => (
          <div key={a.id} className="border rounded p-2 flex items-center justify-between">
            <div>
              <div className="font-semibold">
                {a.plate_number} [
                <span className="font-normal" style={{ color: a.status === 'stolen' ? 'var(--danger)' : a.status === 'suspicious' ? 'var(--warning)' : 'var(--success)' }}>
                  {a.status}
                </span>]
              </div>
              <div className="text-sm">Predicted: {a.predicted_latitude?.toFixed(5)}, {a.predicted_longitude?.toFixed(5)}</div>
              <div className="text-xs">{new Date(a.timestamp).toLocaleString()}</div>
            </div>
            <div className="flex gap-2">
              {a.acknowledged ? (
                <span className="text-sm" style={{ color: 'var(--success)' }}>Dispatched</span>
              ) : (
                <button onClick={() => acknowledge(a.id)} className="px-3 py-1 rounded text-white" style={{ background: 'var(--accent)' }}>
                  Ack & Dispatch
                </button>
              )}
            </div>
          </div>
        ))}
        {alerts.length === 0 && !error && (
          <div className="text-sm text-gray-500">No alerts yet.</div>
        )}
      </div>
    </div>
  );
}