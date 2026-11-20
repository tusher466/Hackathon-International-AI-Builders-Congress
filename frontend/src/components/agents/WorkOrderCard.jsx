import { useState } from 'react'
import { Card } from '../common/Card'
import { Badge } from '../common/Badge'
import { OutcomeButton } from '../common/OutcomeButton'
import { outcomes } from '../../utils/outcomes'
import { useApprove, useReject } from '../../hooks/useApprovals'
import { toast } from '../common/Toast'
import { formatRelativeTime } from '../../utils/format'

export const WorkOrderCard = ({ item }) => {
  const [comment, setComment] = useState('')
  const [decidedBy, setDecidedBy] = useState('Demo User')
  const approveMut = useApprove()
  const rejectMut = useReject()

  const handleApprove = () => {
    approveMut.mutate({ alertId: item.alert_id, body: { decided_by: decidedBy, comment } }, {
      onSuccess: (res) => {
        toast.success(`Approved work order for ${item.machine_id}. Ticket ${res.ticket?.ticket_id} now in progress.`, { href: `/tickets/${res.ticket?.ticket_id}`, label: 'View ticket' })
      },
      onError: () => {
        toast.error('Failed to approve. Please retry.')
      }
    })
  }

  const handleReject = () => {
    rejectMut.mutate({ alertId: item.alert_id, body: { decided_by: decidedBy, comment } }, {
      onSuccess: () => {
        toast.success(`Rejected work order for ${item.machine_id}. System will continue monitoring.`)
      }
    })
  }

  return (
    <Card className='p-4'>
      <div className='flex items-start justify-between gap-2 mb-2'>
        <div>
          <div className='flex items-center gap-2'>
            <span className='font-mono text-sm font-semibold'>{item.machine_id}</span>
            <Badge variant='steel'>{item.alert_type}</Badge>
            <Badge variant={item.severity==='critical' ? 'critical' : item.severity==='high' ? 'warning' : 'neutral'}>{item.severity}</Badge>
          </div>
          <div className='text-xs text-[var(--text-muted)] mt-1'>Alert {item.alert_id} • {formatRelativeTime(item.ticket?.created_at || new Date().toISOString())}</div>
        </div>
        <div className='text-xs font-mono'>Conf {(item.confidence*100).toFixed(0)}%</div>
      </div>

      <div className='mt-2'>
        <div className='text-sm font-medium'>What the AI wants to do:</div>
        <div className='text-sm mt-1'>{item.plan?.action_type} - {item.plan?.rationale}</div>
        <div className='text-xs text-[var(--text-muted)] mt-2'>Why: {item.diagnosis?.root_cause}</div>
        {item.diagnosis?.citations?.slice(0,2).map(c => (
          <div key={c.index} className='text-xs mt-1 font-mono bg-[var(--bg)] p-1 rounded border border-[var(--border)]'>[{c.index}] {c.source}: "{c.excerpt.slice(0,80)}..."</div>
        ))}
      </div>

      <div className='grid grid-cols-2 gap-3 mt-3 text-xs'>
        <div className='p-2 rounded bg-[var(--bg)] border border-[var(--border)]'>
          <div className='font-medium text-[var(--healthy)]'>If you approve:</div>
          <ul className='list-disc ml-4 mt-1 space-y-0.5 text-[var(--text-muted)]'>
            {outcomes.approve.preview.slice(0,3).map((o,i) => <li key={i}>{o}</li>)}
          </ul>
        </div>
        <div className='p-2 rounded bg-[var(--bg)] border border-[var(--border)]'>
          <div className='font-medium text-[var(--critical)]'>If you reject:</div>
          <ul className='list-disc ml-4 mt-1 space-y-0.5 text-[var(--text-muted)]'>
            {outcomes.reject.preview.slice(0,3).map((o,i) => <li key={i}>{o}</li>)}
          </ul>
        </div>
      </div>

      <div className='mt-3 grid grid-cols-2 gap-2'>
        <input placeholder='Your name (decided_by)' value={decidedBy} onChange={e=>setDecidedBy(e.target.value)} className='px-2 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)]' />
        <input placeholder='Optional comment' value={comment} onChange={e=>setComment(e.target.value)} className='px-2 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)]' />
      </div>

      <div className='mt-3 flex gap-2'>
        <OutcomeButton label='Approve' variant='primary' outcomes={outcomes.approve.preview} onConfirm={handleApprove} className='flex-1' />
        <OutcomeButton label='Reject' variant='outline' outcomes={outcomes.reject.preview} onConfirm={handleReject} className='flex-1' />
      </div>

      <div className='mt-2 text-xs text-[var(--text-muted)]'>Risk level: <span className={item.plan?.risk_level==='high' ? 'text-[var(--critical)]' : 'text-[var(--warning)]'}>{item.plan?.risk_level}</span> • Estimates: {item.plan?.estimated_impact?.downtime_avoided_minutes}min downtime avoided</div>
    </Card>
  )
}
