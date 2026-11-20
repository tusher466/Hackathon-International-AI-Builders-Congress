const statuses = ['open','awaiting_approval','in_progress','resolved']

export const TicketStatusStepper = ({ status }) => {
  const idx = statuses.indexOf(status)
  return (
    <div className='flex items-center gap-2'>
      {statuses.map((s,i) => (
        <div key={s} className='flex items-center gap-2'>
          <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border ${i<=idx ? 'bg-[var(--accent)] text-white border-[var(--accent)]' : 'border-[var(--border)] text-[var(--text-muted)]'}`}>{i+1}</div>
          <span className={`text-xs ${i===idx ? 'font-semibold text-[var(--text-primary)]' : 'text-[var(--text-muted)]'}`}>{s}</span>
          {i<statuses.length-1 && <div className={`w-8 h-0.5 ${i<idx ? 'bg-[var(--accent)]' : 'bg-[var(--border)]'}`} />}
        </div>
      ))}
    </div>
  )
}
