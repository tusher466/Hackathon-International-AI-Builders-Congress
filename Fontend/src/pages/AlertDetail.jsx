import { useParams } from 'react-router-dom'
import { useState } from 'react'
import { useAlert } from '../hooks/useAlerts'
import { useTrace } from '../hooks/useTrace'
import { PageHeader } from '../layout/PageHeader'
import { Tabs } from '../components/common/Tabs'
import { Card } from '../components/common/Card'
import { SeverityBadge } from '../components/common/StatusDot'
import { TopSensorsBar } from '../components/alerts/TopSensorsBar'
import { AgentTimeline } from '../components/agents/AgentTimeline'
import { CitationList } from '../components/agents/CitationList'
import { PlanCard } from '../components/agents/PlanCard'
import { ImpactEstimateCard } from '../components/agents/ImpactEstimateCard'
import { RepairInstructions } from '../components/tickets/RepairInstructions'
import { TicketCard } from '../components/tickets/TicketCard'
import { OutcomeButton } from '../components/common/OutcomeButton'
import { outcomes } from '../utils/outcomes'
import { useApprove, useReject } from '../hooks/useApprovals'
import { toast } from '../components/common/Toast'
import { SensorChart } from '../components/machines/SensorChart'
import { useMachineReadings } from '../hooks/useMachines'
import { formatRelativeTime } from '../utils/format'

export const AlertDetail = () => {
  const { alertId } = useParams()
  const { data: alert, isLoading } = useAlert(alertId)
  const { data: trace } = useTrace(alertId)
  const { data: readings } = useMachineReadings(alert?.machine_id, 50)
  const [tab, setTab] = useState('what')
  const [comment, setComment] = useState('')
  const [decidedBy, setDecidedBy] = useState('Demo User')
  const approveMut = useApprove()
  const rejectMut = useReject()

  if (isLoading) return <div className='text-xs'>Loading alert {alertId}...</div>
  if (!alert) return <div className='text-sm'>Alert not found: {alertId}</div>

  const storySteps = [
    { key: 'detected', label: 'Detected', done: true },
    { key: 'diagnosed', label: 'Diagnosed', done: !!alert.diagnosis },
    { key: 'planned', label: 'Plan ready', done: !!alert.plan },
    { key: 'approval', label: 'Approval', done: alert.status==='ticketed' || alert.status==='resolved', current: alert.status==='awaiting_approval' },
    { key: 'ticket', label: 'Repair instructions & Ticket', done: alert.status==='ticketed' },
  ]

  const handleApprove = () => {
    approveMut.mutate({ alertId, body: { decided_by: decidedBy, comment } }, {
      onSuccess: (res) => toast.success(`Approved ${alertId}. Ticket ${res.ticket?.ticket_id} in progress.`, { href: `/tickets/${res.ticket?.ticket_id}`, label: 'View ticket' })
    })
  }
  const handleReject = () => {
    rejectMut.mutate({ alertId, body: { decided_by: decidedBy, comment } }, {
      onSuccess: () => toast.success(`Rejected ${alertId}. Monitoring continues.`)
    })
  }

  return (
    <div className='space-y-4'>
      <PageHeader title={`Alert ${alertId}`} purpose={`Full story of one incident on ${alert.machine_id}: what happened, why, what AI plans, and repair instructions.`} bullets={['Story stepper shows progress Detected → Diagnosis → Plan → Approval → Ticket','Tabs separate concerns: What happened, Agent Trace, Diagnosis, Plan, Repair, Ticket','Every step clickable and explained','If approval pending, sticky bottom bar with outcome preview']} />

      <Card className='p-4'>
        <div className='flex items-start justify-between gap-3'>
          <div>
            <div className='flex items-center gap-2'><SeverityBadge severity={alert.severity} /><span className='font-mono text-xs'>{alert.machine_id} • {alert.alert_type}</span><span className='text-xs font-mono'>Conf {(alert.confidence*100).toFixed(0)}% • Anomaly {alert.anomaly_score?.toFixed(2)}</span></div>
            <div className='text-sm mt-2'>{alert.description || alert.diagnosis?.root_cause || 'Incident detected by Factory Brain'}</div>
            <div className='text-xs text-[var(--text-muted)] mt-1'>{formatRelativeTime(alert.ts)} • Status: {alert.status} • ID {alert.alert_id}</div>
          </div>
        </div>
        <div className='mt-3 flex items-center gap-2'>
          {storySteps.map((s,i) => (
            <div key={s.key} className='flex items-center gap-2'>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] border ${s.done ? 'bg-[var(--healthy)] text-white border-[var(--healthy)]' : s.current ? 'bg-[var(--accent)] text-white border-[var(--accent)]' : 'border-[var(--border)] text-[var(--text-muted)]'}`}>{i+1}</div>
              <span className='text-xs'>{s.label}</span>
              {i<storySteps.length-1 && <div className='w-6 h-0.5 bg-[var(--border)]' />}
            </div>
          ))}
        </div>
      </Card>

      <Tabs tabs={[{ key:'what', label:'What happened' }, { key:'trace', label:'Agent Trace' }, { key:'diagnosis', label:'Diagnosis' }, { key:'plan', label:'Plan' }, { key:'repair', label:'Repair Instructions' }, { key:'ticket', label:'Ticket' }]} active={tab} onChange={setTab} />

      {tab==='what' && (
        <div className='space-y-3'>
          <TopSensorsBar sensors={alert.top_sensors} />
          {readings && <SensorChart data={readings} dataKey={alert.top_sensors?.[0]?.name || 'vibration'} label={`Top sensor ${alert.top_sensors?.[0]?.name}`} unit='' />}
        </div>
      )}

      {tab==='trace' && <AgentTimeline events={trace} />}

      {tab==='diagnosis' && (
        <div className='space-y-3'>
          <Card className='p-4'><h4 className='font-medium text-sm'>Root cause</h4><p className='text-sm mt-1'>{alert.diagnosis?.root_cause || 'Investigating...'}</p><div className='text-xs text-[var(--text-muted)] mt-2'>Confidence: {(alert.diagnosis?.confidence*100)?.toFixed(0)}%</div><p className='text-xs mt-2 leading-relaxed'>{alert.diagnosis?.reasoning}</p></Card>
          <CitationList citations={alert.diagnosis?.citations} />
        </div>
      )}

      {tab==='plan' && (
        <div className='space-y-3'>
          <PlanCard plan={alert.plan} />
          <ImpactEstimateCard impact={alert.plan?.estimated_impact} />
        </div>
      )}

      {tab==='repair' && <RepairInstructions instructions={alert.plan?.steps?.join(', ') || 'Follow standard procedure'} />}

      {tab==='ticket' && (
        <div className='space-y-3'>
          <Card className='p-4'><div className='text-sm'>Ticket linked to this alert will appear here. When approved, ticket moves to In Progress and technician notified.</div></Card>
        </div>
      )}

      {alert.status==='awaiting_approval' && (
        <div className='sticky bottom-0 bg-[var(--surface)] border-t border-[var(--border)] p-3 flex items-center gap-3'>
          <input placeholder='Your name' value={decidedBy} onChange={e=>setDecidedBy(e.target.value)} className='px-2 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)]' />
          <input placeholder='Comment' value={comment} onChange={e=>setComment(e.target.value)} className='flex-1 px-2 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)]' />
          <OutcomeButton label='Approve' variant='primary' outcomes={outcomes.approve.preview} onConfirm={handleApprove} />
          <OutcomeButton label='Reject' variant='outline' outcomes={outcomes.reject.preview} onConfirm={handleReject} />
        </div>
      )}
    </div>
  )
}
