import { AlertRow } from './AlertRow'
import { Card } from '../common/Card'
import { EmptyState } from '../common/EmptyState'

export const AlertFeed = ({ alerts, limit=8 }) => {
  const list = alerts?.slice(0, limit) || []
  if (list.length===0) {
    return <EmptyState title='No active alerts' description='When the AI detects something unusual, alerts will appear here with severity, machine, and cause. Alerts are created automatically from sensor streaming.' />
  }
  return (
    <Card className='p-0 overflow-hidden'>
      <div className='p-3 border-b border-[var(--border)] font-medium text-sm'>Active Alerts (latest {limit})</div>
      <div className='divide-y divide-[var(--border)]'>
        {list.map(a => <AlertRow key={a.alert_id} alert={a} />)}
      </div>
    </Card>
  )
}
