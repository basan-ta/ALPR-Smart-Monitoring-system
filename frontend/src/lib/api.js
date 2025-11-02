// Environment-based API base URL
// Uses NEXT_PUBLIC_API_URL if present (absolute or relative). Falls back to '/api'.
const ENV_URL = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE;
const API_BASE = (() => {
  try {
    const base = (ENV_URL || '').trim();
    if (!base) {
      console.warn('NEXT_PUBLIC_API_URL not defined; falling back to "/api" via Next.js rewrite.');
      return '/api';
    }
    // Remove trailing slash for consistency
    return base.replace(/\/+$/g, '');
  } catch (e) {
    console.warn('Failed to read NEXT_PUBLIC_API_URL; using "/api". Error:', e);
    return '/api';
  }
})();

function normalizePath(path) {
  const p = String(path || '').trim();
  if (!p.startsWith('/')) return `/${p}`;
  return p;
}

function buildUrl(path) {
  return `${API_BASE}${normalizePath(path)}`;
}

function makeHeaders({ json = true, headers = {} } = {}) {
  const base = { Accept: 'application/json' };
  if (json) base['Content-Type'] = 'application/json';
  return { ...base, ...headers };
}

async function fetchJSON(url, { method = 'GET', headers, body, timeoutMs = 10000, cache = 'no-store', credentials = 'omit', signal } = {}) {
  const controller = signal ? null : new AbortController();
  const sig = signal || (controller ? controller.signal : undefined);
  const timer = controller ? setTimeout(() => controller.abort(new Error('Request timeout')), Math.max(1000, timeoutMs)) : null;
  try {
    const res = await fetch(url, {
      method,
      headers: makeHeaders({ json: method !== 'GET', headers }),
      body: body == null ? undefined : (typeof body === 'string' ? body : JSON.stringify(body)),
      cache,
      credentials,
      signal: sig,
    });
    const text = await res.text();
    let json;
    try { json = text ? JSON.parse(text) : null; } catch { json = null; }
    if (!res.ok) {
      const detail = json?.detail || res.statusText || 'Request failed';
      const err = new Error(`${method} ${url} failed: ${res.status} ${detail}`);
      err.status = res.status;
      err.body = json || text;
      throw err;
    }
    return json;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

// CRUD helpers
const api = {
  get: (path, opts) => fetchJSON(buildUrl(path), { method: 'GET', ...(opts || {}) }),
  post: (path, body, opts) => fetchJSON(buildUrl(path), { method: 'POST', body, ...(opts || {}) }),
  put: (path, body, opts) => fetchJSON(buildUrl(path), { method: 'PUT', body, ...(opts || {}) }),
  del: (path, opts) => fetchJSON(buildUrl(path), { method: 'DELETE', ...(opts || {}) }),
};

// Domain-specific helpers
export const getRecentSightings = (minutes = 10) => api.get(`/sightings/recent/?minutes=${encodeURIComponent(minutes)}`);
export const getRecentAlerts = (minutes = 60) => api.get(`/alerts/recent/?minutes=${encodeURIComponent(minutes)}`);
export const getVehicles = () => api.get(`/vehicles/`);
export const getStats = () => api.get(`/stats/`);

export const acknowledgeAlert = async (id) => {
  try {
    // Prefer POST acknowledge to be explicit
    return await api.post(`/alerts/${id}/acknowledge/`, {});
  } catch (e) {
    // Fallback to GET acknowledge if backend only allows GET
    return api.get(`/alerts/${id}/acknowledge/`);
  }
};

export const getPredictedRouteForPlate = async (plate) => {
  const vehicles = await getVehicles();
  const v = vehicles.find((x) => (x.plate_number || '').toUpperCase() === (plate || '').toUpperCase());
  if (!v) return null;
  return api.get(`/vehicles/${v.id}/predicted/`);
};

export { API_BASE, api };