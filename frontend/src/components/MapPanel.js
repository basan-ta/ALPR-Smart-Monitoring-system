"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import { getRecentSightings, getPredictedRouteForPlate } from "../lib/api";
import "leaflet/dist/leaflet.css";

const MapContainer = dynamic(() => import("react-leaflet").then(mod => mod.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then(mod => mod.TileLayer), { ssr: false });
const Marker = dynamic(() => import("react-leaflet").then(mod => mod.Marker), { ssr: false });
const Popup = dynamic(() => import("react-leaflet").then(mod => mod.Popup), { ssr: false });
const Polyline = dynamic(() => import("react-leaflet").then(mod => mod.Polyline), { ssr: false });

// Load Leaflet dynamically on the client to avoid SSR "window is not defined"
// Do not import at module scope, as Leaflet touches window during import.
// eslint-disable-next-line no-unused-vars
let LRef = null;

// Client-only Leaflet loader
function useLeaflet() {
  const [L, setL] = useState(null);
  useEffect(() => {
    let mounted = true;
    (async () => {
      if (typeof window === "undefined") return;
      const mod = await import("leaflet");
      LRef = mod.default;
      if (mounted) setL(LRef);
    })();
    return () => { mounted = false; };
  }, []);
  return L;
}

const statusColor = (status) => {
  if (status === "stolen") return "red";
  if (status === "suspicious") return "orange";
  return "green";
};

export default function MapPanel() {
  const [sightings, setSightings] = useState([]);
  const [routes, setRoutes] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const L = useLeaflet();

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        setError(null);
        setLoading(true);
        const data = await getRecentSightings(10);
        if (!mounted) return;
        setSightings(data);
        // Fetch predicted routes for suspicious/stolen
        const plates = [...new Set(data.map(s => s.plate_number))];
        const suspicious = data.filter(s => {
          const v = s.vehicle;
          const hasObj = v && typeof v === 'object';
          return hasObj && ["suspicious", "stolen"].includes(v.status);
        });
        const byPlate = new Set(suspicious.map(s => s.plate_number));
        // Concurrently fetch routes and batch state updates to avoid multiple re-renders
        const promises = [...byPlate].map(async (plate) => {
          try {
            const route = await getPredictedRouteForPlate(plate);
            if (route && route.path) {
              return { plate, path: route.path.map(p => [p.lat, p.lon]) };
            }
          } catch (e) { /* ignore */ }
          return null;
        });
        const results = await Promise.all(promises);
        const nextRoutes = {};
        for (const r of results) {
          if (r && r.path) nextRoutes[r.plate] = r.path;
        }
        if (Object.keys(nextRoutes).length > 0) {
          setRoutes(prev => ({ ...prev, ...nextRoutes }));
        }
        setLoading(false);
      } catch (e) {
        console.error("Failed to load sightings", e);
        setError(e);
        setLoading(false);
      }
    };
    load();
    const id = setInterval(load, 3000);
    return () => { mounted = false; clearInterval(id); };
  }, []);

  const center = useMemo(() => {
    if (sightings.length > 0) {
      return [sightings[0].latitude, sightings[0].longitude];
    }
    return [27.7172, 85.3240]; // Kathmandu default
  }, [sightings]);

  const icon = (color) => {
    if (!L) return undefined;
    return new L.Icon({
      iconUrl: `data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\"><circle cx=\"12\" cy=\"12\" r=\"8\" fill=\"${color}\"/></svg>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
  };

  return (
    <div className="rounded-xl border border-muted bg-surface p-3 h-[480px] animate-slide-up" role="region" aria-label="Live map of recent sightings">
      <h2 className="text-lg font-semibold mb-2">Live Map</h2>
      {loading && (
        <div className="text-sm mb-2 text-gray-500" aria-live="polite">Loading map data…</div>
      )}
      {error && (
        <div className="text-sm mb-2" aria-live="assertive" style={{ color: 'var(--danger)' }}>
          Failed to load sightings: {String(error.message || error)}
        </div>
      )}
      <MapContainer center={center} zoom={13} style={{ height: 420, width: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap contributors" />
        {sightings.map((s) => {
          const curStatus = s?.vehicle && typeof s.vehicle === 'object' ? s.vehicle.status : 'normal';
          return (
          <Marker key={s.id} position={[s.latitude, s.longitude]} icon={icon(statusColor(curStatus))} title={`${s.plate_number} — ${curStatus || 'normal'}`}>
            <Popup>
              <div className="space-y-1">
                <div className="font-semibold">{s.plate_number}</div>
                <div>Status: {curStatus || 'normal'}</div>
                <div>Speed: {s.speed_kmh?.toFixed(1)} km/h</div>
                <div>Heading: {s.heading_deg?.toFixed(0)}°</div>
              </div>
            </Popup>
          </Marker>
        )})}
        {Object.entries(routes).map(([plate, path]) => (
          <Polyline key={`route-${plate}`} positions={path} color="purple" />
        ))}
      </MapContainer>
      {/* Accessible text alternative: list recent sightings for screen readers */}
      <ul className="sr-only" aria-label="Recent sightings list">
        {sightings.map(s => (
          <li key={`sr-${s.id}`}>{s.plate_number} at {s.latitude?.toFixed(5)}, {s.longitude?.toFixed(5)} — status {s?.vehicle?.status || 'normal'}.</li>
        ))}
      </ul>
    </div>
  );
}