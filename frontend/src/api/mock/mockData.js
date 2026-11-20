const now = () => new Date().toISOString()

function rnd(min, max) {
  return Math.random() * (max - min) + min
}

export const machines = [
  { machine_id: 'TURBO-01', machine_type: 'turbofan', health_score: 92, status: 'healthy', last_seen: now(), open_alert_count: 0, line_id: 'LINE-A' },
  { machine_id: 'TURBO-02', machine_type: 'turbofan', health_score: 68, status: 'warning', last_seen: now(), open_alert_count: 1, line_id: 'LINE-A' },
  { machine_id: 'TURBO-03', machine_type: 'turbofan', health_score: 45, status: 'critical', last_seen: now(), open_alert_count: 2, line_id: 'LINE-B' },
  { machine_id: 'SECOM-01', machine_type: 'secom', health_score: 77, status: 'warning', last_seen: now(), open_alert_count: 1, line_id: 'LINE-A' },
  { machine_id: 'SECOM-02', machine_type: 'secom', health_score: 88, status: 'healthy', last_seen: now(), open_alert_count: 0, line_id: 'LINE-B' },
  { machine_id: 'SECOM-03', machine_type: 'secom', health_score: 51, status: 'warning', last_seen: now(), open_alert_count: 1, line_id: 'LINE-C' },
  { machine_id: 'BOSCH-01', machine_type: 'bosch', health_score: 95, status: 'healthy', last_seen: now(), open_alert_count: 0, line_id: 'LINE-C' },
  { machine_id: 'BOSCH-02', machine_type: 'bosch', health_score: 36, status: 'critical', last_seen: now(), open_alert_count: 2, line_id: 'LINE-C' },
  { machine_id: 'BOSCH-03', machine_type: 'bosch', health_score: 72, status: 'warning', last_seen: now(), open_alert_count: 1, line_id: 'LINE-A' },
  { machine_id: 'BOSCH-04', machine_type: 'bosch', health_score: 0, status: 'offline', last_seen: new Date(Date.now() - 1000*60*20).toISOString(), open_alert_count: 0, line_id: 'LINE-B' },
]

export const alerts = [
  {
    alert_id: 'ALT-1001',
    machine_id: 'TURBO-03',
    machine_type: 'turbofan',
    ts: new Date(Date.now() - 1000*60*12).toISOString(),
    alert_type: 'degradation',
    severity: 'critical',
    confidence: 0.92,
    anomaly_score: 0.87,
    predicted_rul: 38,
    top_sensors: [
      { name: 'vibration_bearing_7', deviation: 3.2, direction: 'high' },
      { name: 'temperature_core', deviation: 2.1, direction: 'high' },
      { name: 'pressure_lpc', deviation: -1.8, direction: 'low' },
    ],
    status: 'awaiting_approval',
    description: 'High vibration on bearing 7 and rising core temperature indicating wear progression.',
  },
  {
    alert_id: 'ALT-1002',
    machine_id: 'BOSCH-02',
    machine_type: 'bosch',
    ts: new Date(Date.now() - 1000*60*45).toISOString(),
    alert_type: 'defect_risk',
    severity: 'high',
    confidence: 0.78,
    anomaly_score: 0.64,
    defect_probability: 0.72,
    top_sensors: [
      { name: 'torque_station_4', deviation: 2.9, direction: 'high' },
      { name: 'current_spindle', deviation: 1.9, direction: 'high' },
    ],
    status: 'planned',
    description: 'Torque deviation at station 4 suggesting tool wear increasing defect rate.',
  },
  {
    alert_id: 'ALT-1003',
    machine_id: 'SECOM-01',
    machine_type: 'secom',
    ts: new Date(Date.now() - 1000*60*90).toISOString(),
    alert_type: 'anomaly',
    severity: 'medium',
    confidence: 0.66,
    anomaly_score: 0.58,
    top_sensors: [
      { name: 'chamber_pressure', deviation: 2.3, direction: 'high' },
      { name: 'gas_flow_rate', deviation: -1.2, direction: 'low' },
    ],
    status: 'diagnosed',
    description: 'Chamber pressure drift above 3 sigma for 30 cycles.',
  },
  {
    alert_id: 'ALT-1004',
    machine_id: 'BOSCH-03',
    machine_type: 'bosch',
    ts: new Date(Date.now() - 1000*60*200).toISOString(),
    alert_type: 'anomaly',
    severity: 'low',
    confidence: 0.51,
    anomaly_score: 0.41,
    top_sensors: [
      { name: 'vibration_axis_x', deviation: 1.4, direction: 'high' },
    ],
    status: 'open',
    description: 'Minor vibration increase on axis X, monitor trend.',
  },
]

