import { Card } from '../common/Card'
import { Badge } from '../common/Badge'

export const PlanCard = ({ plan }) => {
  if (!plan) return null
  const typeLabel = {
    schedule_maintenance: 'Schedule Maintenance - plan repair during downtime window',
    reduce_load: 'Reduce Load - slow machine to prevent failure',
    reroute_production: 'Reroute Production - move work to other line',
    stop_machine: 'Stop Machine - immediate stop required for safety',
    inspect_quality: 'Inspect Quality - check recent units for defects',
    monitor_only: 'Monitor Only - watch trend, no action yet',
  }
  return (
    <Card className='p-4'>
      <div className='flex items-center gap-2 mb-2'>
        <h4 className='font-medium'>{typeLabel[plan.action_type] || plan.action_type}</h4>
        <Badge variant={plan.risk_level==='high' ? 'critical' : plan.risk_level==='medium' ? 'warning' : 'steel'}>{plan.risk_level} risk</Badge>
        {plan.requires_approval && <Badge variant='orange'>Requires approval</Badge>}
      </div>
      <p className='text-xs text-[var(--text-muted)] mb-3'>{plan.rationale}</p>
      <div className='space-y-1'>
        <div className='text-xs font-medium'>Steps:</div>
        <ol className='list-decimal ml-5 space-y-1 text-sm text-[var(--text-primary)]'>
          {plan.steps?.map((s,i) => <li key={i}>{s}</li>)}
        </ol>
      </div>
    </Card>
  )
}
