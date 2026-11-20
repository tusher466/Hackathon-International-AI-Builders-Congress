import { useState } from 'react'
import { Card } from '../common/Card'

export const AnomalyExplainer = ({ alert, diagnosis }) => {
  const [showRaw, setShowRaw] = useState(false)
  if (!alert) return null
  const plain = diagnosis?.reasoning || `Vibration on ${alert.top_sensors?.[0]?.name || 'primary sensor'} has risen ${alert.top_sensors?.[0]?.deviation || '?'} sigma above normal over last 30 readings. This usually means wear or drift that needs attention.`
  return (
    <Card className='p-4'>
      <h4 className='text-sm font-semibold mb-2'>Why is this happening? (Plain language)</h4>
      <p className='text-sm text-[var(--text-primary)] leading-relaxed'>{plain}</p>
      <button onClick={() => setShowRaw(!showRaw)} className='mt-2 text-xs text-[var(--accent)] underline'>{showRaw ? 'Hide raw numbers' : 'Show the raw numbers'}</button>
      {showRaw && (
        <div className='mt-3 p-2 rounded bg-[var(--bg)] border border-[var(--border)] font-mono text-xs'>
          {alert.top_sensors?.map(s => (
            <div key={s.name}>{s.name}: deviation {s.deviation} ({s.direction})</div>
          ))}
          <div className='mt-1'>Anomaly score: {alert.anomaly_score} • Confidence: {alert.confidence}</div>
        </div>
      )}
    </Card>
  )
}
