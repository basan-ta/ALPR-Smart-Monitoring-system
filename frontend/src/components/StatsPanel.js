"use client";
import { useEffect, useState } from "react";
import { getStats } from "../lib/api";

export default function StatsPanel() {
  const [stats, setStats] = useState(null);
  const [display, setDisplay] = useState({ vehicles: 0, alerts: 0, online: 0 });
  const [error, setError] = useState(null);

  const load = async () => {
    try {
      setError(null);
      const data = await getStats();
      setStats(data);
    } catch (e) {
      console.error(e);
      setError(e);
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!stats) return;
    const reduceMotion = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const target = {
      vehicles: stats.vehicles_scanned_24h || 0,
      alerts: stats.alerts_triggered_24h || 0,
      online: stats.total_vehicles_online || 0,
    };
    if (reduceMotion) {
      setDisplay(target);
      return;
    }
    const duration = 700;
    const start = performance.now();
    const from = { ...display };
    function step(now) {
      const t = Math.min(1, (now - start) / duration);
      setDisplay({
        vehicles: Math.round(from.vehicles + (target.vehicles - from.vehicles) * t),
        alerts: Math.round(from.alerts + (target.alerts - from.alerts) * t),
        online: Math.round(from.online + (target.online - from.online) * t),
      });
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stats?.vehicles_scanned_24h, stats?.alerts_triggered_24h, stats?.total_vehicles_online]);

  return (
    <div className="rounded-xl border border-muted bg-surface p-3 animate-slide-up" role="region" aria-label="Statistics" aria-busy={!stats}>
      <h2 className="text-lg font-semibold mb-2">Statistics</h2>
      {error && (
        <div className="text-sm mb-2" aria-live="assertive" style={{ color: 'var(--danger)' }}>
          Failed to load statistics: {String(error?.message || error)}
        </div>
      )}
      {stats ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          <div className="border rounded p-2" role="group" aria-label="Vehicles scanned in last 24 hours" tabIndex={0}>
            <div id="stat-vehicles-label" className="text-xs text-gray-500">Vehicles scanned (24h)</div>
            <div className="text-2xl font-bold" aria-live="polite" aria-describedby="stat-vehicles-label">{display.vehicles}</div>
          </div>
          <div className="border rounded p-2" role="group" aria-label="Alerts triggered in last 24 hours" tabIndex={0}>
            <div id="stat-alerts-label" className="text-xs text-gray-500">Alerts triggered (24h)</div>
            <div className="text-2xl font-bold" aria-live="polite" aria-describedby="stat-alerts-label">{display.alerts}</div>
          </div>
          <div className="border rounded p-2" role="group" aria-label="Vehicles online in last 5 minutes" tabIndex={0}>
            <div id="stat-online-label" className="text-xs text-gray-500">Vehicles online (5m)</div>
            <div className="text-2xl font-bold" aria-live="polite" aria-describedby="stat-online-label">{display.online}</div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2" aria-live="polite">
          <div className="border rounded p-2">
            <div className="h-3 w-24 bg-muted animate-pulse rounded mb-2" />
            <div className="h-6 w-16 bg-muted animate-pulse rounded" />
          </div>
          <div className="border rounded p-2">
            <div className="h-3 w-28 bg-muted animate-pulse rounded mb-2" />
            <div className="h-6 w-16 bg-muted animate-pulse rounded" />
          </div>
          <div className="border rounded p-2">
            <div className="h-3 w-32 bg-muted animate-pulse rounded mb-2" />
            <div className="h-6 w-16 bg-muted animate-pulse rounded" />
          </div>
        </div>
      )}
    </div>
  );
}