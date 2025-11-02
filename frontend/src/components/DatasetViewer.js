"use client";

import { useMemo, useState } from "react";
import { useDataset } from "../lib/dataset";
import { isValidNepaliPlate, extractProvinceFromPlate } from "../lib/nepaliPlate";

function TableHeader({ columns, sort, setSort }) {
  return (
    <thead>
      <tr className="text-left">
        {columns.map(col => (
          <th
            key={col.key}
            role="columnheader"
            aria-sort={sort.key === col.key ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}
            className="p-2 cursor-pointer select-none"
            onClick={() => {
              const dir = (sort.key === col.key && sort.dir === 'asc') ? 'desc' : 'asc';
              setSort({ key: col.key, dir });
            }}
          >
            <span className="underline-offset-2 hover:underline">{col.label}</span>
            {sort.key === col.key && (
              <span className="ml-1 text-xs" aria-hidden="true">{sort.dir === 'asc' ? '▲' : '▼'}</span>
            )}
          </th>
        ))}
      </tr>
    </thead>
  );
}

export default function DatasetViewer() {
  const [source, setSource] = useState('api');
  const [pollIntervalMs, setPollIntervalMs] = useState(5000);
  const [minutesSightings, setMinutesSightings] = useState(60);
  const [minutesAlerts, setMinutesAlerts] = useState(120);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [provinceFilter, setProvinceFilter] = useState('all');
  const [validOnly, setValidOnly] = useState(false);

  const { data, loading, error, refresh, meta } = useDataset({ source, minutesSightings, minutesAlerts, pollIntervalMs });

  const [vehSort, setVehSort] = useState({ key: 'plate_number', dir: 'asc' });
  const [sigSort, setSigSort] = useState({ key: 'timestamp', dir: 'desc' });
  const [altSort, setAltSort] = useState({ key: 'timestamp', dir: 'desc' });

  const searchLower = search.trim().toLowerCase();
  const provinceOptions = ['all', '१','२','३','४','५','६','७'];

  const filteredVehicles = useMemo(() => {
    let list = data.vehicles || [];
    if (statusFilter !== 'all') list = list.filter(v => v.status === statusFilter);
    if (validOnly) list = list.filter(v => v.is_valid_plate);
    if (provinceFilter !== 'all') list = list.filter(v => extractProvinceFromPlate(v.plate_number) === provinceFilter);
    if (searchLower) list = list.filter(v => (v.plate_number || '').toLowerCase().includes(searchLower) || (v.owner || '').toLowerCase().includes(searchLower));
    const { key, dir } = vehSort;
    return [...list].sort((a, b) => {
      const av = a[key] ?? '';
      const bv = b[key] ?? '';
      if (av < bv) return dir === 'asc' ? -1 : 1;
      if (av > bv) return dir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data.vehicles, statusFilter, validOnly, provinceFilter, searchLower, vehSort]);

  const filteredSightings = useMemo(() => {
    let list = data.sightings || [];
    if (validOnly) list = list.filter(s => s.is_valid_plate);
    if (searchLower) list = list.filter(s => (s.plate_number || '').toLowerCase().includes(searchLower));
    const { key, dir } = sigSort;
    return [...list].sort((a, b) => {
      const av = a[key] ?? '';
      const bv = b[key] ?? '';
      if (av < bv) return dir === 'asc' ? -1 : 1;
      if (av > bv) return dir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data.sightings, validOnly, searchLower, sigSort]);

  const filteredAlerts = useMemo(() => {
    let list = data.alerts || [];
    if (searchLower) list = list.filter(a => (a.plate_number || '').toLowerCase().includes(searchLower));
    const { key, dir } = altSort;
    return [...list].sort((a, b) => {
      const av = a[key] ?? '';
      const bv = b[key] ?? '';
      if (av < bv) return dir === 'asc' ? -1 : 1;
      if (av > bv) return dir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data.alerts, searchLower, altSort]);

  return (
    <div className="space-y-4 animate-fade-in">
      <div className="rounded-xl border border-muted bg-surface p-3" role="region" aria-label="Vehicles list">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-sm">Source</label>
            <select value="api" disabled className="border rounded px-2 py-1 text-sm opacity-70 cursor-not-allowed" aria-disabled="true">
              <option value="api">Backend API ({meta.apiBase})</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm">Poll</label>
            <select value={pollIntervalMs} onChange={e => setPollIntervalMs(Number(e.target.value))} className="border rounded px-2 py-1 text-sm">
              <option value={0}>Off</option>
              <option value={3000}>3s</option>
              <option value={5000}>5s</option>
              <option value={10000}>10s</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm">Sightings (min)</label>
            <select value={minutesSightings} onChange={e => setMinutesSightings(Number(e.target.value))} className="border rounded px-2 py-1 text-sm">
              <option value={30}>30</option>
              <option value={60}>60</option>
              <option value={120}>120</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm">Alerts (min)</label>
            <select value={minutesAlerts} onChange={e => setMinutesAlerts(Number(e.target.value))} className="border rounded px-2 py-1 text-sm">
              <option value={60}>60</option>
              <option value={120}>120</option>
              <option value={240}>240</option>
            </select>
          </div>
          <div className="flex-1" />
          <button onClick={refresh} className="px-3 py-1 bg-blue-600 text-white rounded text-sm">Refresh</button>
        </div>
        <div className="mt-2 text-xs text-gray-600">Counts — Vehicles: {meta.counts.vehicles}, Sightings: {meta.counts.sightings}, Alerts: {meta.counts.alerts}</div>
        {loading && (
          <div className="mt-1 text-sm text-gray-500" aria-live="polite">Loading dataset…</div>
        )}
        {error && (
          <div className="mt-1 text-sm" aria-live="assertive" style={{ color: 'var(--danger)' }}>
            Failed to load dataset: {String(error?.message || error)}
          </div>
        )}
      </div>

      <div className="rounded-xl border border-muted bg-surface p-3">
        <div className="flex flex-wrap items-center gap-3 mb-2">
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search plate or owner" className="border rounded px-2 py-1 text-sm w-48" />
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="border rounded px-2 py-1 text-sm">
            {['all','normal','suspicious','stolen'].map(s => (<option key={s} value={s}>{s}</option>))}
          </select>
          <select value={provinceFilter} onChange={e => setProvinceFilter(e.target.value)} className="border rounded px-2 py-1 text-sm">
            {provinceOptions.map(p => (<option key={p} value={p}>{p}</option>))}
          </select>
          <label className="text-sm flex items-center gap-2"><input type="checkbox" checked={validOnly} onChange={e => setValidOnly(e.target.checked)} /> Valid plates only</label>
        </div>

        {/* Desktop/tablet table view */}
        <div className="hidden md:block overflow-auto max-h-[260px] table-wrap" aria-live="polite">
          <table className="min-w-full text-sm" role="table" aria-label="Vehicles">
            <TableHeader columns={[
              { key: 'plate_number', label: 'Plate' },
              { key: 'status', label: 'Status' },
              { key: 'owner', label: 'Owner' },
              { key: 'last_seen', label: 'Last Seen' },
              { key: 'is_valid_plate', label: 'Valid' },
              { key: 'province', label: 'Province' },
            ]} sort={vehSort} setSort={setVehSort} />
            <tbody>
              {filteredVehicles.map(v => (
                <tr key={v.id} className="border-t">
                  <td className="p-2 font-semibold">{v.plate_number}</td>
                  <td className="p-2">{v.status}</td>
                  <td className="p-2">{v.owner}</td>
                  <td className="p-2">{v.last_seen ? new Date(v.last_seen).toLocaleString() : '-'}</td>
                  <td className="p-2">{v.is_valid_plate ? '✓' : '✗'}</td>
                  <td className="p-2">{v.province || '-'}</td>
                </tr>
              ))}
              {filteredVehicles.length === 0 && (
                <tr><td className="p-2 text-gray-500" colSpan={6}>No vehicles match filters.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        {/* Mobile card view */}
        <div className="md:hidden card-list" aria-live="polite">
          {filteredVehicles.map(v => (
            <div key={v.id} className="card">
              <div className="flex items-center justify-between">
                <div className="font-semibold" aria-label="Plate">{v.plate_number}</div>
                <span className="text-xs" aria-label="Province">{v.province || '-'}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                <div><span className="text-gray-500">Status:</span> {v.status}</div>
                <div><span className="text-gray-500">Owner:</span> {v.owner || '-'}</div>
                <div><span className="text-gray-500">Last seen:</span> {v.last_seen ? new Date(v.last_seen).toLocaleString() : '-'}</div>
                <div><span className="text-gray-500">Valid:</span> {v.is_valid_plate ? '✓' : '✗'}</div>
              </div>
            </div>
          ))}
          {filteredVehicles.length === 0 && (
            <div className="text-sm text-gray-500">No vehicles match filters.</div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-muted bg-surface p-3" role="region" aria-label="Sightings list">
          <h3 className="text-base font-semibold mb-2">Sightings</h3>
          {/* Desktop/tablet table view */}
          <div className="hidden md:block overflow-auto max-h-[260px] table-wrap" aria-live="polite">
            <table className="min-w-full text-sm" role="table" aria-label="Sightings">
              <TableHeader columns={[
                { key: 'plate_number', label: 'Plate' },
                { key: 'latitude', label: 'Lat' },
                { key: 'longitude', label: 'Lon' },
                { key: 'speed_kmh', label: 'Speed' },
                { key: 'heading_deg', label: 'Heading' },
                { key: 'timestamp', label: 'Time' },
                { key: 'is_valid_plate', label: 'Valid' },
              ]} sort={sigSort} setSort={setSigSort} />
              <tbody>
                {filteredSightings.map(s => (
                  <tr key={s.id} className="border-t">
                    <td className="p-2 font-semibold">{s.plate_number}</td>
                    <td className="p-2">{s.latitude?.toFixed(5)}</td>
                    <td className="p-2">{s.longitude?.toFixed(5)}</td>
                    <td className="p-2">{s.speed_kmh?.toFixed(1)}</td>
                    <td className="p-2">{s.heading_deg?.toFixed(0)}°</td>
                    <td className="p-2">{new Date(s.timestamp).toLocaleString()}</td>
                    <td className="p-2">{s.is_valid_plate ? '✓' : '✗'}</td>
                  </tr>
                ))}
                {filteredSightings.length === 0 && (
                  <tr><td className="p-2 text-gray-500" colSpan={7}>No sightings match filters.</td></tr>
                )}
              </tbody>
            </table>
          </div>
          {/* Mobile card view */}
          <div className="md:hidden card-list" aria-live="polite">
            {filteredSightings.map(s => (
              <div key={s.id} className="card">
                <div className="font-semibold" aria-label="Plate">{s.plate_number}</div>
                <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                  <div><span className="text-gray-500">Lat:</span> {s.latitude?.toFixed(5)}</div>
                  <div><span className="text-gray-500">Lon:</span> {s.longitude?.toFixed(5)}</div>
                  <div><span className="text-gray-500">Speed:</span> {s.speed_kmh?.toFixed(1)} km/h</div>
                  <div><span className="text-gray-500">Heading:</span> {s.heading_deg?.toFixed(0)}°</div>
                  <div className="col-span-2"><span className="text-gray-500">Time:</span> {new Date(s.timestamp).toLocaleString()}</div>
                  <div><span className="text-gray-500">Valid:</span> {s.is_valid_plate ? '✓' : '✗'}</div>
                </div>
              </div>
            ))}
            {filteredSightings.length === 0 && (
              <div className="text-sm text-gray-500">No sightings match filters.</div>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-muted bg-surface p-3" role="region" aria-label="Alerts list">
          <h3 className="text-base font-semibold mb-2">Alerts</h3>
          {/* Desktop/tablet table view */}
          <div className="hidden md:block overflow-auto max-h-[260px] table-wrap" aria-live="polite">
            <table className="min-w-full text-sm" role="table" aria-label="Alerts">
              <TableHeader columns={[
                { key: 'plate_number', label: 'Plate' },
                { key: 'status', label: 'Status' },
                { key: 'timestamp', label: 'Time' },
                { key: 'acknowledged', label: 'Ack' },
                { key: 'dispatched', label: 'Dispatch' },
                { key: 'is_valid_plate', label: 'Valid' },
              ]} sort={altSort} setSort={setAltSort} />
              <tbody>
                {filteredAlerts.map(a => (
                  <tr key={a.id} className="border-t">
                    <td className="p-2 font-semibold">{a.plate_number}</td>
                    <td className="p-2">{a.status}</td>
                    <td className="p-2">{new Date(a.timestamp).toLocaleString()}</td>
                    <td className="p-2">{a.acknowledged ? '✓' : '—'}</td>
                    <td className="p-2">{a.dispatched ? '✓' : '—'}</td>
                    <td className="p-2">{a.is_valid_plate ? '✓' : '✗'}</td>
                  </tr>
                ))}
                {filteredAlerts.length === 0 && (
                  <tr><td className="p-2 text-gray-500" colSpan={6}>No alerts match filters.</td></tr>
                )}
              </tbody>
            </table>
          </div>
          {/* Mobile card view */}
          <div className="md:hidden card-list" aria-live="polite">
            {filteredAlerts.map(a => (
              <div key={a.id} className="card">
                <div className="flex items-center justify-between">
                  <div className="font-semibold" aria-label="Plate">{a.plate_number}</div>
                  <span className="text-xs" aria-label="Status">{a.status}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                  <div className="col-span-2"><span className="text-gray-500">Time:</span> {new Date(a.timestamp).toLocaleString()}</div>
                  <div><span className="text-gray-500">Ack:</span> {a.acknowledged ? '✓' : '—'}</div>
                  <div><span className="text-gray-500">Dispatch:</span> {a.dispatched ? '✓' : '—'}</div>
                  <div><span className="text-gray-500">Valid:</span> {a.is_valid_plate ? '✓' : '✗'}</div>
                </div>
              </div>
            ))}
            {filteredAlerts.length === 0 && (
              <div className="text-sm text-gray-500">No alerts match filters.</div>
            )}
          </div>
        </div>
      </div>

      {loading && (
        <div className="text-sm text-gray-600" role="status" aria-live="polite">Loading dataset…</div>
      )}
      {error && (
        <div className="text-sm" aria-live="assertive" style={{ color: 'var(--danger)' }}>
          Failed to load: {String(error.message || error)}
          <button onClick={refresh} className="ml-2 px-2 py-1 border border-muted rounded bg-surface">Retry</button>
        </div>
      )}
    </div>
  );
}