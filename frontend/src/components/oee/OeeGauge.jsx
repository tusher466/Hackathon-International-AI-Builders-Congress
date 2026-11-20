import { InfoTip } from '../common/InfoTip'
import { infoTips } from '../../utils/outcomes'

export const OeeGauge = ({ label, value, infoKey }) => {
  const pct = (value <= 1 ? value*100 : value)
  const info = infoTips[infoKey] || { title: label, content: '' }
  const getColor = () => {
    if (pct >= 85) return 'var(--healthy)'
    if (pct >= 60) return 'var(--warning)'
    return 'var(--critical)'
  }
  return (
    <div className='card p-4 flex flex-col gap-2'>
      <div className='flex items-center gap-2'>
        <span className='text-xs uppercase tracking-wide text-[var(--text-muted)]'>{label}</span>
        <InfoTip title={info.title} content={info.content} />
      </div>
      <div className='flex items-end gap-2'>
        <span className='font-mono text-3xl font-semibold tabular'>{pct.toFixed(1)}%</span>
        <div className='flex-1 h-2 bg-[var(--border)] rounded-full overflow-hidden mb-2'>
          <div className='h-full' style={{ width: `${Math.min(100, pct)}%`, background: getColor() }} />
        </div>
      </div>
      <div className='text-xs text-[var(--text-muted)]'>
        {pct >= 85 ? 'World-class' : pct >= 60 ? 'Typical' : 'Needs improvement'}
      </div>
    </div>
  )
}
