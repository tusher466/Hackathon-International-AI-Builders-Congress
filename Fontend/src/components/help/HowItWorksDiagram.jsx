import { useState } from 'react'
import { Card } from '../common/Card'

const blocks = [
  { id:'sensors', label:'Sensors', desc:'Vibration, temperature, current, torque sampled 1Hz from 10 machines. Data streamed via WebSocket.', page:'/machines' },
  { id:'ingestion', label:'Ingestion', desc:'Normalizes sensor values, stores rolling window, calculates z-scores for anomaly detection.', page:'/machines/:id' },
  { id:'detection', label:'Detection Models', desc:'Monitor Agent runs statistical and ML models. Threshold: anomaly score >0.6 triggers alert.', page:'/alerts' },
  { id:'alert', label:'Alert', desc:'Created with severity, confidence, top sensors, machine ID. Starts Agent pipeline.', page:'/alerts/:id' },
  { id:'diagnosis', label:'Diagnosis Agent', desc:'Searches manuals and failure logs using RAG. Produces root cause, reasoning, citations.', page:'/alerts/:id tab Diagnosis' },
  { id:'planner', label:'Planner Agent', desc:'Generates steps, risk level, requires_approval flag, estimated impact (downtime, defects, energy).', page:'/actions' },
  { id:'supervisor', label:'Supervisor Agent', desc:'Policy: if risk high or stop_machine, require human approval. Otherwise auto-execute and create ticket.', page:'/actions' },
  { id:'knowledge', label:'Knowledge Library', desc:'Manuals, failure logs, sensor specs indexed for vector search. Every answer cites sources.', page:'/knowledge' },
  { id:'approval', label:'Human Approval', desc:'You see outcome preview: approve moves ticket to In Progress, reject cancels action. Both logged.', page:'/actions > Pending' },
  { id:'audit', label:'Audit Log', desc:'Append-only log of every AI suggestion and human decision. Filters and CSV export. Cannot edit/delete.', page:'/actions > Audit log' },
  { id:'ticket', label:'Ticket', desc:'Work order with repair instructions, safety warnings, status stepper, link to alert story.', page:'/tickets' },
]

export const HowItWorksDiagram = () => {
  const [selected, setSelected] = useState(null)
  return (
    <div className='space-y-4'>
      <div className='grid grid-cols-2 md:grid-cols-4 gap-3'>
        {blocks.map(b => (
          <button key={b.id} onClick={() => setSelected(b)} className={`card p-3 text-left hover:border-[var(--border-hover)] ${selected?.id===b.id ? 'border-[var(--accent)]' : ''}`}>
            <div className='text-sm font-medium'>{b.label}</div>
            <div className='text-[10px] text-[var(--text-muted)] mt-1 truncate'>{b.desc.slice(0,60)}...</div>
          </button>
        ))}
      </div>
      {selected && (
        <Card className='p-4'>
          <h4 className='font-semibold'>{selected.label}</h4>
          <p className='text-sm text-[var(--text-muted)] mt-1 leading-relaxed'>{selected.desc}</p>
          <div className='text-xs mt-2'>See it in: <span className='font-mono text-[var(--accent)]'>{selected.page}</span></div>
        </Card>
      )}
    </div>
  )
}
