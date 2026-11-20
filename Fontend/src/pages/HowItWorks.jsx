import { PageHeader } from '../layout/PageHeader'
import { HowItWorksDiagram } from '../components/help/HowItWorksDiagram'
import { Card } from '../components/common/Card'
import { useState } from 'react'

const faqs = [
  { q:'What is anomaly score?', a:'How unusual current readings are vs learned normal. 0=perfectly normal, 1=very unusual. Based on z-score of multivariate sensor distribution. Threshold 0.6 triggers alert. Good <0.3, warning 0.3-0.7, critical >0.7.' },
  { q:'What is RUL?', a:'Remaining Useful Life - estimate of hours left before likely failure. From degradation trend regression. Confidence shows uncertainty. Low RUL means plan maintenance soon. Good >200h, warning 50-200h, critical <50h.' },
  { q:'What is OEE?', a:'Overall Equipment Effectiveness = Availability × Performance × Quality. Availability = uptime/planned time, Performance = actual/ideal speed, Quality = good/total units. World-class 85%+, typical 60%.' },
  { q:'Why is approval requested?', a:'Policy: any stop_machine action or high risk plan requires human approval. Low risk tasks auto-execute. Approval ensures safety and prevents unnecessary downtime.' },
  { q:'Where do sources come from?', a:'Knowledge library: turbofan maintenance manuals, Bosch tooling docs, SECOM PM docs, failure logs, sensor specs. Indexed for vector search. Every diagnosis cites sources you can verify.' },
  { q:'What does audit log record?', a:'Chronological record of EVERY AI suggestion and human decision: time, actor (AI agent name or human), event type (suggestion/approval/rejection/execution/override), machine, summary, details with reasoning. Append-only, cannot edit/delete, export CSV.' },
]

export const HowItWorks = () => {
  const [openIdx, setOpenIdx] = useState(null)
  return (
    <div className='space-y-4'>
      <PageHeader title='How It Works' purpose='Interactive architecture diagram and FAQ explaining the system in plain language.' bullets={['Click blocks for plain explanation and page link where output appears','FAQ accordion with anomaly score, RUL, OEE, approval, sources, audit log','Cause-and-effect chain Sensor → Detection → Diagnosis → Plan → Action → Ticket each clickable']} />

      <HowItWorksDiagram />

      <Card className='p-4'>
        <h3 className='font-semibold mb-3'>Cause-and-effect chain (every step explained)</h3>
        <div className='space-y-2 text-sm'>
          <div><strong>Sensor</strong> → physical measurement (vibration g, temp C, current A). Data streamed 1Hz via WebSocket. You see in Machine Detail charts. Source of truth.</div>
          <div><strong>Detection</strong> → Monitor Agent compares to normal baseline. If anomaly_score {' > '} 0.6, creates alert with severity, confidence, top_sensors. See in Alerts list.</div>
          <div><strong>Diagnosis</strong> → Diagnosis Agent searches manuals/logs (RAG). Produces root_cause, confidence, reasoning, citations [1][2]. See in Alert Detail → Diagnosis tab.</div>
          <div><strong>Plan</strong> → Planner Agent creates action_type (schedule_maintenance, reduce_load...), steps, risk, requires_approval, rationale, estimated_impact. See Agent Actions.</div>
          <div><strong>Action</strong> → Supervisor checks risk policy. If high risk or stop_machine, requests human approval. Otherwise auto-executes. Toast shows result with link.</div>
          <div><strong>Ticket</strong> → Work order with repair instructions, tools, safety warning LOTO, expected result per step, status stepper. See Tickets page.</div>
          <div>Each step clickable and links to page showing its output. Audit log records everything.</div>
        </div>
      </Card>

      <Card className='p-4'>
        <h3 className='font-semibold mb-3'>FAQ</h3>
        <div className='space-y-2'>
          {faqs.map((f,i) => (
            <div key={i} className='border-b border-[var(--border)] pb-2'>
              <button onClick={() => setOpenIdx(openIdx===i ? null : i)} className='w-full text-left flex justify-between items-center py-2'>
                <span className='text-sm font-medium'>{f.q}</span>
                <span className='text-xs'>{openIdx===i ? '−' : '+'}</span>
              </button>
              {openIdx===i && <div className='text-xs text-[var(--text-muted)] pb-2 leading-relaxed'>{f.a}</div>}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
