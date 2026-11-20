export const KeyValue = ({ label, value, mono=false }) => {
  return (
    <div className='flex flex-col gap-1'>
      <span className='text-xs text-[var(--text-muted)] uppercase tracking-wide'>{label}</span>
      <span className={mono ? 'font-mono text-sm text-[var(--text-primary)]' : 'text-sm text-[var(--text-primary)]'}>{value || '—'}</span>
    </div>
  )
}

export const KeyValueRow = ({ items }) => {
  return (
    <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
      {items.map((it,i) => <KeyValue key={i} {...it} />)}
    </div>
  )
}
