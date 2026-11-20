import { Card } from '../common/Card'
import { CopyButton } from '../common/CopyButton'

export const RepairInstructions = ({ instructions }) => {
  if (!instructions) return null
  const steps = instructions.split(',').map(s=>s.trim()).filter(Boolean)
  // fallback if single string
  const list = steps.length>1 ? steps : instructions.split('\n').filter(Boolean)
  return (
    <Card className='p-4'>
      <div className='flex items-center justify-between mb-2'>
        <h4 className='font-medium text-sm'>Repair Instructions</h4>
        <CopyButton text={instructions} label='Copy steps' />
      </div>
      <div className='mb-3 p-2 rounded bg-[var(--critical)]/10 border border-[var(--critical)]/30 text-xs'>
        <strong>Safety:</strong> Follow lockout/tagout (LOTO) procedures before touching machine. Wear PPE. This is a critical warning - ensure machine is de-energized.
      </div>
      <ol className='list-decimal ml-5 space-y-2 text-sm'>
        {list.map((step,i) => (
          <li key={i} className='leading-relaxed'>
            {step}
            <div className='text-xs text-[var(--text-muted)]'>Expected result: Step {i+1} completes, proceed to next. If not, check logs and alert.</div>
          </li>
        ))}
      </ol>
      <div className='mt-3 flex gap-2'>
        <button onClick={() => window.print()} className='px-3 py-1 text-xs border border-[var(--border)] rounded'>Print</button>
      </div>
    </Card>
  )
}
