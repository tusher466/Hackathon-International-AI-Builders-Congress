import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceArea } from 'recharts'
import { Card } from '../common/Card'

export const SensorChart = ({ data, dataKey, label, unit, anomalies=[] }) => {
  if (!data || data.length===0) return <Card className='p-4'><div className='text-xs text-[var(--text-muted)]'>No data for {label}</div></Card>
  const chartData = data.map(d => ({
    ts: new Date(d.ts).toLocaleTimeString(),
    value: d.sensors?.[dataKey] ?? d.sensors?.vibration ?? 0,
    rawTs: d.ts
  }))

  return (
    <Card className='p-4'>
      <div className='flex items-center justify-between mb-2'>
        <h4 className='text-sm font-medium'>{label} <span className='font-mono text-xs text-[var(--text-muted)]'>({dataKey})</span></h4>
        <span className='font-mono text-xs tabular'>{chartData[chartData.length-1]?.value?.toFixed(2)} {unit}</span>
      </div>
      <div className='h-40'>
        <ResponsiveContainer width='100%' height='100%'>
          <LineChart data={chartData}>
            <XAxis dataKey='ts' tick={{ fontSize: 10, fill: 'var(--text-muted)' }} interval='preserveStartEnd' />
            <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} width={40} />
            <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border)', fontSize: '12px', fontFamily: 'JetBrains Mono' }} />
            {anomalies.map((a,i) => (
              <ReferenceArea key={i} x1={a.start} x2={a.end} fill='var(--critical)' fillOpacity={0.1} stroke='var(--critical)' strokeOpacity={0.3} />
            ))}
            <Line type='monotone' dataKey='value' stroke='var(--steel)' strokeWidth={1.5} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
