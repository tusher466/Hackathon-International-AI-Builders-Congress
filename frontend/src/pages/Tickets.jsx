import { useState } from 'react'
import { PageHeader } from '../layout/PageHeader'
import { useTickets } from '../hooks/useTickets'
import { TicketCard } from '../components/tickets/TicketCard'
import { EmptyState } from '../components/common/EmptyState'

export const Tickets = () => {
  const [filter, setFilter] = useState('')
  const [view, setView] = useState('list')
  const { data: tickets, isLoading } = useTickets({ ...(filter?{status:filter}:{}) })

  const grouped = tickets ? { open: tickets.filter(t=>t.status==='open'), awaiting_approval: tickets.filter(t=>t.status==='awaiting_approval'), in_progress: tickets.filter(t=>t.status==='in_progress'), resolved: tickets.filter(t=>t.status==='resolved'), rejected: tickets.filter(t=>t.status==='rejected') } : {}

  return (
    <div className='space-y-4'>
      <PageHeader title='Tickets - Repair Jobs' purpose='Repair jobs created from alerts. Track status Open → Awaiting approval → In progress → Resolved. Each ticket links to full alert story.' bullets={['Status filter and kanban toggle','Needs human review means AI not confident enough','Click ticket to see repair instructions, safety warnings, timestamps']} />

      <div className='flex gap-2 items-center text-xs'>
        <select value={filter} onChange={e=>setFilter(e.target.value)} className='px-2 py-2 rounded border border-[var(--border)] bg-[var(--bg)]'>
          <option value=''>All status</option>
          <option value='open'>Open</option>
          <option value='awaiting_approval'>Awaiting approval</option>
          <option value='in_progress'>In progress</option>
          <option value='resolved'>Resolved</option>
        </select>
        <button onClick={() => setView(v=>v==='list'?'kanban':'list')} className='px-3 py-2 rounded border border-[var(--border)]'>{view==='list'?'Kanban view':'List view'}</button>
      </div>

      {isLoading ? <div className='text-xs'>Loading tickets...</div> : tickets?.length===0 ? <EmptyState title='No tickets' description='Tickets are created when alerts are diagnosed. Inject a fault in Simulator to see full chain create a ticket.' /> : view==='list' ? (
        <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3'>
          {tickets.map(t => <TicketCard key={t.ticket_id} ticket={t} />)}
        </div>
      ) : (
        <div className='grid grid-cols-1 md:grid-cols-4 gap-3'>
          {Object.entries(grouped).map(([status, list]) => (
            <div key={status} className='space-y-2'>
              <h4 className='text-xs font-semibold uppercase'>{status} ({list.length})</h4>
              {list.map(t => <TicketCard key={t.ticket_id} ticket={t} />)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
