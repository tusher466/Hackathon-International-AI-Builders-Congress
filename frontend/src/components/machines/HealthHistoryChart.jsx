import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { Card } from '../common/Card'

export const HealthHistoryChart = ({ data }) => {
  const chartData = data?.map((d,i) => ({
    time: new Date(d.ts).toLocaleTimeString(),
    health: 80 - Math.sin(i/10)*10 + Math.random()*5,
  })) || Array.from({length: 30}).map((_,i) => ({ time: `${i}`, health: 70 + Math.random()*20 }))

  return (
    <Card className='p-4'>
      <h4 className='text-sm font-medium mb-2'>Health History (last readings)</h4>
      <div className='h-40'>
        <ResponsiveContainer width='100%' height='100%'>
          <AreaChart data={chartData}>
            <XAxis dataKey='time' tick={{fontSize:10, fill:'var(--text-muted)'}} />
            <YAxis domain={[0,100]} tick={{fontSize:10}} />
            <Tooltip contentStyle={{ background:'var(--surface)', border:'1px solid var(--border)'}} />
            <Area dataKey='health' stroke='var(--healthy)' fill='var(--healthy)' fillOpacity={0.1} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
