import { Link } from 'react-router-dom'
import { Card } from '../common/Card'
import { Badge } from '../common/Badge'
import { formatRelativeTime } from '../../utils/format'

export const TicketCard = ({ ticket }) => {
  return (
    <Link to={`/tickets/${ticket.ticket_id}`}>
      <Card hover className='p-3'>
        <div className='flex items-start justify-between gap-2'>
          <div>
            <span className='font-mono text-sm font-semibold'>{ticket.ticket_id}</span>
            <span className='ml-2 text-xs text-[var(--text-muted)]'>{ticket.machine_id}</span>
            <Badge variant={ticket.priority==='high' ? 'critical' : ticket.priority==='medium' ? 'warning' : 'steel'} className='ml-2'>{ticket.priority}</Badge>
          </div>
          <Badge variant='steel'>{ticket.status}</Badge>
        </div>
        <div className='text-sm mt-1'>{ticket.title}</div>
        <div className='text-xs text-[var(--text-muted)] mt-1'>{ticket.description?.slice(0,100)}</div>
        <div className='text-[10px] font-mono text-[var(--text-muted)] mt-1'>{formatRelativeTime(ticket.created_at)}</div>
      </Card>
    </Link>
  )
}
