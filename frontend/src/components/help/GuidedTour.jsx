import { useState, useEffect } from 'react'

const steps = [
  { id:1, target: 'overview', title: 'Welcome to Factory Brain', text: 'This is your live factory overview. Factory Brain watches machines, detects problems, and proposes fixes with evidence.' },
  { id:2, target: 'oee', title: 'OEE shows efficiency', text: 'OEE = Availability × Performance × Quality. World-class is 85%+. Click info icons to learn formulas.' },
  { id:3, target: 'bottleneck', title: 'Bottleneck is your biggest opportunity', text: 'Orange left border highlights the station limiting throughput. Fix this for biggest gain.' },
  { id:4, target: 'machines', title: 'Machine health scores', text: '0-100 score combining anomaly, RUL, defect risk. Click a card to see sensor trends and forecast.' },
  { id:5, target: 'alerts', title: 'Alerts explain what happened', text: 'Each alert has top sensors, diagnosis with citations, and plan. Click to see full story.' },
  { id:6, target: 'actions', title: 'You approve high-risk actions', text: 'Pending work orders require your approval. Approve/reject shows outcome preview. Every decision is logged in Audit Log.' },
]

export const GuidedTour = ({ open, onClose }) => {
  const [idx, setIdx] = useState(0)
  useEffect(() => {
    if (open) setIdx(0)
  }, [open])
  if (!open) return null
  const step = steps[idx]
  return (
    <div className='fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4'>
      <div className='card max-w-md w-full p-5'>
        <div className='text-xs text-[var(--text-muted)] mb-1'>Step {idx+1} of {steps.length}</div>
        <h3 className='font-semibold text-[var(--text-primary)] mb-2'>{step.title}</h3>
        <p className='text-sm text-[var(--text-muted)] mb-4'>{step.text}</p>
        <div className='h-1 bg-[var(--border)] rounded-full overflow-hidden mb-4'>
          <div className='h-full bg-[var(--accent)]' style={{ width: `${((idx+1)/steps.length)*100}%` }} />
        </div>
        <div className='flex justify-between gap-2'>
          <button onClick={onClose} className='px-3 py-1.5 text-xs border border-[var(--border)] rounded'>Skip tour</button>
          <div className='flex gap-2'>
            {idx>0 && <button onClick={() => setIdx(i=>i-1)} className='px-3 py-1.5 text-xs border border-[var(--border)] rounded'>Back</button>}
            {idx<steps.length-1 ? <button onClick={() => setIdx(i=>i+1)} className='px-4 py-1.5 text-xs rounded bg-[var(--accent)] text-white'>Next</button> : <button onClick={() => { localStorage.setItem('factory-brain-tour-done','true'); onClose() }} className='px-4 py-1.5 text-xs rounded bg-[var(--accent)] text-white'>Finish</button>}
          </div>
        </div>
      </div>
    </div>
  )
}
