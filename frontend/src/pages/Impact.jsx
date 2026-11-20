import { PageHeader } from '../layout/PageHeader'
import { useImpact } from '../hooks/useMetrics'
import { BigNumber } from '../components/common/BigNumber'
import { Card } from '../components/common/Card'
import { InfoTip } from '../components/common/InfoTip'
import { infoTips } from '../utils/outcomes'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

export const Impact = () => {
  const { data: impact } = useImpact()

  const severityData = impact ? Object.entries(impact.alerts_by_severity).map(([k,v]) => ({ name: k, value: v })) : []
  const resolutionData = impact ? [{ name: 'Auto-resolved', value: impact.auto_resolved_count }, { name: 'Human-approved', value: impact.human_approved_count }] : []

  const COLORS = ['var(--offline)','var(--warning)','var(--warning)','var(--critical)']

  return (
    <div className='space-y-4'>
      <PageHeader title='Impact - Downtime, Defects and Energy Saved' purpose='Large numbers showing estimated benefit of early detection. Charts show breakdown by severity and resolution type.' bullets={['Downtime avoided in minutes','Defects prevented count','Energy saved kWh','All values are estimates with InfoTip explaining formula','Alerts by severity bar chart','Auto vs human approved pie']} />

      <div className='grid grid-cols-1 md:grid-cols-3 gap-3'>
        <BigNumber label='Downtime avoided' value={`${impact?.downtime_avoided || 0}`} unit='minutes' info={infoTips.impact} delta='Estimated' />
        <BigNumber label='Defects prevented' value={impact?.defects_prevented || 0} info={infoTips.impact} delta='Estimated' />
        <BigNumber label='Energy saved' value={impact?.energy_saved || 0} unit='kWh' info={infoTips.impact} delta='Estimated' />
      </div>

      <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
        <Card className='p-4'>
          <h4 className='text-sm font-medium mb-2'>Alerts by severity</h4>
          <div className='h-48'>
            <ResponsiveContainer width='100%' height='100%'>
              <BarChart data={severityData}>
                <XAxis dataKey='name' tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ background:'var(--surface)', border:'1px solid var(--border)' }} />
                <Bar dataKey='value' fill='var(--steel)' />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card className='p-4'>
          <h4 className='text-sm font-medium mb-2'>Resolution type</h4>
          <div className='h-48'>
            <ResponsiveContainer width='100%' height='100%'>
              <PieChart>
                <Pie data={resolutionData} dataKey='value' nameKey='name' cx='50%' cy='50%' outerRadius={60} label>{resolutionData.map((_,i) => <Cell key={i} fill={i===0 ? 'var(--healthy)' : 'var(--accent)'} />)}</Pie>
                <Tooltip contentStyle={{ background:'var(--surface)', border:'1px solid var(--border)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className='text-xs text-[var(--text-muted)]'>Auto-resolved = low risk actions executed without human. Human-approved = high-risk actions you approved.</div>
        </Card>
      </div>

      <Card className='p-4'>
        <div className='flex items-center gap-2 mb-2'><h4 className='text-sm font-medium'>How estimates are calculated</h4><InfoTip title={infoTips.impact.title} content={infoTips.impact.content} /></div>
        <ul className='text-xs text-[var(--text-muted)] list-disc ml-5 space-y-1'>
          <li>Downtime avoided = (Historical average downtime for similar fault) minus (Expected downtime with early action from plan). Historical average from failure logs.</li>
          <li>Defects prevented = defect rate trend (defects per hour when torque high) × exposure time avoided.</li>
          <li>Energy saved = reduced load / idle time avoided × average power draw. From energy meters.</li>
          <li>All labeled as Estimated values because they are predictions, not guarantees.</li>
        </ul>
      </Card>
    </div>
  )
}