export const traces = {
  'ALT-1001': [
    { agent: 'Monitor', ts: new Date(Date.now() - 1000*60*13).toISOString(), input_summary: 'Streaming sensor data for TURBO-03', output_summary: 'Anomaly score 0.87 crossed threshold 0.6', reasoning: 'Vibration bearing 7 has risen for 20 ticks, z-score 3.2. Temperature core up 2.1 sigma. Model flagged degradation.', duration_ms: 320 },
    { agent: 'Diagnosis', ts: new Date(Date.now() - 1000*60*12.5).toISOString(), input_summary: 'Alert data + last 100 readings + knowledge search', output_summary: 'Root cause: bearing wear progression leading to increased friction', reasoning: 'Checked manuals: bearing 7 wear shows vibration + temp rise. Failure log SEC-2023-04 matches pattern (cosine 0.89). RUL estimate from trend regression 38h.', duration_ms: 1240 },
    { agent: 'Planner', ts: new Date(Date.now() - 1000*60*12).toISOString(), input_summary: 'Diagnosis + impact history', output_summary: 'Propose schedule_maintenance with reduced load intermediate step', reasoning: 'Risk high, requires approval because stop_machine action. Estimated impact: downtime avoided 240min, defects 0. Approval needed per supervisor policy.', duration_ms: 890 },
    { agent: 'Supervisor', ts: new Date(Date.now() - 1000*60*11.8).toISOString(), input_summary: 'Plan risk=high, confidence 0.92', output_summary: 'Requires human approval, ticket created in awaiting_approval', reasoning: 'Policy: any stop_machine or risk high requires human. Auto-approve not allowed.', duration_ms: 120 },
  ],
  'ALT-1002': [
    { agent: 'Monitor', ts: new Date(Date.now() - 1000*60*47).toISOString(), input_summary: 'Torque station 4 stream', output_summary: 'Defect probability 0.72 trending up', reasoning: 'Torque variance increasing, correlates with tool wear season.', duration_ms: 210 },
    { agent: 'Diagnosis', ts: new Date(Date.now() - 1000*60*46).toISOString(), input_summary: 'Sensor + manual search', output_summary: 'Tool wear at station 4, replace within 12h', reasoning: 'Manual BOSCH-TOOL-04 says torque high 2.9 sigma indicates worn insert. Past logs show same.', duration_ms: 980 },
  ],
  'ALT-1003': [
    { agent: 'Monitor', ts: new Date(Date.now() - 1000*60*92).toISOString(), input_summary: 'Chamber pressure readings', output_summary: 'Anomaly score 0.58, drift detected', reasoning: 'Chamber pressure drifting, deviation 2.3 sigma.', duration_ms: 180 },
  ],
}

export const diagnoses = {
  'ALT-1001': {
    root_cause: 'Bearing 7 wear progression causing increased friction and heat in turbofan low-pressure compressor stage.',
    confidence: 0.92,
    reasoning: 'Vibration on bearing sensor 7 has risen 3.2 sigma above normal over last 30 readings. Core temperature rising 2.1 sigma correlates. Manual TMAN-07 section 4.2 describes this exact pattern as early wear. Failure log FL-2023-11 shows similar vibration led to failure in 42h. RUL regression from trend gives 38h remaining.',
    citations: [
      { index: 1, source: 'TMAN-07 Turbofan Maintenance Manual', section: '4.2 Bearing wear signatures', doc_type: 'manual', excerpt: 'Vibration increase >3 sigma on bearing sensors 6-8 with concomitant core temperature rise indicates early bearing wear...', score: 0.89 },
      { index: 2, source: 'Failure Log FL-2023-11', section: 'TURBO-02 failure analysis', doc_type: 'failure log', excerpt: 'Prior to failure, vibration_bearing_7 rose from 0.4 to 3.1 sigma over 2 days, temperature_core 1.8 sigma. RUL at alert 41h, actual 38h.', score: 0.87 },
    ],
  },
  'ALT-1002': {
    root_cause: 'Torque tool at station 4 worn, causing increased resistance and defect risk on Bosch assembly line.',
    confidence: 0.78,
    reasoning: 'Torque station 4 deviation 2.9 sigma high, current draw up 1.9 sigma. Manual indicates insert wear past 5000 cycles causes this. Tool cycle count 5230.',
    citations: [
      { index: 1, source: 'BOSCH-TOOL-04 Tooling Manual', section: 'Tool wear limits', doc_type: 'manual', excerpt: 'When torque exceeds 2.5 sigma above baseline for >20 cycles, inspect insert for wear. Typical life 5000 cycles.', score: 0.82 },
    ],
  },
  'ALT-1003': {
    root_cause: 'Chamber pressure regulator drift due to partial valve blockage in SECOM process chamber.',
    confidence: 0.66,
    reasoning: 'Chamber pressure 2.3 sigma high, gas flow low. SECOM manual 3.1 notes regulator drift after 300 cycles since clean. Last clean 340 cycles ago.',
    citations: [
      { index: 1, source: 'SECOM-PM-03 Preventive Maintenance', section: '3.1 Chamber regulator', doc_type: 'manual', excerpt: 'Regulator requires cleaning every 300 cycles. Drift symptom: chamber pressure +2 sigma, gas_flow -1 sigma.', score: 0.71 },
    ],
  },
}

