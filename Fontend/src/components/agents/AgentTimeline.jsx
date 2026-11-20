import { AgentStepCard } from './AgentStepCard'

export const AgentTimeline = ({ events }) => {
  if (!events || events.length===0) {
    return <div className='text-xs text-[var(--text-muted)]'>No agent steps yet. When an alert fires, you will see Monitor → Diagnosis → Planner steps appear here live, each with reasoning.</div>
  }
  return (
    <div className='space-y-3'>
      {events.map((e,i) => <AgentStepCard key={i} event={e} />)}
    </div>
  )
}
