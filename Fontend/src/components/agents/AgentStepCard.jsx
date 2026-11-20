import { Eye, Search, Route, Wrench, Shield } from 'lucide-react'
import { Card } from '../common/Card'
import { useState } from 'react'

const iconMap = {
  Monitor: Eye,
  Diagnosis: Search,
  Planner: Route,
  Action: Wrench,
  Supervisor: Shield,
}

const roleMap = {
  Monitor: 'Watches sensor streams and detects anomalies',
  Diagnosis: 'Finds root cause by searching manuals and logs',
  Planner: 'Creates repair plan with risk and impact estimate',
  Action: 'Executes or requests approval for the plan',
  Supervisor: 'Checks risk and ensures human approves high-risk actions',
}

export const AgentStepCard = ({ event }) => {
  const [expanded, setExpanded] = useState(false)
  const Icon = iconMap[event.agent] || Search
  return (
    <Card className='p-3'>
      <div className='flex gap-3'>
        <div className='w-8 h-8 rounded-full border border-[var(--border)] flex items-center justify-center bg-[var(--bg)]'>
          <Icon size={14} className='text-[var(--steel)]' />
        </div>
        <div className='flex-1'>
          <div className='flex items-center gap-2'>
            <span className='text-sm font-medium'>{event.agent} Agent</span>
            <span className='text-xs text-[var(--text-muted)]'>{roleMap[event.agent] || ''}</span>
            <span className='ml-auto text-[10px] font-mono text-[var(--text-muted)]'>{event.duration_ms ? `${event.duration_ms}ms` : ''}</span>
          </div>
          <div className='text-xs text-[var(--text-muted)] mt-1'>Input: {event.input_summary}</div>
          <div className='text-sm text-[var(--text-primary)] mt-1'>Output: {event.output_summary}</div>
          {event.reasoning && (
            <button onClick={() => setExpanded(!expanded)} className='mt-1 text-xs text-[var(--accent)] underline'>{expanded ? 'Hide reasoning' : 'Show reasoning'}</button>
          )}
          {expanded && event.reasoning && (
            <div className='mt-2 p-2 rounded bg-[var(--bg)] border border-[var(--border)] text-xs text-[var(--text-muted)] leading-relaxed'>
              {event.reasoning}
            </div>
          )}
          <div className='text-[10px] font-mono text-[var(--text-muted)] mt-1'>{new Date(event.ts).toLocaleString()}</div>
        </div>
      </div>
    </Card>
  )
}
