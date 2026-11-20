export const glossaryTerms = [
  {
    term: 'RUL',
    short: 'Remaining Useful Life',
    definition: 'An estimate of how many hours or cycles a machine has left before it will likely fail. Higher is better. Calculated from sensor degradation trends and historical failure patterns.',
    goodBad: 'Good: >200 hours. Warning: 50-200h. Critical: <50h.',
  },
  {
    term: 'Anomaly Score',
    short: 'How unusual the current readings are',
    definition: 'A number that shows how far current sensor data is from normal behavior. 0 = perfectly normal, 1 = very unusual. Based on statistical distance from learned normal patterns.',
    goodBad: 'Good: <0.3. Warning: 0.3-0.7. Critical: >0.7.',
  },
  {
    term: 'OEE',
    short: 'Overall Equipment Effectiveness',
    definition: 'A single number showing how well a line is running. Formula: Availability × Performance × Quality. Availability = uptime ÷ planned time. Performance = actual speed ÷ ideal speed. Quality = good units ÷ total units.',
    goodBad: 'World-class: 85%+. Typical factory: 60%. Poor: <40%.',
  },
  {
    term: 'RAG',
    short: 'Retrieval Augmented Generation',
    definition: 'The AI searches your manuals and logs for relevant passages before answering, so every answer shows its sources you can verify.',
    goodBad: '',
  },
  {
    term: 'Confidence',
    short: 'How sure the system is',
    definition: '0-100% showing how certain the detection or diagnosis is. Higher means more evidence. Low confidence answers trigger human review.',
    goodBad: 'High: >80%. Medium: 50-80%. Low: <50% (needs human check).',
  },
  {
    term: 'Bottleneck',
    short: 'Slowest station limiting the line',
    definition: 'The machine or station that limits total output. Fixing it gives the biggest throughput gain. Measured in units lost per hour if it runs slow.',
    goodBad: 'Want 0. Any number means lost production.',
  },
  {
    term: 'Health Score',
    short: 'Overall machine condition 0-100',
    definition: 'Combines sensor anomalies, RUL, defect risk, and open alerts into one number. 100 = perfect. Calculated from weighted sensor deviations and historical health patterns.',
    goodBad: 'Healthy: 80-100. Warning: 50-79. Critical: <50.',
  },
  {
    term: 'Top Sensors',
    short: 'Sensors contributing most to an alert',
    definition: 'The 3-5 sensors whose readings are most unusual compared to normal, ranked by deviation amount. They point to the likely physical cause.',
    goodBad: '',
  },
  {
    term: 'Estimated Impact',
    short: 'Predicted benefit if you act',
    definition: 'The AI estimates downtime avoided, defects prevented, and energy saved based on similar past incidents and current performance trends. Labeled as estimates because they are predictions.',
    goodBad: '',
  },
  {
    term: 'Agent',
    short: 'AI specialist for one job',
    definition: 'Monitor Agent watches for anomalies → Diagnosis Agent finds cause using manuals → Planner Agent makes a repair plan → Supervisor checks risk and requests approval if needed.',
    goodBad: '',
  },
]

export const getGlossaryDef = (term) => {
  return glossaryTerms.find(t => t.term.toLowerCase() === term.toLowerCase())
}
