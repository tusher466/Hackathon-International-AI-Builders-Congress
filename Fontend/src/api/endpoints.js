import { apiClient, isMockMode } from './client'
import { mockApi } from './mock/mockServer'

// wrapper that tries real API, falls back to mock if 404 or network error
async function withFallback(fnReal, fnMock, opts = {}) {
  const forceMock = isMockMode()
  if (forceMock) {
    return fnMock()
  }
  try {
    return await fnReal()
  } catch (e) {
    const isNotFound = e.status === 404
    const isNetwork = !e.status
    if ((isNotFound && opts.fallbackOn404) || (isNetwork && opts.fallbackOnError)) {
      console.warn('Falling back to mock for', e.message)
      return fnMock()
    }
    if (opts.fallbackAlways) {
      console.warn('Falling back to mock', e.message)
      return fnMock()
    }
    throw e
  }
}

export const api = {
  getMachines: () => withFallback(
    () => apiClient.get('/machines'),
    () => mockApi.getMachines(),
    { fallbackOnError: true, fallbackOn404: true, fallbackAlways: true }
  ),
  getMachine: (id) => withFallback(
    () => apiClient.get(`/machines/${id}`),
    () => mockApi.getMachine(id),
    { fallbackOnError: true, fallbackAlways: true }
  ),
  getReadings: (id, limit = 100) => withFallback(
    () => apiClient.get(`/machines/${id}/readings?limit=${limit}`),
    () => mockApi.getReadings(id, limit),
    { fallbackOnError: true, fallbackAlways: true }
  ),
  getAlerts: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return withFallback(
      () => apiClient.get(`/alerts${qs ? '?' + qs : ''}`),
      () => mockApi.getAlerts(params),
      { fallbackOnError: true, fallbackAlways: true }
    )
  },
  getAlert: (id) => withFallback(
    () => apiClient.get(`/alerts/${id}`),
    () => mockApi.getAlert(id),
    { fallbackOnError: true, fallbackAlways: true }
  ),
  getTrace: (alertId) => withFallback(
    () => apiClient.get(`/decisions/${alertId}/trace`),
    () => mockApi.getTrace(alertId),
    { fallbackOnError: true, fallbackAlways: true }
  ),
  getPendingApprovals: () => withFallback(
    () => apiClient.get('/approvals/pending'),
    () => mockApi.getPendingApprovals(),
    { fallbackOnError: true, fallbackAlways: true }
  ),
  approve: (alertId, body) => withFallback(
    () => apiClient.post(`/approvals/${alertId}/approve`, body),
    () => mockApi.approve(alertId, body),
    { fallbackOnError: true, fallbackAlways: true }
  ),
  reject: (alertId, body) => withFallback(
    () => apiClient.post(`/approvals/${alertId}/reject`, body),
    () => mockApi.reject(alertId, body),
    { fallbackOnError: true, fallbackAlways: true }
  ),
  getTickets: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return withFallback(
      () => apiClient.get(`/tickets${qs ? '?' + qs : ''}`),
      () => mockApi.getTickets(params),
      { fallbackOnError: true, fallbackAlways: true }
    )
  },
  getTicket: (id) => withFallback(
    () => apiClient.get(`/tickets/${id}`),
    () => mockApi.getTicket(id),
    { fallbackOnError: true, fallbackAlways: true }
  ),
  searchKnowledge: (body) => withFallback(
    () => apiClient.post('/knowledge/search', body),
    () => mockApi.searchKnowledge(body),
    { fallbackOnError: true, fallbackAlways: true }
  ),
  getImpact: () => withFallback(
    () => apiClient.get('/metrics/impact'),
    () => mockApi.getImpact(),
    { fallbackOnError: true, fallbackAlways: true }
  ),
  getHealth: () => withFallback(
    () => apiClient.get('/health'),
    () => mockApi.getHealth(),
    { fallbackOnError: true, fallbackAlways: true }
  ),
  getOee: () => withFallback(
    () => apiClient.get('/metrics/oee'),
    () => mockApi.getOee(),
    { fallbackOn404: true, fallbackOnError: true, fallbackAlways: true }
  ),
  getBottlenecks: () => withFallback(
    () => apiClient.get('/bottlenecks'),
    () => mockApi.getBottlenecks(),
    { fallbackOn404: true, fallbackOnError: true, fallbackAlways: true }
  ),
  chat: (body) => withFallback(
    () => apiClient.post('/chat', body),
    () => mockApi.chat(body),
    { fallbackOn404: true, fallbackOnError: true, fallbackAlways: true }
  ),
  getAuditLog: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return withFallback(
      () => apiClient.get(`/audit-log${qs ? '?' + qs : ''}`),
      () => mockApi.getAuditLog(params),
      { fallbackOn404: true, fallbackOnError: true, fallbackAlways: true }
    )
  },
  // control
  controlStart: () => withFallback(() => apiClient.post('/control/stream/start', {}), () => mockApi.controlStart(), { fallbackAlways: true }),
  controlStop: () => withFallback(() => apiClient.post('/control/stream/stop', {}), () => mockApi.controlStop(), { fallbackAlways: true }),
  controlPause: () => withFallback(() => apiClient.post('/control/stream/pause', {}), () => mockApi.controlPause(), { fallbackAlways: true }),
  controlResume: () => withFallback(() => apiClient.post('/control/stream/resume', {}), () => mockApi.controlResume(), { fallbackAlways: true }),
  injectFault: (body) => withFallback(() => apiClient.post('/control/inject-fault', body), () => mockApi.injectFault(body), { fallbackAlways: true }),
  reset: () => withFallback(() => apiClient.post('/control/reset', {}), () => mockApi.reset(), { fallbackAlways: true }),
}