export const plans = {
  'ALT-1001': {
    action_type: 'schedule_maintenance',
    steps: [
      'Reduce engine load to 70% immediately to slow wear',
      'Schedule hot-section inspection within 12h',
      'Prepare bearing replacement kit T-KIT-7',
      'Perform replacement during next planned downtime window (4h)',
      'Run post-maintenance vibration baseline capture',
    ],
    risk_level: 'high',
    requires_approval: true,
    rationale: 'Bearing wear will progress to failure in ~38h if not addressed. Reducing load slows progression and buys time. Full stop not yet required but monitoring must be continuous.',
    estimated_impact: { downtime_avoided_minutes: 240, defects_prevented: 0, energy_saved_kwh: 120 },
  },
  'ALT-1002': {
    action_type: 'inspect_quality',
    steps: [
      'Reduce line speed 10% at station 4',
      'Inspect last 50 units from station 4 for defects',
      'Replace torque tool insert at station 4',
      'Recalibrate torque profile',
    ],
    risk_level: 'medium',
    requires_approval: false,
    rationale: 'Tool wear increasing defect risk. Immediate replacement prevents defect cascade.',
    estimated_impact: { downtime_avoided_minutes: 60, defects_prevented: 45, energy_saved_kwh: 15 },
  },
  'ALT-1003': {
    action_type: 'reduce_load',
    steps: [
      'Schedule chamber clean in next 24h',
      'Monitor pressure trend every 10 cycles',
      'If pressure exceeds 3 sigma, pause process',
    ],
    risk_level: 'low',
    requires_approval: false,
    rationale: 'Early drift, not yet critical. Cleaning will reset regulator.',
    estimated_impact: { downtime_avoided_minutes: 30, defects_prevented: 12, energy_saved_kwh: 5 },
  },
}

export const tickets = [
  {
    ticket_id: 'TCK-5001',
    alert_id: 'ALT-1001',
    machine_id: 'TURBO-03',
    title: 'Bearing 7 wear - schedule maintenance',
    description: 'High vibration on bearing 7 and core temperature rise indicates wear. RUL 38h estimated.',
    priority: 'high',
    status: 'awaiting_approval',
    instructions: 'Reduce engine load to 70%, schedule inspection within 12h, prepare replacement kit, 4h window for swap, capture baseline after.',
    created_at: new Date(Date.now() - 1000*60*11).toISOString(),
    updated_at: new Date(Date.now() - 1000*60*11).toISOString(),
  },
  {
    ticket_id: 'TCK-5002',
    alert_id: 'ALT-1002',
    machine_id: 'BOSCH-02',
    title: 'Replace torque tool station 4',
    description: 'Torque deviation indicates tool wear, replace insert',
    priority: 'medium',
    status: 'in_progress',
    instructions: 'Reduce line speed 10%, inspect last 50 units, replace insert, recalibrate.',
    created_at: new Date(Date.now() - 1000*60*44).toISOString(),
    updated_at: new Date(Date.now() - 1000*60*30).toISOString(),
  },
  {
    ticket_id: 'TCK-5003',
    alert_id: 'ALT-1003',
    machine_id: 'SECOM-01',
    title: 'Chamber regulator clean',
    description: 'Chamber pressure drift, clean regulator',
    priority: 'low',
    status: 'open',
    instructions: 'Schedule clean in 24h, monitor every 10 cycles.',
    created_at: new Date(Date.now() - 1000*60*88).toISOString(),
    updated_at: new Date(Date.now() - 1000*60*88).toISOString(),
  },
]

