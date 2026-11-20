import { useState, useRef, useEffect } from 'react'
import { Info } from 'lucide-react'

export const InfoTip = ({ title, content, children }) => {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const displayTitle = title || 'Info'
  const displayContent = content || children

  return (
    <span className='relative inline-flex items-center' ref={ref}>
      <button
        type='button'
        aria-label={`Info: ${displayTitle}`}
        onClick={() => setOpen(!open)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className='inline-flex items-center justify-center w-5 h-5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)]'
      >
        <Info size={12} />
      </button>
      {open && (
        <div className='absolute left-0 top-7 z-50 w-72 p-3 rounded-[8px] bg-[var(--surface)] border border-[var(--border)] shadow-none tooltip-enter'>
          <div className='text-sm font-semibold text-[var(--text-primary)] mb-1'>{displayTitle}</div>
          <div className='text-xs text-[var(--text-muted)] leading-relaxed'>{displayContent}</div>
        </div>
      )}
    </span>
  )
}
