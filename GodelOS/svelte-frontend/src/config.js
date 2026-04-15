// Centralized frontend configuration for API and WebSocket bases

const pick = (...vals) => vals.find(v => typeof v === 'string' && v.length > 0);

// Allow overrides via Vite env, window, or sensible defaults
let HOST = pick(import.meta?.env?.VITE_BACKEND_HOST, window?.GODELOS_BACKEND_HOST, 'localhost');
if (HOST === '0.0.0.0') HOST = 'localhost';
const PORT = pick(import.meta?.env?.VITE_BACKEND_PORT, window?.GODELOS_BACKEND_PORT, '8000');
const DIRECT_API = pick(import.meta?.env?.VITE_API_BASE_URL, window?.GODELOS_API_BASE_URL, null);

export const API_BASE_URL = DIRECT_API || `http://${HOST}:${PORT}`;

// Derive WS base from API base
export const WS_BASE_URL = (() => {
  try {
    const u = new URL(API_BASE_URL);
    const proto = u.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${proto}//${u.host}`;
  } catch {
    return 'ws://localhost:8000';
  }
})();

export default { API_BASE_URL, WS_BASE_URL };
