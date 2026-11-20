import { machines as baseMachines, alerts as baseAlerts, traces, diagnoses, plans, tickets as baseTickets, knowledgeBase, oee, bottlenecks, impact, auditLog as baseAudit, health, chatExamples, genReading } from './mockData.js'

let machines = JSON.parse(JSON.stringify(baseMachines))
let alerts = JSON.parse(JSON.stringify(baseAlerts))
let tickets = JSON.parse(JSON.stringify(baseTickets))
let auditLog = JSON.parse(JSON.stringify(baseAudit))
let streamState = 'running'
let injectedFaults = []

const delay = (ms) => new Promise(r => setTimeout(r, ms))

export const mockApi = {
  getMachines: async () => {
    await delay(200)
    return machines
  },
  getMachine: async (id) => {
    await delay(150)
    const m = machines.find(x => x.machine_id === id)
    if (!m) throw { status: 404, message: 'not found' }
    return m
  },
  getReadings: async (id, limit=100) => {
    await delay(100)
    const arr = []
    for (let i=limit; i>=0; i--) {
      const reading = genReading(id, i)
      arr.push({ ...reading, ts: new Date(Date.now() - i*1000).toISOString() })
    }
    return arr
  },
  getAlerts: async (params={}) => {
    await delay(200)
    let filtered = [...alerts]
    if (params.severity) filtered = filtered.filter(a => a.severity === params.severity)
    if (params.status) filtered = filtered.filter(a => a.status === params.status)
    if (params.machine_id) filtered = filtered.filter(a => a.machine_id === params.machine_id)
    const limit = params.limit ? parseInt(params.limit) : 50
    return filtered.slice(0, limit)
  },
  getAlert: async (id) => {
    await delay(150)
    const alert = alerts.find(a => a.alert_id === id)
    if (!alert) throw { status: 404 }
    const diagnosis = diagnoses[id]
    const plan = plans[id]
    return { ...alert, diagnosis, plan }
  },
  getTrace: async (alertId) => {
    await delay(150)
    return traces[alertId] || []
  },
  getPendingApprovals: async () => {
    await delay(200)
    const pendingAlerts = alerts.filter(a => a.status === 'awaiting_approval')
    return pendingAlerts.map(a => ({
      alert_id: a.alert_id,
      machine_id: a.machine_id,
      severity: a.severity,
      alert_type: a.alert_type,
      confidence: a.confidence,
      top_sensors: a.top_sensors,
      diagnosis: diagnoses[a.alert_id],
      plan: plans[a.alert_id],
      ticket: tickets.find(t => t.alert_id === a.alert_id)
    }))
  },
  approve: async (alertId, body) => {
    await delay(300)
    const alert = alerts.find(a => a.alert_id === alertId)
    if (alert) alert.status = 'ticketed'
    const ticket = tickets.find(t => t.alert_id === alertId)
    if (ticket) {
      ticket.status = 'in_progress'
      ticket.updated_at = new Date().toISOString()
    }
    auditLog.unshift({
      id: `AUD-${Date.now()}`,
      ts: new Date().toISOString(),
      actor_type: 'human',
      actor: body.decided_by || 'Demo User',
      event_type: 'approval',
      alert_id: alertId,
      ticket_id: ticket?.ticket_id,
      machine_id: alert?.machine_id,
      summary: `Approved ${plans[alertId]?.action_type || 'action'} for ${alert?.machine_id}`,
      details: { comment: body.comment || '', reasoning: diagnoses[alertId]?.reasoning }
    })
    return { ok: true, ticket }
  },
  reject: async (alertId, body) => {
    await delay(300)
    const alert = alerts.find(a => a.alert_id === alertId)
    if (alert) alert.status = 'open'
    const ticket = tickets.find(t => t.alert_id === alertId)
    if (ticket) {
      ticket.status = 'rejected'
      ticket.updated_at = new Date().toISOString()
    }
    auditLog.unshift({
      id: `AUD-${Date.now()}`,
      ts: new Date().toISOString(),
      actor_type: 'human',
      actor: body.decided_by || 'Demo User',
      event_type: 'rejection',
      alert_id: alertId,
      ticket_id: ticket?.ticket_id,
      machine_id: alert?.machine_id,
      summary: `Rejected action for ${alert?.machine_id}`,
      details: { comment: body.comment || '' }
    })
    return { ok: true }
  },
  getTickets: async (params={}) => {
    await delay(200)
    let f = [...tickets]
    if (params.status) f = f.filter(t => t.status === params.status)
    return f
  },
  getTicket: async (id) => {
    await delay(150)
    const t = tickets.find(x => x.ticket_id === id)
    if (!t) throw { status: 404 }
    const alert = alerts.find(a => a.alert_id === t.alert_id)
    return { ...t, alert, diagnosis: diagnoses[t.alert_id], plan: plans[t.alert_id] }
  },
  searchKnowledge: async (body) => {
    await delay(400)
    const q = (body.query || '').toLowerCase()
    let results = knowledgeBase.filter(k => k.text.toLowerCase().includes(q) || k.source.toLowerCase().includes(q) || q.includes('bearing') && k.source.includes('TMAN') || q.includes('torque') && k.source.includes('BOSCH'))
    if (results.length === 0 && q) {
      // fallback to all sorted by score
      results = [...knowledgeBase].sort((a,b) => b.score - a.score).slice(0,3)
    }
    if (!q) results = [...knowledgeBase].slice(0,5)
    return results.slice(0, body.k || 5).map((r,i) => ({ ...r, index: i+1, highlight: r.text }))
  },
  getImpact: async () => {
    await delay(150)
    return impact
  },
  getHealth: async () => {
    await delay(100)
    return { ...health, stream_state: streamState }
  },
  getOee: async () => {
    await delay(150)
    return oee
  },
  getBottlenecks: async () => {
    await delay(150)
    return bottlenecks
  },
  chat: async (body) => {
    await delay(800)
    const q = (body.question || '').toLowerCase()
    // find example
    let ex = chatExamples.find(e => q.includes(e.q.toLowerCase().slice(0,15)) || e.q.toLowerCase().includes(q.slice(0,15)))
    if (q.includes('line 3') && q.includes('2 am') || q.includes('2am') || q.includes('stop')) {
      ex = chatExamples[0]
    } else if (q.includes('fail') || q.includes('most likely')) {
      ex = chatExamples[1]
    }
    if (ex) {
      return { answer: ex.a, citations: ex.citations, related_alert_ids: ex.related_alert_ids }
    }
    if (q.includes('bottleneck') || q.includes('slowing')) {
      return {
        answer: 'Current bottleneck is BOSCH-02 on LINE-C. Station 4 torque tool is worn, causing 124 units lost per hour. The tool exceeded its 5000 cycle life. Reason: slowing assembly cycle by 18%. Recommend immediate tool replacement.',
        citations: [
          { index: 1, source: 'BOSCH-TOOL-04 Tooling Manual', section: 'Tool wear limits', doc_type: 'manual', excerpt: 'When torque exceeds 2.5 sigma above baseline for >20 cycles, inspect insert for wear. Typical life 5000 cycles.', score: 0.82 },
        ],
        related_alert_ids: ['ALT-1002']
      }
    }
    if (!q || q.length < 3) {
      return { answer: '', citations: [], related_alert_ids: [] }
    }
    // generic insufficient evidence case when random
    if (q.includes('xyz') || q.includes('unicorn')) {
      return { answer: 'Not enough evidence in the manuals or logs to answer this question. The knowledge base was searched but no relevant passages were found with sufficient similarity. Try rephrasing or check machine-specific logs.', citations: [], related_alert_ids: [] }
    }
    // default answer with generic
    return {
      answer: `Based on available data: Your question about "${body.question}" was searched against manuals and failure logs. The most relevant findings indicate that anomalies are triggered when sensor deviation exceeds 2.5 sigma. For detailed diagnosis, check the alerts page and machine health charts. For TURBO-03, bearing wear pattern matches manual TMAN-07 4.2 with 92% confidence.`,
      citations: [
        { index: 1, source: 'TMAN-07 Turbofan Maintenance Manual', section: '4.2 Bearing wear signatures', doc_type: 'manual', excerpt: 'Vibration increase >3 sigma on bearing sensors 6-8 with concomitant core temperature rise indicates early bearing wear.', score: 0.72 },
        { index: 2, source: 'Sensor Spec TURBO-SEC-01', section: '2.4 Vibration thresholds', doc_type: 'sensor log', excerpt: 'Normal vibration_bearing_7 range 0.2-0.8 g. Alert at 2.0 g sustained. Critical at 3.0 g.', score: 0.61 },
      ],
      related_alert_ids: ['ALT-1001']
    }
  },
  getAuditLog: async (params={}) => {
    await delay(200)
    let f = [...auditLog]
    if (params.actor) f = f.filter(a => a.actor_type === params.actor)
    if (params.type) f = f.filter(a => a.event_type === params.type)
    if (params.machine_id) f = f.filter(a => a.machine_id === params.machine_id)
    return f.slice(0, parseInt(params.limit|| '100'))
  },
  controlStart: async () => { await delay(100); streamState='running'; return { state: streamState } },
  controlStop: async () => { await delay(100); streamState='stopped'; return { state: streamState } },
  controlPause: async () => { await delay(100); streamState='paused'; return { state: streamState } },
  controlResume: async () => { await delay(100); streamState='running'; return { state: streamState } },
  injectFault: async (body) => {
    await delay(500)
    const faultId = `FLT-${Date.now()}`
    const newAlert = {
      alert_id: `ALT-${Math.floor(1000 + Math.random()*9000)}`,
      machine_id: body.machine_id,
      machine_type: machines.find(m=>m.machine_id===body.machine_id)?.machine_type || 'turbofan',
      ts: new Date().toISOString(),
      alert_type: body.fault_type === 'degradation' ? 'degradation' : 'anomaly',
      severity: body.magnitude > 0.7 ? 'critical' : body.magnitude > 0.4 ? 'high' : 'medium',
      confidence: 0.6 + Math.random()*0.3,
      anomaly_score: body.magnitude,
      top_sensors: [{ name: 'injected_sensor', deviation: body.magnitude * 4, direction: 'high' }],
      status: 'detected',
      description: `Injected fault ${body.fault_type} on ${body.machine_id} magnitude ${body.magnitude}`,
    }
    alerts.unshift(newAlert)
    injectedFaults.push({ id: faultId, ...body })
    // update machine health
    const mach = machines.find(m=>m.machine_id===body.machine_id)
    if (mach) {
      mach.health_score = Math.max(10, mach.health_score - body.magnitude*40)
      mach.status = mach.health_score < 50 ? 'critical' : mach.health_score < 80 ? 'warning' : 'healthy'
      mach.open_alert_count +=1
    }
    // audit
    auditLog.unshift({
      id: `AUD-${Date.now()}`,
      ts: new Date().toISOString(),
      actor_type: 'human',
      actor: 'Demo User',
      event_type: 'override',
      machine_id: body.machine_id,
      summary: `Injected fault ${body.fault_type} magnitude ${body.magnitude}`,
      details: { fault: body }
    })
    return { alert_id: newAlert.alert_id, fault_id: faultId }
  },
  reset: async () => {
    await delay(300)
    machines = JSON.parse(JSON.stringify(baseMachines))
    alerts = JSON.parse(JSON.stringify(baseAlerts))
    tickets = JSON.parse(JSON.stringify(baseTickets))
    auditLog = JSON.parse(JSON.stringify(baseAudit))
    injectedFaults = []
    streamState='running'
    return { ok: true }
  }
}

