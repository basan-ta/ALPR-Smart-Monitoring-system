"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { getVehicles, getRecentSightings, getRecentAlerts, API_BASE, api } from "./api";
import { isValidNepaliPlate, normalizePlate, extractProvinceFromPlate } from "./nepaliPlate";

export async function getDataset({
  source = "api",
  minutesSightings = 60,
  minutesAlerts = 120,
} = {}) {
  // Enforce API-only by default; keep legacy branch for compatibility
  if (source === "apiLegacy") {
    const [vehicles, sightings, alerts] = await Promise.all([
      getVehicles(),
      getRecentSightings(minutesSightings),
      getRecentAlerts(minutesAlerts),
    ]);
    return { vehicles, sightings, alerts, source };
  }
  // Unified dataset endpoint
  const url = `/dataset/?minutesSightings=${encodeURIComponent(minutesSightings)}&minutesAlerts=${encodeURIComponent(minutesAlerts)}`;
  const json = await api.get(url);
  return { vehicles: json.vehicles || [], sightings: json.sightings || [], alerts: json.alerts || [], source: "api" };
}

function formatAndValidateDataset(raw) {
  const vehicles = (raw.vehicles || []).map(v => ({
    ...v,
    plate_number: normalizePlate(v.plate_number || ""),
    is_valid_plate: isValidNepaliPlate(v.plate_number || ""),
    province: extractProvinceFromPlate(v.plate_number || "") || null,
  }));
  const sightings = (raw.sightings || []).map(s => ({
    ...s,
    plate_number: normalizePlate(s.plate_number || ""),
    is_valid_plate: isValidNepaliPlate(s.plate_number || ""),
  }));
  const alerts = (raw.alerts || []).map(a => ({
    ...a,
    plate_number: normalizePlate(a.plate_number || ""),
    is_valid_plate: isValidNepaliPlate(a.plate_number || ""),
  }));
  return { vehicles, sightings, alerts };
}

export function useDataset(options) {
  const { source = "api", minutesSightings = 60, minutesAlerts = 120, pollIntervalMs = 5000 } = options || {};
  const [data, setData] = useState({ vehicles: [], sightings: [], alerts: [], source });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const lastRef = useRef(null);

  const load = async () => {
    try {
      setError(null);
      const raw = await getDataset({ source, minutesSightings, minutesAlerts });
      const formatted = formatAndValidateDataset(raw);
      const next = { ...formatted, source };
      // Perform shallow comparison to avoid unnecessary re-renders
      const last = lastRef.current;
      const same = last && JSON.stringify(last) === JSON.stringify(next);
      if (!same) {
        lastRef.current = next;
        setData(next);
      }
      setLoading(false);
    } catch (e) {
      setError(e);
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;
    const tick = async () => {
      if (!mounted) return;
      await load();
    };
    tick();
    const id = pollIntervalMs ? setInterval(tick, pollIntervalMs) : null;
    return () => { mounted = false; if (id) clearInterval(id); };
  }, [source, minutesSightings, minutesAlerts, pollIntervalMs]);

  const meta = useMemo(() => ({
    apiBase: API_BASE,
    counts: {
      vehicles: data.vehicles.length,
      sightings: data.sightings.length,
      alerts: data.alerts.length,
    },
  }), [data]);

  return { data, loading, error, refresh: load, meta };
}