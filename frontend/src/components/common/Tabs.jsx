import clsx from 'clsx'

export const Tabs = ({ tabs, active, onChange }) => {
  return (
    <div className='flex gap-1 border-b border-[var(--border)]'>
      {tabs.map(t => (
        <button
          key={t.key}
          onClick={() => onChange(t.key)}
          className={clsx(
            'px-4 py-2 text-sm font-medium border-b-2 -mb-[1px] transition-colors min-h-[44px]',
            active === t.key ? 'border-[var(--accent)] text-[var(--accent)]' : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-primary)]'
          )}
        >
          {t.label}
          {t.count != null && <span className='ml-2 px-1.5 py-0.5 text-xs rounded bg-[var(--border)]'>{t.count}</span>}
        </button>
      ))}
    </div>
  )
}
