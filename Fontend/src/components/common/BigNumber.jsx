import { InfoTip } from './InfoTip'

export const BigNumber = ({ label, value, unit, info, delta }) => {
  return (
    <div className='card p-4'>
      <div className='flex items-center gap-2 mb-1'>
        <span className='text-xs text-[var(--text-muted)] uppercase tracking-wide'>{label}</span>
        {info && <InfoTip title={info.title} content={info.content} />}
      </div>
      <div className='flex items-baseline gap-2'>
        <span className='big-number font-mono text-3xl md:text-4xl font-semibold tabular text-[var(--text-primary)]'>{value}</span>
        {unit && <span className='text-sm text-[var(--text-muted)]'>{unit}</span>}
      </div>
      {delta && <div className='text-xs text-[var(--text-muted)] mt-1'>{delta}</div>}
    </div>
  )
}
