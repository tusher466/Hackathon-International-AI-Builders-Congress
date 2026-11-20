import { useSyncExternalStore } from 'react'

let _state = {
  readings: {}, // machine_id -> latest reading
  healthUpdates: {}, // machine_id -> health
  recentEvents: [], // last 20 events
  alerts: [], // live alerts
  agentActivity: null,
}

let listeners = new Set()

function setState(updater) {
  const next = typeof updater === 'function' ? updater(_state) : updater
  _state = { ..._state, ...next }
  listeners.forEach(l => l(_state))
}

function subscribe(cb) {
  listeners.add(cb)
  return () => listeners.delete(cb)
}

function getSnapshot() {
  return _state
}

export const liveStore = {
  getState: () => _state,
  setState,
  dispatch: (msg) => {
    const { type, payload, ts } = msg
    const event = { type, payload, ts, id: Date.now() + Math.random() }
    setState(prev => {
      const recent = [event, ...prev.recentEvents].slice(0, 20)
      let updates = { recentEvents: recent }
      if (type === 'reading') {
        updates.readings = { ...prev.readings, [payload.machine_id]: payload }
      } else if (type === 'health_update') {
        updates.healthUpdates = { ...prev.healthUpdates, [payload.machine_id]: payload }
      } else if (type === 'alert_created') {
        updates.alerts = [payload, ...prev.alerts].slice(0, 50)
      } else if (type === 'agent_step') {
        updates.agentActivity = { text: `${payload.agent} Agent: ${payload.summary}`, ts, alert_id: payload.alert_id }
      } else if (type === 'diagnosis_ready') {
        updates.agentActivity = { text: `Diagnosis ready for ${payload.alert_id}`, ts }
      } else if (type === 'plan_ready') {
        updates.agentActivity = { text: `Plan ready for ${payload.alert_id}`, ts }
      } else if (type === 'approval_required') {
        updates.agentActivity = { text: `Approval required for ${payload.alert_id}`, ts }
      } else if (type === 'fault_injected') {
        updates.agentActivity = { text: `Fault injected on ${payload.machine_id}`, ts }
      } else if (type === 'oee_update') {
        // handled via query invalidation elsewhere, just log
      }
      return { ...prev, ...updates }
    })
  }
}

export const useLiveStore = (selector) => {
  const state = useSyncExternalStore(subscribe, getSnapshot, getSnapshot)
  return selector ? selector(state) : state
}
