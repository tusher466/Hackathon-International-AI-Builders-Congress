const API_KEY = import.meta.env.VITE_API_KEY || ''

// Resolve base URL: allow env override, else auto-detect prod vs dev
// In production (merged), frontend is served from same origin as backend, so use relative /api/v1
// In dev (vite on 3000), backend is on 8000
function resolveBaseUrl() {
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (envUrl) return envUrl.replace(/\/$/, '')
  if (typeof window !== 'undefined') {
    // If running on vite dev server port 3000, point to backend 8000
    if (window.location.port === '3000' || window.location.port === '5173' || window.location.port === '4173') {
      const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
      if (isLocalhost) {
        return 'http://localhost:8000/api/v1'
      }
    }
    // Production merged: same origin, relative path
    return `${window.location.origin}/api/v1`
  }
  return 'http://localhost:8000/api/v1'
}

const BASE_URL = resolveBaseUrl()

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`
  const headers = {
    'Content-Type': 'application/json',
    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
    ...(options.headers || {}),
  }

  try {
    const res = await fetch(url, { ...options, headers })
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      const err = new Error(text || `HTTP ${res.status}`)
      err.status = res.status
      throw err
    }
    // handle empty responses
    const ct = res.headers.get('content-type') || ''
    if (ct.includes('application/json')) {
      return await res.json()
    }
    const txt = await res.text().catch(() => '')
    try {
      return txt ? JSON.parse(txt) : txt
    } catch {
      return txt
    }
  } catch (e) {
    throw e
  }
}

export const apiClient = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  put: (path, body) => request(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: (path, body) => request(path, { method: 'PATCH', body: JSON.stringify(body) }),
  del: (path) => request(path, { method: 'DELETE' }),
}

export const isMockMode = () => {
  return import.meta.env.VITE_USE_MOCK === 'true'
}

export const getWsUrl = () => {
  const envWs = import.meta.env.VITE_WS_URL
  if (envWs) return envWs
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    // Dev mode: backend on 8000
    if (window.location.port === '3000' || window.location.port === '5173') {
      return 'ws://localhost:8000/ws/live'
    }
    // Production merged: same host, /ws/live
    if (window.location.port === '8000') {
      return `${protocol}//${window.location.host}/ws/live`
    }
    return `${protocol}//${window.location.host}/ws/live`
  }
  return 'ws://localhost:8000/ws/live'
}

export const getBaseUrl = () => BASE_URL
