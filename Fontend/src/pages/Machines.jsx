import { useState } from 'react'
import { PageHeader } from '../layout/PageHeader'
import { useMachines } from '../hooks/useMachines'
import { MachineCard } from '../components/machines/MachineCard'
import { SkeletonCard } from '../components/common/Skeleton'
import { EmptyState } from '../components/common/EmptyState'

export const Machines = () => {
  const { data: machines, isLoading } = useMachines()
  const [filterType, setFilterType] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [search, setSearch] = useState('')
  const [view, setView] = useState('grid')

  const filtered = machines?.filter(m => {
    if (filterType && m.machine_type !== filterType) return false
    if (filterStatus && m.status !== filterStatus) return false
    if (search && !m.machine_id.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <div className='space-y-4'>
      <PageHeader title='Machines' purpose='Health of every machine. See health score, status, and open alerts. Click a card to see sensor trends and forecast.' bullets={['Filter by type (turbofan, secom, bosch) and status','Search by machine ID','Health score tooltip explains calculation','Grid/table toggle for dense view']} />

      <div className='flex flex-wrap gap-2 items-center'>
        <input placeholder='Search ID (e.g. TURBO-01)' value={search} onChange={e=>setSearch(e.target.value)} className='px-3 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)]' />
        <select value={filterType} onChange={e=>setFilterType(e.target.value)} className='px-2 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)]'>
          <option value=''>All types</option>
          <option value='turbofan'>Turbofan engine</option>
          <option value='secom'>Semiconductor (SECOM)</option>
          <option value='bosch'>Assembly line (Bosch)</option>
        </select>
        <select value={filterStatus} onChange={e=>setFilterStatus(e.target.value)} className='px-2 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)]'>
          <option value=''>All status</option>
          <option value='healthy'>Running well</option>
          <option value='warning'>Needs attention</option>
          <option value='critical'>Needs action now</option>
          <option value='offline'>No data</option>
        </select>
        <button onClick={() => setView(v=>v==='grid'?'table':'grid')} className='px-3 py-2 text-xs rounded border border-[var(--border)]'>{view==='grid'?'Table view':'Grid view'}</button>
      </div>

      {isLoading ? <div className='grid grid-cols-1 md:grid-cols-3 gap-3'><SkeletonCard /><SkeletonCard /><SkeletonCard /></div> : filtered?.length===0 ? <EmptyState title='No machines match filters' description='Try clearing type/status filters or search. Machines appear here once ingestion sees them.' /> : view==='grid' ? (
        <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3'>
          {filtered.map(m => <MachineCard key={m.machine_id} machine={m} />)}
        </div>
      ) : (
        <div className='card overflow-auto'>
          <table className='w-full text-sm'>
            <thead><tr className='text-left text-[var(--text-muted)] border-b border-[var(--border)]'><th className='p-2'>ID</th><th>Type</th><th>Health</th><th>Status</th><th>Alerts</th><th>Last seen</th></tr></thead>
            <tbody>{filtered.map(m => <tr key={m.machine_id} className='border-b border-[var(--border)]'><td className='p-2 font-mono'>{m.machine_id}</td><td className='p-2'>{m.machine_type}</td><td className='p-2'>{m.health_score}</td><td className='p-2'>{m.status}</td><td className='p-2'>{m.open_alert_count}</td><td className='p-2 text-xs'>{new Date(m.last_seen).toLocaleString()}</td></tr>)}</tbody>
          </table>
        </div>
      )}
    </div>
  )
}
