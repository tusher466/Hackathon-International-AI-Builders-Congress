import { useState } from 'react'
import { Link } from 'react-router-dom'
import { PageHeader } from '../layout/PageHeader'
import { useAlerts } from '../hooks/useAlerts'
import { Card } from '../components/common/Card'
import { SeverityBadge } from '../components/common/StatusDot'
import { formatRelativeTime, formatAbsoluteTime } from '../utils/format'

export const Alerts = () => {
  const [filters, setFilters] = useState({})
  const { data: alerts, isLoading } = useAlerts({ ...filters, limit: '100' })

  return (
    <div className='space-y-4'>
      <PageHeader title='Alerts' purpose='Problems the system detected from sensor data. Each alert has severity, confidence, top sensors, and full story of detection → diagnosis → plan → ticket.' bullets={['Filter by severity, status, machine, type','Live-updating: new alerts fade in without full refetch','Severity badge includes icon+label for color-blind safety','Mini stepper shows Detected/Diagnosed/Planned/Awaiting approval/Ticketed','Click row to see full incident story']} />

      <div className='flex flex-wrap gap-2 text-xs'>
        <select value={filters.severity||''} onChange={e=>setFilters({...filters, severity: e.target.value})} className='px-2 py-2 rounded border border-[var(--border)] bg-[var(--bg)]'>
          <option value=''>All severity</option>
          <option value='low'>Low - Watch</option>
          <option value='medium'>Medium - Needs attention</option>
          <option value='high'>High - Act soon</option>
          <option value='critical'>Needs action now</option>
        </select>
        <select value={filters.status||''} onChange={e=>setFilters({...filters, status: e.target.value})} className='px-2 py-2 rounded border border-[var(--border)] bg-[var(--bg)]'>
          <option value=''>All status</option>
          <option value='open'>Open</option>
          <option value='diagnosed'>Diagnosed</option>
          <option value='planned'>Plan ready</option>
          <option value='awaiting_approval'>Awaiting approval</option>
          <option value='ticketed'>Ticketed</option>
        </select>
        <input placeholder='Machine ID' value={filters.machine_id||''} onChange={e=>setFilters({...filters, machine_id: e.target.value})} className='px-2 py-2 rounded border border-[var(--border)] bg-[var(--bg)]' />
        <input placeholder='Type anomaly/degradation/defect_risk' value={filters.alert_type||''} onChange={e=>{ const v=e.target.value; setFilters({...filters, ...(v?{alert_type:v}:{})}) }} className='px-2 py-2 rounded border border-[var(--border)] bg-[var(--bg)] w-64' />
        <button onClick={() => setFilters({})} className='px-3 py-2 rounded border border-[var(--border)]'>Clear</button>
      </div>

      {isLoading ? <div className='text-xs'>Loading alerts...</div> : (
        <Card className='p-0 overflow-auto'>
          <table className='w-full text-xs'>
            <thead><tr className='text-left text-[var(--text-muted)] border-b border-[var(--border)]'><th className='p-2'>Severity</th><th>Machine</th><th>Type</th><th>Confidence</th><th>Time</th><th>Status</th><th>Stepper</th></tr></thead>
            <tbody>
              {alerts?.map(a => (
                <tr key={a.alert_id} className='border-b border-[var(--border)] hover:bg-[var(--surface-hover)]'>
                  <td className='p-2'><Link to={`/alerts/${a.alert_id}`}><SeverityBadge severity={a.severity} /></Link></td>
                  <td className='p-2 font-mono'>{a.machine_id}</td>
                  <td className='p-2'>{a.alert_type}</td>
                  <td className='p-2 font-mono'>{ (a.confidence*100).toFixed(0)}%<div className='h-1 bg-[var(--border)] rounded mt-1 w-16'><div className='h-full bg-[var(--steel)]' style={{ width: `${a.confidence*100}%` }} /></div></td>
                  <td className='p-2 font-mono' title={formatAbsoluteTime(a.ts)}>{formatRelativeTime(a.ts)}</td>
                  <td className='p-2'>{a.status}</td>
                  <td className='p-2'><div className='flex gap-1'>{['detected','diagnosed','planned','awaiting_approval','ticketed'].map(step => <div key={step} className={`w-2 h-2 rounded-full ${['detected','diagnosed','planned','awaiting_approval','ticketed'].indexOf(a.status) >= ['detected','diagnosed','planned','awaiting_approval','ticketed'].indexOf(step) || a.status===step ? 'bg-[var(--accent)]' : 'bg-[var(--border)]'}`} title={step} />)}</div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