export const knowledgeBase = [
  { source: 'TMAN-07 Turbofan Maintenance Manual', section: '4.2 Bearing wear signatures', doc_type: 'manual', text: 'Vibration increase >3 sigma on bearing sensors 6-8 with concomitant core temperature rise indicates early bearing wear. Recommended action: reduce load, inspect within 12h, RUL typically 30-50h at this stage.', score: 0.89 },
  { source: 'BOSCH-TOOL-04 Tooling Manual', section: 'Tool wear limits', doc_type: 'manual', text: 'When torque exceeds 2.5 sigma above baseline for >20 cycles, inspect insert for wear. Typical life 5000 cycles. Continued use increases defect rate by 12% per day.', score: 0.82 },
  { source: 'SECOM-PM-03 Preventive Maintenance', section: '3.1 Chamber regulator', doc_type: 'manual', text: 'Regulator requires cleaning every 300 cycles. Drift symptom: chamber pressure +2 sigma, gas_flow -1 sigma. If not cleaned, risk of process drift and wafer defects.', score: 0.77 },
  { source: 'Failure Log FL-2023-11', section: 'TURBO-02 failure analysis', doc_type: 'failure log', text: 'Prior to failure, vibration_bearing_7 rose from 0.4 to 3.1 sigma over 2 days, temperature_core 1.8 sigma. RUL at alert 41h, actual 38h. Root cause confirmed bearing spall.', score: 0.87 },
  { source: 'Sensor Spec TURBO-SEC-01', section: '2.4 Vibration thresholds', doc_type: 'sensor log', text: 'Normal vibration_bearing_7 range 0.2-0.8 g. Alert at 2.0 g sustained. Critical at 3.0 g. Sample rate 1Hz.', score: 0.65 },
  { source: 'Line 3 Incident 2024-02', section: 'Root cause', doc_type: 'failure log', text: 'Line 3 stopped at 2AM due to torque tool failure at station 4. Preceded by 2 days of rising torque variance. Fix was insert replacement, 45 min downtime.', score: 0.91 },
]

export const oee = {
  availability: 0.89,
  performance: 0.84,
  quality: 0.96,
  oee: 0.72,
  per_line: [
    { line_id: 'LINE-A', availability: 0.91, performance: 0.86, quality: 0.97, oee: 0.76 },
    { line_id: 'LINE-B', availability: 0.82, performance: 0.79, quality: 0.94, oee: 0.61 },
    { line_id: 'LINE-C', availability: 0.92, performance: 0.88, quality: 0.96, oee: 0.78 },
  ],
}

export const bottlenecks = [
  { line_id: 'LINE-C', machine_id: 'BOSCH-02', reason: 'Station 4 torque tool worn, slowing assembly cycle by 18%', units_lost_per_hour: 124, since: new Date(Date.now() - 1000*60*60*5).toISOString() },
]

export const impact = {
  downtime_avoided: 3420,
  defects_prevented: 412,
  energy_saved: 685,
  alerts_by_severity: { low: 12, medium: 8, high: 5, critical: 2 },
  auto_resolved_count: 18,
  human_approved_count: 9,
}

export const auditLog = [
  { id: 'AUD-001', ts: new Date(Date.now() - 1000*60*11).toISOString(), actor_type: 'ai', actor: 'Supervisor Agent', event_type: 'suggestion', alert_id: 'ALT-1001', ticket_id: 'TCK-5001', machine_id: 'TURBO-03', summary: 'Proposed schedule_maintenance for bearing wear', details: { reasoning: 'RUL 38h, risk high, approval required', citations: ['TMAN-07 4.2', 'FL-2023-11'] } },
  { id: 'AUD-002', ts: new Date(Date.now() - 1000*60*44).toISOString(), actor_type: 'ai', actor: 'Planner Agent', event_type: 'suggestion', alert_id: 'ALT-1002', ticket_id: 'TCK-5002', machine_id: 'BOSCH-02', summary: 'Proposed tool replacement at station 4', details: { reasoning: 'Torque 2.9 sigma high', citations: ['BOSCH-TOOL-04'] } },
  { id: 'AUD-003', ts: new Date(Date.now() - 1000*60*30).toISOString(), actor_type: 'human', actor: 'Alex Rivera', event_type: 'approval', alert_id: 'ALT-1002', ticket_id: 'TCK-5002', machine_id: 'BOSCH-02', summary: 'Approved tool replacement', details: { comment: 'Checked inventory, kit available. Proceed.' } },
  { id: 'AUD-004', ts: new Date(Date.now() - 1000*60*88).toISOString(), actor_type: 'ai', actor: 'Diagnosis Agent', event_type: 'suggestion', alert_id: 'ALT-1003', ticket_id: 'TCK-5003', machine_id: 'SECOM-01', summary: 'Diagnosed chamber regulator drift', details: { reasoning: 'Pressure +2.3 sigma after 340 cycles since clean' } },
  { id: 'AUD-005', ts: new Date(Date.now() - 1000*60*120).toISOString(), actor_type: 'human', actor: 'Jamie Chen', event_type: 'override', alert_id: 'ALT-999', ticket_id: null, machine_id: 'TURBO-01', summary: 'Manually set health to 92 after maintenance verification', details: { comment: 'Post-maintenance check completed, vibration nominal.' } },
]

