import { useEffect, useState } from 'react'
import { X, CheckCircle, AlertCircle } from 'lucide-react'
import { Link } from 'react-router-dom'

let toastListeners = []
let toasts = []

function notifyListeners() {
  toastListeners.forEach(l => l([...toasts]))
}

export const toast = {
  success: (message, link) => {
    const id = Date.now()
    toasts.push({ id, message, link, type: 'success' })
    notifyListeners()
    setTimeout(() => toast.dismiss(id), 5000)
  },
  error: (message) => {
    const id = Date.now()
    toasts.push({ id, message, type: 'error' })
    notifyListeners()
    setTimeout(() => toast.dismiss(id), 5000)
  },
  info: (message, link) => {
    const id = Date.now()
    toasts.push({ id, message, link, type: 'info' })
    notifyListeners()
    setTimeout(() => toast.dismiss(id), 4000)
  },
  dismiss: (id) => {
    toasts = toasts.filter(t => t.id !== id)
    notifyListeners()
  }
}

export const ToastContainer = () => {
  const [list, setList] = useState([])

  useEffect(() => {
    const cb = (items) => setList(items)
    toastListeners.push(cb)
    return () => { toastListeners = toastListeners.filter(l => l !== cb) }
  }, [])

  return (
    <div className='fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm'>
      {list.map(t => (
        <div key={t.id} className='card p-3 flex items-start gap-2 border-l-4' style={{ borderLeftColor: t.type==='success' ? 'var(--healthy)' : t.type==='error' ? 'var(--critical)' : 'var(--accent)' }}>
          {t.type==='success' ? <CheckCircle size={18} className='text-[var(--healthy)] mt-0.5' /> : <AlertCircle size={18} className='text-[var(--text-muted)] mt-0.5' />}
          <div className='flex-1'>
            <div className='text-sm text-[var(--text-primary)]'>{t.message}</div>
            {t.link && <Link to={t.link.href} className='text-xs text-[var(--accent)] underline'>{t.link.label}</Link>}
          </div>
          <button onClick={() => toast.dismiss(t.id)} className='text-[var(--text-muted)] hover:text-[var(--text-primary)]'><X size={14} /></button>
        </div>
      ))}
    </div>
  )
}
