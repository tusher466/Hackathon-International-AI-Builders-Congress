import { useState } from 'react'
import { Database, Eye, Search, Route, Wrench, Ticket } from 'lucide-react'

const stages = [
  { key: 'sensors', label: 'Sensors', icon: Database, desc: 'Machines send vibration, temperature, current every second.', owner: 'Ingestion service', page: 'Machine Detail shows live charts' },
  { key: 'detection', label: 'Detection', icon: Eye, desc: 'Anomaly models compare current readings to normal patterns.', owner: 'Monitor Agent (eye)', page: 'Alerts page lists what was detected' },
  { key: 'diagnosis', label: 'Diagnosis', icon: Search, desc: 'AI searches manuals and failure logs to find root cause.', owner: 'Diagnosis Agent (search)', page: 'Alert Detail > Diagnosis tab shows reasoning and citations' },
  { key: 'planning', label: 'Planning', icon: Route, desc: 'Planner creates repair steps with risk and estimated impact.', owner: 'Planner Agent (route)', page: 'Agent Actions shows work orders' },
  { key: 'action', label: 'Action', icon: Wrench, desc: 'High-risk actions require human approval; low-risk auto-runs.', owner: 'Supervisor Agent (shield)', page: 'Approvals & Audit Log' },
  { key: 'ticket', label: 'Ticket', icon: Ticket, desc: 'Work order with instructions, status, and verification steps.', owner: 'Ticketing system', page: 'Tickets page tracks execution' },
]

export const PipelineFlow = ({ counters = {} }) => {
  const [selected, setSelected] = useState(null)

  return (
    <div className='card p-4'>
      <h3 className='font-semibold mb-3'>How Factory Brain handles an incident: Sensor → Detection → Diagnosis → Planning → Action → Ticket</h3>
      <div className='flex flex-col md:flex-row items-stretch gap-0 overflow-x-auto'>
        {stages.map((s, idx) => {
          const Icon = s.icon
          const isActive = selected?.key === s.key
          return (
            <div key={s.key} className='flex flex-1 items-center'>
              <button
                onClick={() => setSelected(s)}
                className={`flex-1 flex flex-col items-center gap-2 p-3 rounded-[8px] border text-center transition-colors min-h-[100px] ${isActive ? 'border-[var(--accent)] bg-[var(--accent)]/10' : 'border-[var(--border)] bg-[var(--surface)] hover:border-[var(--border-hover)]'}`}
              >
                <Icon size={20} className={isActive ? 'text-[var(--accent)]' : 'text-[var(--steel)]'} />
                <span className='text-xs font-medium'>{s.label}</span>
                {counters[s.key] != null && <span className='text-[10px] font-mono px-1.5 py-0.5 rounded bg-[var(--border)]'>{counters[s.key]}</span>}
              </button>
              {idx < stages.length -1 && (
                <div className='w-8 h-0.5 bg-[var(--border)] relative mx-1 hidden md:block'>
                  <div className='absolute top-0 left-0 h-full w-2 bg-[var(--accent)] animate-[slide_1.2s_linear_infinite]' style={{ animation: 'slideDash 1.2s linear infinite' }} />
                </div>
              )}
            </div>
          )
        })}
      </div>
      {selected && (
        <div className='mt-4 p-3 rounded-[8px] bg-[var(--bg)] border border-[var(--border)]'>
          <div className='flex items-start justify-between gap-2'>
            <div>
              <div className='font-medium text-sm text-[var(--text-primary)]'>{selected.label}: What it does</div>
              <p className='text-xs text-[var(--text-muted)] mt-1'>{selected.desc}</p>
              <div className='mt-2 text-xs'>
                <span className='text-[var(--text-muted)]'>Owner: </span><span className='text-[var(--text-primary)]'>{selected.owner}</span>
              </div>
              <div className='mt-1 text-xs'>
                <span className='text-[var(--text-muted)]'>See it in: </span><span className='text-[var(--text-primary)]'>{selected.page}</span>
              </div>
            </div>
            <button onClick={() => setSelected(null)} className='text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)]'>Close</button>
          </div>
        </div>
      )}
      <style>{`
        @keyframes slideDash {
          0% { transform: translateX(-8px); }
          100% { transform: translateX(32px); }
        }
      `}</style>
    </div>
  )
}
