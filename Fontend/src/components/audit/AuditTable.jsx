import { AuditEntryRow } from './AuditEntryRow'

export const AuditTable = ({ entries }) => {
  if (!entries || entries.length===0) {
    return <div className='text-xs text-[var(--text-muted)]'>No audit entries. Every AI suggestion and human decision will appear here chronologically. This log is append-only and cannot be edited or deleted.</div>
  }
  return (
    <div className='overflow-auto'>
      <table className='w-full text-xs'>
        <thead><tr className='text-left text-[var(--text-muted)] border-b border-[var(--border)]'><th className='p-2'>Time</th><th>Actor</th><th>Event</th><th>Machine</th><th>Summary</th><th>Links</th></tr></thead>
        <tbody>
          {entries.map(e => <AuditEntryRow key={e.id} entry={e} />)}
        </tbody>
      </table>
    </div>
  )
}
