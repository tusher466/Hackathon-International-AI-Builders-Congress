import { useState } from 'react'
import { OeeGauge } from './OeeGauge'
import { InfoTip } from '../common/InfoTip'
import { infoTips } from '../../utils/outcomes'
import { formatPercent } from '../../utils/format'

export const OeeSummary = ({ data, isDemo }) => {
  const [expanded, setExpanded] = useState(false)
  if (!data) return null
  return (
    <div className='space-y-3'>
      <div className='card p-4 border-l-4' style={{ borderLeftColor: 'var(--accent)' }}>
        <div className='flex items-center gap-2 mb-2'>
          <h3 className='font-semibold'>OEE (Overall Equipment Effectiveness)</h3>
          <InfoTip title={infoTips.oee.title} content={infoTips.oee.content} />
          {isDemo && <span className='text-[10px] px-1.5 py-0.5 rounded bg-[var(--border)] font-mono'>Demo data</span>}
        </div>
        <div className='flex items-baseline gap-3'>
          <span className='font-mono text-4xl font-bold tabular'>{formatPercent(data.oee)}</span>
          <span className='text-sm text-[var(--text-muted)]'>= Availability {formatPercent(data.availability)} × Performance {formatPercent(data.performance)} × Quality {formatPercent(data.quality)}</span>
        </div>
        <div className='mt-3 grid grid-cols-1 md:grid-cols-3 gap-3'>
          <OeeGauge label='Availability' value={data.availability} infoKey='oeeAvailability' />
          <OeeGauge label='Performance' value={data.performance} infoKey='oeePerformance' />
          <OeeGauge label='Quality' value={data.quality} infoKey='oeeQuality' />
        </div>
        <button onClick={() => setExpanded(!expanded)} className='mt-3 text-xs text-[var(--accent)] underline'>{expanded ? 'Hide per-line breakdown' : 'Show per-line breakdown'}</button>
        {expanded && (
          <div className='mt-3 overflow-auto'>
            <table className='w-full text-xs'>
              <thead><tr className='text-[var(--text-muted)] text-left'><th className='p-2'>Line</th><th>Availability</th><th>Performance</th><th>Quality</th><th>OEE</th></tr></thead>
              <tbody>
                {data.per_line?.map(l => (
                  <tr key={l.line_id} className='border-t border-[var(--border)]'><td className='p-2 font-mono'>{l.line_id}</td><td>{formatPercent(l.availability)}</td><td>{formatPercent(l.performance)}</td><td>{formatPercent(l.quality)}</td><td className='font-semibold'>{formatPercent(l.oee)}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
