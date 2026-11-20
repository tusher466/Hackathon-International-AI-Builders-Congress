import { useState } from 'react'
import { PageHeader } from '../layout/PageHeader'
import { Tabs } from '../components/common/Tabs'
import { WorkOrderCard } from '../components/agents/WorkOrderCard'
import { AuditTable } from '../components/audit/AuditTable'
import { AuditFilters } from '../components/audit/AuditFilters'
import { useApprovals } from '../hooks/useApprovals'
import { useAuditLog } from '../hooks/useAuditLog'
import { useTickets } from '../hooks/useTickets'
import { EmptyState } from '../components/common/EmptyState'
import { Card } from '../components/common/Card'

export const AgentActions = () => {
  const [tab, setTab] = useState('pending')
  const { data: pending, isLoading: pLoading } = useApprovals()
  const { data: tickets } = useTickets()
  const [filters, setFilters] = useState({})
  const { data: audit } = useAuditLog({ ...filters, limit: '100' })

  const handleExport = () => {
    const rows = audit || []
    const csv = ['id,ts,actor_type,actor,event_type,machine_id,summary', ...rows.map(r => `${r.id},${r.ts},${r.actor_type},${r.actor},${r.event_type},${r.machine_id || ''},"${r.summary.replace(/"/g,'""')}"`)].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'audit_log.csv'
    a.click()
  }

  return (
    <div className='space-y-4'>
      <PageHeader title='Agent Actions' purpose='Work orders waiting for your decision, history of decisions, and audit log of every AI suggestion and human action.' bullets={['Pending tab: high-risk actions like stop machine need approval. Approve/Reject shows outcome preview','History: past work orders with outcome and who decided','Audit log: chronological append-only record, filters, CSV export, expand row for reasoning']} />

      <Tabs tabs={[{ key:'pending', label:'Pending work orders', count: pending?.length }, { key:'history', label:'History', count: tickets?.length }, { key:'audit', label:'Audit log', count: audit?.length }]} active={tab} onChange={setTab} />

      {tab==='pending' && (
        <div className='space-y-3'>
          {pLoading ? <div className='text-xs'>Loading...</div> : pending?.length===0 ? <EmptyState title='Nothing waiting. High-risk actions like stopping a machine will appear here for your decision.' description='When the AI proposes stop_machine or risk is high, work order appears here. You approve or reject with outcome preview. Every decision logged.' /> : (
            <div className='grid grid-cols-1 md:grid-cols-2 gap-3'>
              {pending.map(item => <WorkOrderCard key={item.alert_id} item={item} />)}
            </div>
          )}
        </div>
      )}

      {tab==='history' && (
        <div className='grid grid-cols-1 md:grid-cols-2 gap-3'>
          {tickets?.map(t => (
            <Card key={t.ticket_id} className='p-3'>
              <div className='flex justify-between'><span className='font-mono text-xs'>{t.ticket_id}</span><span className='text-xs'>{t.status}</span></div>
              <div className='text-sm mt-1'>{t.title}</div>
              <div className='text-xs text-[var(--text-muted)]'>{t.machine_id} • {new Date(t.updated_at).toLocaleString()}</div>
            </Card>
          ))}
        </div>
      )}

      {tab==='audit' && (
        <div className='space-y-3'>
          <AuditFilters filters={filters} setFilters={setFilters} onExport={handleExport} />
          <Card className='p-0 overflow-hidden'>
            <AuditTable entries={audit} />
          </Card>
          <div className='text-[10px] text-[var(--text-muted)]'>Audit log is append-only. No edit or delete controls. Every AI suggestion, human approval/rejection, execution, and override is recorded with actor (AI agent name or human name), timestamp, and details.</div>
        </div>
      )}
    </div>
  )
}
