// Central outcome preview texts for every action button
export const outcomes = {
  approve: {
    label: 'Approve',
    preview: [
      'The AI agents resume and execute the planned action',
      'The ticket moves to In Progress',
      'The technician assigned is notified',
      'An audit log entry is created showing you approved it',
    ],
  },
  reject: {
    label: 'Reject',
    preview: [
      'The planned action is cancelled and will not run',
      'The ticket moves to Rejected',
      'The system continues monitoring without taking action',
      'Your comment and decision are recorded in the audit log',
    ],
  },
  injectFault: {
    label: 'Inject Fault',
    preview: [
      'A simulated sensor fault is added to the selected machine',
      'The live charts will show the drift/spike within seconds',
      'An alert will be created when the anomaly score crosses threshold',
      'The agent pipeline will start: Diagnosis → Plan → Approval → Ticket',
    ],
  },
  startStream: {
    label: 'Start Stream',
    preview: [
      'Sensor data streaming begins for all machines',
      'Live charts begin updating every second',
      'The connection indicator turns to Live',
      'Detection models start watching for anomalies',
    ],
  },
  pauseStream: {
    label: 'Pause Stream',
    preview: [
      'Sensor streaming pauses, charts freeze',
      'No new alerts will be generated while paused',
      'You can resume at any time without losing data',
    ],
  },
  resumeStream: {
    label: 'Resume Stream',
    preview: [
      'Sensor streaming resumes from where it paused',
      'Charts continue updating',
      'Detection restarts',
    ],
  },
  stopStream: {
    label: 'Stop Stream',
    preview: [
      'Streaming stops completely',
      'Machines may show as offline after a short delay',
      'You will need to start again to resume',
    ],
  },
  reset: {
    label: 'Reset Simulation',
    preview: [
      'All injected faults are cleared',
      'Mock alerts and tickets from simulation are removed',
      'Machines return to healthy baseline',
      'OEE and metrics reset to demo defaults',
      'This cannot be undone in demo mode',
    ],
  },
  ask: {
    label: 'Ask',
    preview: [
      'Your question is sent to the AI',
      'The system searches manuals, logs, and sensor data',
      'You will get an answer with cited sources you can click to verify',
    ],
  },
  exportCsv: {
    label: 'Export CSV',
    preview: [
      'The current filtered audit log is downloaded as a CSV file',
      'File contains time, actor, event type, machine, and summary',
    ],
  },
}

export const infoTips = {
  healthScore: {
    title: 'Health Score 0-100',
    content: 'Overall machine condition. Combines anomaly score (40%), RUL shortfall (30%), defect probability (20%), and open alert count (10%). 80-100 = Running well, 50-79 = Needs attention, <50 = Needs action now.',
  },
  oee: {
    title: 'OEE = Availability × Performance × Quality',
    content: 'Availability = uptime / planned time. Shows if machines are running when they should. Performance = actual output / ideal output. Shows if line runs at target speed. Quality = good units / total units. World-class 85%+, typical 60%, <40% poor.',
  },
  anomalyScore: {
    title: 'Anomaly Score 0-1',
    content: 'How unusual readings are vs learned normal. Based on z-score of multivariate sensor distribution. Good <0.3, warning 0.3-0.7, critical >0.7.',
  },
  confidence: {
    title: 'Confidence 0-100%',
    content: 'How certain the system is. Based on signal strength and historical match. >80% high, 50-80% medium, <50% low and needs human review.',
  },
  bottleneck: {
    title: 'Bottleneck: line constraint',
    content: 'The station limiting total throughput. Calculated as difference between ideal line speed and actual speed at this station. Units lost per hour = throughput × (1 - station efficiency). Fix this for biggest gain.',
  },
  rul: {
    title: 'Remaining Useful Life',
    content: 'Prediction of hours until failure, from degradation trend regression. Confidence shows prediction uncertainty. Low RUL means plan maintenance soon.',
  },
  impact: {
    title: 'Impact is estimated',
    content: 'Downtime avoided = historical avg downtime for similar fault minus expected downtime with early action. Defects prevented = defect rate trend × exposure time. Energy saved = reduced load / idle time avoided. These are predictions, not guarantees.',
  },
  oeeAvailability: {
    title: 'Availability',
    content: 'Planned production time minus downtime, divided by planned time. Measures if machines are running when scheduled.',
  },
  oeePerformance: {
    title: 'Performance',
    content: 'Actual output rate divided by ideal rate. <100% means micro-stops, slow cycles, or reduced speed.',
  },
  oeeQuality: {
    title: 'Quality',
    content: 'Good units divided by total units produced. <100% means defects, rework, or scrap.',
  },
}