export const health = {
  status: 'degraded',
  message: '2 machines need action now, 4 need attention',
  stream_state: 'running',
  connected_machines: 9,
}

export const chatExamples = [
  {
    q: 'Why did Line 3 stop at 2 AM?',
    a: 'Line 3 stopped at 2AM on 2024-02-18 due to torque tool failure at station 4. Logs show torque variance rising for 2 days before. The insert had exceeded its 5000 cycle life at 5230 cycles. Fix was replacement, 45 minutes downtime. This is similar to current BOSCH-02 alert ALT-1002 which also shows torque deviation.',
    citations: [
      { index: 1, source: 'Line 3 Incident 2024-02', section: 'Root cause', doc_type: 'failure log', excerpt: 'Line 3 stopped at 2AM due to torque tool failure at station 4. Preceded by 2 days of rising torque variance. Fix was insert replacement, 45 min downtime.', score: 0.91 },
      { index: 2, source: 'BOSCH-TOOL-04 Tooling Manual', section: 'Tool wear limits', doc_type: 'manual', excerpt: 'When torque exceeds 2.5 sigma above baseline for >20 cycles, inspect insert for wear. Typical life 5000 cycles.', score: 0.82 },
    ],
    related_alert_ids: ['ALT-1002'],
  },
  {
    q: 'Which machine is most likely to fail this week?',
    a: 'TURBO-03 has the highest failure risk. RUL estimate is 38 hours based on bearing wear trend (vibration 3.2 sigma high). Confidence 92%. BOSCH-02 is second: tool wear defect probability 72% but not immediate catastrophic failure. Recommend prioritizing TURBO-03 maintenance.',
    citations: [
      { index: 1, source: 'TMAN-07 Turbofan Maintenance Manual', section: '4.2 Bearing wear signatures', doc_type: 'manual', excerpt: 'Vibration increase >3 sigma on bearing sensors 6-8 with concomitant core temperature rise indicates early bearing wear...', score: 0.89 },
      { index: 2, source: 'Failure Log FL-2023-11', section: 'TURBO-02 failure analysis', doc_type: 'failure log', excerpt: 'Prior to failure, vibration_bearing_7 rose from 0.4 to 3.1 sigma over 2 days... RUL at alert 41h, actual 38h.', score: 0.87 },
    ],
    related_alert_ids: ['ALT-1001', 'ALT-1002'],
  },
]

export function genReading(machineId, tick) {
  const base = {
    'TURBO-01': { vibration: 0.4, temp: 85, current: 12 },
    'TURBO-02': { vibration: 0.9, temp: 95, current: 13.5 },
    'TURBO-03': { vibration: 2.8, temp: 112, current: 15.2 },
    'SECOM-01': { vibration: 0.5, temp: 65, current: 8.1 },
    'BOSCH-02': { vibration: 1.8, temp: 72, current: 14.3 },
  }
  const b = base[machineId] || { vibration: 0.5, temp: 70, current: 10 }
  return {
    machine_id: machineId,
    ts: new Date().toISOString(),
    sensors: {
      vibration: b.vibration + rnd(-0.1, 0.1) + Math.sin(tick/20)*0.05,
      vibration_bearing_7: machineId === 'TURBO-03' ? 3.2 + rnd(-0.2,0.2) : b.vibration + rnd(-0.1,0.1),
      temperature: b.temp + rnd(-1,1),
      temperature_core: machineId === 'TURBO-03' ? 112 + rnd(-2,2) : b.temp + rnd(-1,1),
      current: b.current + rnd(-0.3,0.3),
      chamber_pressure: machineId.startsWith('SECOM') ? 2.3 + rnd(-0.2,0.2) : rnd(0.9,1.1),
      torque_station_4: machineId === 'BOSCH-02' ? 2.9 + rnd(-0.2,0.2) : rnd(0.2,0.6),
    }
  }
}
