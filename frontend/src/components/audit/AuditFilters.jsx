export const AuditFilters = ({ filters, setFilters, onExport }) => {
  return (
    <div className='flex flex-wrap gap-2 items-center text-xs'>
      <select value={filters.actor||''} onChange={e=>setFilters({...filters, actor: e.target.value})} className='px-2 py-1 rounded border border-[var(--border)] bg-[var(--bg)]'>
        <option value=''>All actors</option>
        <option value='ai'>AI only</option>
        <option value='human'>Human only</option>
      </select>
      <select value={filters.type||''} onChange={e=>setFilters({...filters, type: e.target.value})} className='px-2 py-1 rounded border border-[var(--border)] bg-[var(--bg)]'>
        <option value=''>All events</option>
        <option value='suggestion'>Suggestion</option>
        <option value='approval'>Approval</option>
        <option value='rejection'>Rejection</option>
        <option value='execution'>Execution</option>
        <option value='override'>Override</option>
      </select>
      <input placeholder='Machine ID' value={filters.machine_id||''} onChange={e=>setFilters({...filters, machine_id: e.target.value})} className='px-2 py-1 rounded border border-[var(--border)] bg-[var(--bg)] w-28' />
      <button onClick={onExport} className='px-3 py-1 rounded border border-[var(--border)] hover:bg-[var(--surface-hover)]'>Export CSV</button>
    </div>
  )
}
