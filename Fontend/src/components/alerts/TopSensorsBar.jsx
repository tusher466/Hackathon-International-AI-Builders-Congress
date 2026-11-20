import { Card } from '../common/Card'

export const TopSensorsBar = ({ sensors }) => {
  if (!sensors || sensors.length===0) return null
  const maxDev = Math.max(...sensors.map(s => Math.abs(s.deviation)))
  return (
    <Card className='p-4'>
      <h4 className='text-sm font-medium mb-3'>Top contributing sensors (why this alert fired)</h4>
      <div className='space-y-2'>
        {sensors.map(s => (
          <div key={s.name} className='flex items-center gap-3'>
            <span className='font-mono text-xs w-40 truncate'>{s.name}</span>
            <div className='flex-1 h-2 bg-[var(--border)] rounded-full overflow-hidden'>
              <div className='h-full bg-[var(--accent)]' style={{ width: `${(Math.abs(s.deviation)/maxDev)*100}%` }} />
            </div>
            <span className='font-mono text-xs tabular w-20 text-right'>{s.deviation >0 ? '+' : ''}{s.deviation.toFixed(1)}σ {s.direction}</span>
          </div>
        ))}
      </div>
      <p className='text-xs text-[var(--text-muted)] mt-2'>Plain explanation: These sensors are most unusual vs normal. σ (sigma) means standard deviations away from average. Bigger = more unusual.</p>
    </Card>
  )
}
