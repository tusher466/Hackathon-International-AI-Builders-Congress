import clsx from 'clsx'

export const ConfirmDialog = ({ open, onClose, onConfirm, title, children, variant='primary' }) => {
  if (!open) return null
  const base = 'inline-flex items-center justify-center px-4 py-2 rounded-[8px] text-sm font-medium min-h-[44px]'
  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4'>
      <div className='card max-w-lg w-full p-5'>
        <h3 className='font-semibold text-[var(--text-primary)] mb-2'>{title}</h3>
        <div className='text-sm text-[var(--text-muted)] mb-4'>{children}</div>
        <div className='flex gap-2 justify-end'>
          <button className={clsx(base, 'border border-[var(--border)]')} onClick={onClose}>Cancel</button>
          <button className={clsx(base, variant==='danger' ? 'bg-[var(--critical)] text-white' : 'bg-[var(--accent)] text-white')} onClick={() => { onClose(); onConfirm(); }}>{title}</button>
        </div>
      </div>
    </div>
  )
}
