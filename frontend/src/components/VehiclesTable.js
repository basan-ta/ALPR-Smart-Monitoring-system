"use client";
import { useEffect, useMemo, useState } from "react";
import { getVehicles } from "../lib/api";

export default function VehiclesTable() {
  const [vehicles, setVehicles] = useState([]);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await getVehicles();
      setVehicles(data);
      setLoading(false);
    } catch (e) {
      console.error(e);
      setError(e);
      setLoading(false);
    }
  };
  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  const filtered = useMemo(() => {
    if (filter === "all") return vehicles;
    return vehicles.filter(v => v.status === filter);
  }, [vehicles, filter]);

  return (
    <div className="rounded-xl border border-muted bg-surface p-3 animate-slide-up" role="region" aria-label="Watchlist vehicles">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-semibold">Watchlist / Vehicles</h2>
        {loading && (
          <div className="text-sm text-gray-500" aria-live="polite">Loading…</div>
        )}
        {error && (
          <div className="text-sm" aria-live="assertive" style={{ color: 'var(--danger)' }}>
            Failed to load vehicles: {String(error.message || error)}
          </div>
        )}
        <div className="flex gap-2 text-sm">
          {['all', 'normal', 'suspicious', 'stolen'].map(s => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              aria-pressed={filter===s}
              className={`px-2 py-1 rounded border border-muted ${filter===s? 'text-white':''}`}
              style={filter===s ? { background: 'var(--accent)' } : { background: 'var(--surface)' }}
            >
              {s}
            </button>
          ))}
        </div>
      </div>
      {/* Desktop/tablet table view */}
      <div className="hidden md:block overflow-auto max-h-[240px]" aria-live="polite">
        <table className="min-w-full text-sm" role="table" aria-label="Vehicles table">
          <thead>
            <tr className="text-left">
              <th className="p-2">Plate</th>
              <th className="p-2">Status</th>
              <th className="p-2">Owner</th>
              <th className="p-2">Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(v => (
              <tr key={v.id} className="border-t">
                <td className="p-2 font-semibold">{v.plate_number}</td>
                <td className="p-2">{v.status}</td>
                <td className="p-2">{v.owner}</td>
                <td className="p-2">{v.last_seen ? new Date(v.last_seen).toLocaleString() : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && !error && (
          <div className="text-sm text-gray-500 p-2">No vehicles.</div>
        )}
      </div>
      {/* Mobile card view */}
      <div className="md:hidden space-y-2" aria-live="polite">
        {filtered.map(v => (
          <div key={v.id} className="border rounded p-2">
            <div className="flex items-center justify-between">
              <div className="font-semibold" aria-label="Plate">{v.plate_number}</div>
              <span className="text-xs" aria-label="Status">{v.status}</span>
            </div>
            <div className="text-sm mt-1"><span className="text-gray-500">Owner:</span> {v.owner || '-'}</div>
            <div className="text-xs text-gray-500">Last seen: {v.last_seen ? new Date(v.last_seen).toLocaleString() : '-'}</div>
          </div>
        ))}
        {filtered.length === 0 && !error && (
          <div className="text-sm text-gray-500">No vehicles.</div>
        )}
      </div>
    </div>
  );
}