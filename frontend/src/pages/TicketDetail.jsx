import { useParams, Link } from 'react-router-dom'
import { useTicket } from '../hooks/useTickets'
import { PageHeader } from '../layout/PageHeader'
import { Card } from '../components/common/Card'
import { TicketStatusStepper } from '../components/tickets/TicketStatusStepper'
import { RepairInstructions } from '../components/tickets/RepairInstructions'
import { InfoTip } from '../components/common/InfoTip'

export const TicketDetail = () => {
  const { ticketId } = useParams()
  const { data: ticket, isLoading } = useTicket(ticketId)

  if (isLoading) return <div className='text-xs'>Loading ticket {ticketId}...</div>
  if (!ticket) return <div className='text-sm'>Ticket not found</div>

  return (
    <div className='space-y-4'>
      <PageHeader title={`Ticket ${ticket.ticket_id}`} purpose={`Repair job for ${ticket.machine_id}. Shows status, description, repair instructions, and link to alert story.`} bullets={['Status stepper shows Open → Awaiting approval → In Progress → Resolved','Repair instructions have tools, safety warnings, expected result per step','Link to alert story for full diagnosis']} />

      <Card className='p-4'>
        <div className='flex items-center justify-between gap-2'>
          <div><span className='font-mono font-bold'>{ticket.ticket_id}</span><span className='ml-2 text-xs'>{ticket.title}</span></div>
          <span className='text-xs px-2 py-1 rounded bg-[var(--border)]'>{ticket.status}</span>
        </div>
        <div className='mt-3'><TicketStatusStepper status={ticket.status} /></div>
        <div className='mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs'>
          <div><span className='text-[var(--text-muted)]'>Machine:</span> <Link to={`/machines/${ticket.machine_id}`} className='text-[var(--accent)] underline font-mono'>{ticket.machine_id}</Link></div>
          <div><span className='text-[var(--text-muted)]'>Alert:</span> <Link to={`/alerts/${ticket.alert_id}`} className='text-[var(--accent)] underline'>{ticket.alert_id}</Link></div>
          <div><span className='text-[var(--text-muted)]'>Priority:</span> {ticket.priority}</div>
          <div><span className='text-[var(--text-muted)]'>Created:</span> {new Date(ticket.created_at).toLocaleString()}</div>
        </div>
        <div className='mt-3 text-sm'>{ticket.description}</div>
      </Card>

      <RepairInstructions instructions={ticket.instructions} />

      <Card className='p-4'>
        <h4 className='text-sm font-medium mb-2'>Status meanings <InfoTip title='Ticket status' content='open = created not started, awaiting_approval = AI proposed waiting for human, in_progress = technician working, resolved = fix verified, rejected = human rejected, needs_human_review = AI not confident enough' /></h4>
        <div className='text-xs text-[var(--text-muted)]'>Current status: {ticket.status}. {ticket.status==='needs_human_review' ? 'The AI was not confident enough, a person must check.' : ticket.status==='awaiting_approval' ? 'AI wants to act but needs human approval.' : ''}</div>
        {ticket.alert && (
          <div className='mt-2 text-xs'>Go to alert story: <Link to={`/alerts/${ticket.alert_id}`} className='text-[var(--accent)] underline'>View alert {ticket.alert_id} detail with diagnosis, citations, plan</Link></div>
        )}
      </Card>
    </div>
  )
}
