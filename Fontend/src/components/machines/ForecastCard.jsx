import { Card } from '../common/Card'
import { InfoTip } from '../common/InfoTip'

export const ForecastCard = ({ machine, alert }) => {
  let title = 'Failure Forecast'
  let mainValue = '—'
  let confidence = null
  let explanation = ''
  if (machine?.machine_type === 'turbofan' || alert?.predicted_rul) {
    title = 'Remaining Useful Life (RUL)'
    mainValue = alert?.predicted_rul ? `${alert.predicted_rul} hours` : 'Unknown'
    confidence = alert ? alert.confidence*100 : 60
    explanation = `Prediction of how many hours this ${machine?.machine_id || 'machine'} has left before likely failure. Calculated from degradation trend regression. Higher hours means more time to act.`
  } else if (machine?.machine_type === 'bosch' || alert?.defect_probability) {
    title = 'Defect Probability'
    mainValue = alert?.defect_probability ? `${(alert.defect_probability*100).toFixed(1)}%` : '—'
    confidence = alert ? alert.confidence*100 : 50
    explanation = 'Chance that next units will be defective based on current tool wear and process drift. Based on historical defect rates vs sensor deviation.'
  } else {
    title = 'Anomaly Trend'
    mainValue = alert ? `Score ${alert.anomaly_score?.toFixed(2)} trending up` : 'Monitoring'
    confidence = alert ? alert.confidence*100 : 40
    explanation = 'Anomaly score shows how unusual current behavior is vs normal. Rising trend suggests developing issue.'
  }

  const confLabel = confidence >=80 ? 'High' : confidence >=50 ? 'Medium' : 'Low'
  const confColor = confidence >=80 ? 'var(--healthy)' : confidence >=50 ? 'var(--warning)' : 'var(--critical)'

  return (
    <Card className='p-4'>
      <div className='flex items-center gap-2 mb-2'>
        <h4 className='text-sm font-semibold'>{title}</h4>
        <InfoTip title={title} content={explanation} />
      </div>
      <div className='font-mono text-2xl font-bold tabular'>{mainValue}</div>
      {confidence != null && (
        <div className='mt-3'>
          <div className='flex items-center justify-between text-xs mb-1'>
            <span className='text-[var(--text-muted)]'>Confidence</span>
            <span className='font-mono tabular'>{confidence?.toFixed(0)}% • {confLabel}</span>
          </div>
          <div className='h-2 bg-[var(--border)] rounded-full overflow-hidden'>
            <div className='h-full' style={{ width: `${confidence}%`, background: confColor }} />
          </div>
          <div className='text-xs text-[var(--text-muted)] mt-1'>What this means: {confLabel==='High' ? 'Strong evidence, reliable prediction' : confLabel==='Medium' ? 'Moderate evidence, monitor closely' : 'Weak evidence, needs human review'}</div>
        </div>
      )}
    </Card>
  )
}
