import { Link } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'

export const BottleneckCard = ({ bottleneck, isDemo }) => {
  if (!bottleneck) {
    return (
      <div className='card p-4 border-l-4 border-[var(--healthy)]'>
        <div className='flex items-center gap-2'>
          <span className='text-[var(--healthy)]'>✓</span>
          <span className='font-medium'>No bottleneck detected</span>
        </div>
        <p className='text-xs text-[var(--text-muted)] mt-1'>All lines are running near ideal speed. This means no single station is limiting throughput right now.</p>
      </div>
    )
  }
  return (
    <div className='card p-4 border-l-4' style={{ borderLeftColor: 'var(--accent)' }}>
      <div className='flex items-start justify-between gap-3'>
        <div>
          <div className='flex items-center gap-2'>
            <AlertTriangle size={16} className='text-[var(--accent)]' />
            <h3 className='font-semibold'>Bottleneck: {bottleneck.line_id} → {bottleneck.machine_id}</h3>
            {isDemo && <span className='text-[10px] px-1.5 py-0.5 rounded bg-[var(--border)] font-mono'>Demo data</span>}
          </div>
          <p className='text-sm text-[var(--text-primary)] mt-1'>{bottleneck.reason}</p>
          <p className='text-xs text-[var(--text-muted)] mt-1'>Plain explanation: Station 4 torque tool is slowing the line, so every hour you lose output.</p>
        </div>
        <div className='text-right'>
          <div className='font-mono text-3xl font-bold text-[var(--accent)] tabular'>~{bottleneck.units_lost_per_hour}</div>
          <div className='text-xs text-[var(--text-muted)]'>units lost per hour</div>
        </div>
      </div>
      <div className='mt-3 flex gap-2'>
        <Link to={`/machines/${bottleneck.machine_id}`} className='px-3 py-1.5 text-xs rounded border border-[var(--border)] hover:bg-[var(--surface-hover)]'>See machine</Link>
        <Link to={`/alerts?machine_id=${bottleneck.machine_id}`} className='px-3 py-1.5 text-xs rounded bg-[var(--accent)] text-white'>See why (alerts)</Link>
      </div>
    </div>
  )
}
