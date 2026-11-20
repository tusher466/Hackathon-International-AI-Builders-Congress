import { useState, useRef, useEffect } from 'react'
import clsx from 'clsx'

export const OutcomeButton = ({ label, variant='primary', outcomes=[], onConfirm, confirmRequired=true, disabled, className }) => {
  const [showConfirm, setShowConfirm] = useState(false)
  const [showPopover, setShowPopover] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) {
        setShowPopover(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleClick = () => {
    if (confirmRequired) {
      setShowConfirm(true)
    } else {
      onConfirm?.()
    }
  }

  const base = 'inline-flex items-center justify-center px-4 py-2 rounded-[8px] text-sm font-medium min-h-[44px] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]'
  const variants = {
    primary: 'bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] disabled:opacity-50',
    outline: 'border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] hover:bg-[var(--surface-hover)] hover:border-[var(--border-hover)]',
    danger: 'bg-[var(--critical)] text-white hover:opacity-90',
  }

  return (
    <span className='relative inline-flex' ref={ref}>
      <button
        className={clsx(base, variants[variant], className)}
        onClick={handleClick}
        disabled={disabled}
        onMouseEnter={() => setShowPopover(true)}
        onMouseLeave={() => setShowPopover(false)}
        onFocus={() => setShowPopover(true)}
        onBlur={() => setShowPopover(false)}
        aria-label={`${label} - shows outcome preview on hover`}
      >
        {label}
      </button>
      {showPopover && outcomes?.length > 0 && !showConfirm && (
        <div className='absolute bottom-full left-0 mb-2 w-80 p-3 rounded-[8px] bg-[var(--surface)] border border-[var(--border)] text-xs z-40 tooltip-enter'>
          <div className='font-semibold text-[var(--text-primary)] mb-1.5'>If you click this:</div>
          <ol className='list-decimal ml-4 space-y-1 text-[var(--text-muted)]'>
            {outcomes.map((o,i) => <li key={i}>{o}</li>)}
          </ol>
        </div>
      )}
      {showConfirm && (
        <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4'>
          <div className='card max-w-md w-full p-5'>
            <h3 className='font-semibold text-[var(--text-primary)] mb-2'>Confirm: {label}</h3>
            <div className='text-sm text-[var(--text-muted)] mb-4'>
              <div className='font-medium text-[var(--text-primary)] mb-1'>This will:</div>
              <ol className='list-decimal ml-5 space-y-1'>
                {outcomes.map((o,i) => <li key={i}>{o}</li>)}
              </ol>
            </div>
            <div className='flex gap-2 justify-end'>
              <button className={clsx(base, variants.outline)} onClick={() => setShowConfirm(false)}>Cancel</button>
              <button className={clsx(base, variants[variant])} onClick={() => { setShowConfirm(false); onConfirm?.() }}>{label}</button>
            </div>
          </div>
        </div>
      )}
    </span>
  )
}
