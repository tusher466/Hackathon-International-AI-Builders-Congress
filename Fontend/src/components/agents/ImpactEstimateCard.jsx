import { Card } from '../common/Card'
import { InfoTip } from '../common/InfoTip'
import { infoTips } from '../../utils/outcomes'

export const ImpactEstimateCard = ({ impact }) => {
  if (!impact) return null
  return (
    <Card className='p-4'>
      <div className='flex items-center gap-2 mb-2'>
        <h4 className='text-sm font-medium'>Estimates (predicted benefit if you act)</h4>
        <InfoTip title={infoTips.impact.title} content={infoTips.impact.content} />
      </div>
      <div className='grid grid-cols-3 gap-3'>
        <div>
          <div className='font-mono text-xl font-bold tabular'>{impact.downtime_avoided_minutes || impact.downtime_avoided || 0}</div>
          <div className='text-xs text-[var(--text-muted)]'>minutes downtime avoided</div>
        </div>
        <div>
          <div className='font-mono text-xl font-bold tabular'>{impact.defects_prevented || 0}</div>
          <div className='text-xs text-[var(--text-muted)]'>defects prevented</div>
        </div>
        <div>
          <div className='font-mono text-xl font-bold tabular'>{impact.energy_saved_kwh || impact.energy_saved || 0}</div>
          <div className='text-xs text-[var(--text-muted)]'>kWh energy saved</div>
        </div>
      </div>
      <p className='text-[10px] text-[var(--text-muted)] mt-2'>These are estimates based on similar past incidents. Not guarantees.</p>
    </Card>
  )
}
