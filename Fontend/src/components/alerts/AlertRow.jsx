import { Link } from 'react-router-dom'
import { SeverityBadge } from '../common/StatusDot'
import { formatRelativeTime, formatAbsoluteTime } from '../../utils/format'

export const AlertRow = ({ alert }) => {
  return (
    <Link to={`/alerts/${alert.alert_id}`} className='flex items-center gap-3 p-3 hover:bg-[var(--surface-hover)] transition-colors'>
      <SeverityBadge severity={alert.severity} />
      <div className='flex-1 min-w-0'>
        <div className='flex items-center gap-2'>
          <span className='font-mono text-xs'>{alert.machine_id}</span>
          <span className='text-xs text-[var(--text-muted)]'>{alert.alert_type}</span>
          <span className='text-xs font-mono tabular'>conf { (alert.confidence*100).toFixed(0)}%</span>
        </div>
        <div className='text-xs text-[var(--text-muted)] truncate'>{alert.description || alert.alert_id}</div>
      </div>
      <div className='text-right'>
        <div className='text-xs font-mono' title={formatAbsoluteTime(alert.ts)}>{formatRelativeTime(alert.ts)}</div>
        <div className='text-[10px] text-[var(--text-muted)]'>{alert.status}</div>
      </div>
    </Link>
  )
}
