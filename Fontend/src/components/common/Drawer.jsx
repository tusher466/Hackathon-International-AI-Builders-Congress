import { X } from 'lucide-react'

export const Drawer = ({ open, onClose, title, children, width='w-96' }) => {
  if (!open) return null
  return (
    <div className='fixed inset-0 z-50 flex justify-end'>
      <div className='flex-1 bg-black/40' onClick={onClose} />
      <div className={`${width} max-w-[90vw] bg-[var(--surface)] border-l border-[var(--border)] h-full overflow-auto`}>
        <div className='flex items-center justify-between p-4 border-b border-[var(--border)] sticky top-0 bg-[var(--surface)]'>
          <h3 className='font-semibold'>{title}</h3>
          <button onClick={onClose} className='p-2 rounded hover:bg-[var(--surface-hover)]'><X size={18} /></button>
        </div>
        <div className='p-4'>{children}</div>
      </div>
    </div>
  )
}
