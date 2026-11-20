export const HealthGauge = ({ value, size=80 }) => {
  const pct = Math.max(0, Math.min(100, value || 0))
  const r = size/2 - 6
  const circ = 2 * Math.PI * r
  const offset = circ - (pct/100)*circ
  let color = 'var(--healthy)'
  if (pct < 50) color = 'var(--critical)'
  else if (pct < 80) color = 'var(--warning)'

  return (
    <div className='relative' style={{ width: size, height: size }}>
      <svg width={size} height={size} className='-rotate-90'>
        <circle cx={size/2} cy={size/2} r={r} stroke='var(--border)' strokeWidth='4' fill='none' />
        <circle cx={size/2} cy={size/2} r={r} stroke={color} strokeWidth='4' fill='none' strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap='round' style={{ transition: 'stroke-dashoffset 0.5s ease' }} />
      </svg>
      <div className='absolute inset-0 flex items-center justify-center font-mono text-xs font-bold'>{pct}</div>
    </div>
  )
}
