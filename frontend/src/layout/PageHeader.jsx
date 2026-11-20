import { useState } from 'react'
import { ChevronDown, ChevronUp, Info } from 'lucide-react'

export const PageHeader = ({ title, purpose, bullets }) => {
  const [open, setOpen] = useState(false)
  return (
    <div className='mb-6'>
      <h1 className='text-2xl font-bold text-[var(--text-primary)]'>{title}</h1>
      <p className='text-sm text-[var(--text-muted)] mt-1'>{purpose}</p>
      <button onClick={() => setOpen(!open)} className='mt-2 inline-flex items-center gap-1 text-xs text-[var(--accent)] hover:underline'>
        <Info size={12} />
        What can I do here?
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>
      {open && (
        <div className='mt-2 p-3 rounded-[8px] bg-[var(--surface)] border border-[var(--border)]'>
          <ul className='list-disc ml-5 space-y-1 text-xs text-[var(--text-muted)]'>
            {bullets?.map((b,i) => <li key={i}>{b}</li>)}
          </ul>
        </div>
      )}
    </div>
  )
}
