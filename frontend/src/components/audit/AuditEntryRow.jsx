import { useState } from 'react'
import { formatRelativeTime, formatAbsoluteTime } from '../../utils/format'
import { Link } from 'react-router-dom'

export const AuditEntryRow = ({ entry }) => {
  const [expanded, setExpanded] = useState(false)
  return (
    <>
      <tr className='border-b border-[var(--border)] hover:bg-[var(--surface-hover)] cursor-pointer' onClick={() => setExpanded(!expanded)}>
        <td className='p-2 font-mono' title={formatAbsoluteTime(entry.ts)}>{formatRelativeTime(entry.ts)}</td>
        <td className='p-2'><span className={`px-1.5 py-0.5 rounded text-[10px] ${entry.actor_type==='ai' ? 'bg-[var(--accent)]/15 text-[var(--accent)]' : 'bg-[var(--border)]'}`}>{entry.actor_type==='ai' ? 'AI' : 'Human'} {entry.actor}</span></td>
        <td className='p-2'>{entry.event_type}</td>
        <td className='p-2 font-mono'>{entry.machine_id || '—'}</td>
        <td className='p-2 max-w-xs truncate'>{entry.summary}</td>
        <td className='p-2'>
          {entry.alert_id && <Link to={`/alerts/${entry.alert_id}`} onClick={e=>e.stopPropagation()} className='text-[var(--accent)] underline mr-1'>{entry.alert_id}</Link>}
          {entry.ticket_id && <Link to={`/tickets/${entry.ticket_id}`} onClick={e=>e.stopPropagation()} className='text-[var(--accent)] underline'>{entry.ticket_id}</Link>}
        </td>
      </tr>
      {expanded && (
        <tr><td colSpan={6} className='p-3 bg-[var(--bg)] text-xs'><pre className='whitespace-pre-wrap font-mono text-[11px]'>{JSON.stringify(entry.details, null, 2)}</pre></td></tr>
      )}
    </>
  )
}