// mock socket emitter for live updates
export class MockSocket {
  constructor(dispatch) {
    this.dispatch = dispatch
    this.interval = null
    this.tick = 0
    this.running = true
  }
  start() {
    if (this.interval) return
    this.interval = setInterval(() => {
      if (!this.running) return
      this.tick++
      // emit readings
      machines.forEach(m => {
        if (m.status !== 'offline') {
          const reading = genReading(m.machine_id, this.tick)
          this.dispatch({ type: 'reading', ts: reading.ts, payload: reading })
          if (this.tick % 5 === 0) {
            const healthUpdate = { machine_id: m.machine_id, health_score: m.health_score + (Math.random()-0.5)*2, status: m.status }
            this.dispatch({ type: 'health_update', ts: new Date().toISOString(), payload: healthUpdate })
          }
        }
      })
      // occasional new alert simulation
      if (this.tick % 30 === 0 && Math.random() < 0.3) {
        // simulate agent steps
        const alert = alerts[0]
        if (alert) {
          this.dispatch({ type: 'agent_step', ts: new Date().toISOString(), payload: { alert_id: alert.alert_id, agent: 'Monitor', summary: 'Watching anomaly trend...' } })
        }
      }
    }, 1000)
  }
  pause() { this.running = false }
  resume() { this.running = true }
  stop() { clearInterval(this.interval); this.interval = null }
  injectFaultEvent(alert) {
    this.dispatch({ type: 'alert_created', ts: new Date().toISOString(), payload: alert })
    setTimeout(() => {
      this.dispatch({ type: 'agent_step', ts: new Date().toISOString(), payload: { alert_id: alert.alert_id, agent: 'Diagnosis', summary: 'Searching manuals...' } })
    }, 1000)
    setTimeout(() => {
      this.dispatch({ type: 'diagnosis_ready', ts: new Date().toISOString(), payload: { alert_id: alert.alert_id } })
    }, 2500)
    setTimeout(() => {
      this.dispatch({ type: 'plan_ready', ts: new Date().toISOString(), payload: { alert_id: alert.alert_id } })
    }, 4000)
    setTimeout(() => {
      this.dispatch({ type: 'approval_required', ts: new Date().toISOString(), payload: { alert_id: alert.alert_id } })
    }, 5000)
  }
}
