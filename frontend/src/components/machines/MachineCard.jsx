import { Link } from 'react-router-dom'
import { Card } from '../common/Card'
import { StatusDot } from '../common/StatusDot'
import { InfoTip } from '../common/InfoTip'
import { infoTips } from '../../utils/outcomes'
import { formatMachineType } from '../../utils/format'
import { HealthGauge } from './HealthGauge'

export const MachineCard = ({ machine }) => {
  return (
    <Link to={`/machines/${machine.machine_id}`} className='block'>
      <Card hover className='h-full'>
        <div className='flex items-start justify-between gap-2 mb-2'>
          <div>
            <div className='font-mono font-semibold text-[var(--text-primary)]'>{machine.machine_id}</div>
            <div className='text-xs text-[var(--text-muted)]'>{formatMachineType(machine.machine_type)} • Line {machine.line_id}</div>
          </div>
          <StatusDot status={machine.status} />
        </div>
        <div className='flex items-center gap-3 my-3'>
          <HealthGauge value={machine.health_score} size={64} />
          <div className='flex-1'>
            <div className='flex items-center gap-2'>
              <span className='text-xs text-[var(--text-muted)]'>Health Score</span>
              <InfoTip title={infoTips.healthScore.title} content={infoTips.healthScore.content} />
            </div>
            <div className='font-mono text-2xl font-bold tabular'>{machine.health_score}</div>
            <div className='text-xs text-[var(--text-muted)]'>Open alerts: {machine.open_alert_count} • Last seen: {new Date(machine.last_seen).toLocaleTimeString()}</div>
          </div>
        </div>
        <div className='h-8 flex items-end gap-0.5'>
          {Array.from({ length: 20 }).map((_, i) => {
            const h = 4 + Math.random() * 20
            return <div key={i} className='flex-1 rounded-sm' style={{ height: `${h}px`, background: machine.status === 'critical' ? 'var(--critical)' : machine.status === 'warning' ? 'var(--warning)' : 'var(--steel)', opacity: 0.6 }} />
          })}
        </div>
      </Card>
    </Link>
  )
}
