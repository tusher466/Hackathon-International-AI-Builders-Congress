import { useState } from 'react'
import { PageHeader } from '../layout/PageHeader'
import { Card } from '../components/common/Card'
import { api } from '../api/endpoints'

export const Knowledge = () => {
  const [query, setQuery] = useState('')
  const [machineType, setMachineType] = useState('')
  const [k, setK] = useState(5)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  const search = async () => {
    setLoading(true)
    try {
      const res = await api.searchKnowledge({ query, machine_type: machineType || undefined, k })
      setResults(res)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className='space-y-4'>
      <PageHeader title='Knowledge - Manuals & Failure Logs' purpose='This is the library the Diagnosis Agent reads before it answers. Every diagnosis cites these sources.' bullets={['Search manuals, failure logs, sensor logs','Results show passage with highlighted terms, source, section, similarity score','Similarity bar in plain explanation','Doc type badge: manual / failure log / sensor log','Same data used by Ask the Factory chat']} />

      <Card className='p-4'>
        <div className='flex flex-wrap gap-2 items-end'>
          <div className='flex-1 min-w-[280px]'>
            <label className='text-xs text-[var(--text-muted)]'>Search query</label>
            <input value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=> e.key==='Enter' && search()} placeholder='e.g. compressor fouling symptoms, chamber pressure drift' className='w-full px-3 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)]' />
          </div>
          <div>
            <label className='text-xs text-[var(--text-muted)]'>Machine type</label>
            <select value={machineType} onChange={e=>setMachineType(e.target.value)} className='w-full px-2 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)]'><option value=''>All</option><option value='turbofan'>Turbofan</option><option value='secom'>SECOM</option><option value='bosch'>Bosch</option></select>
          </div>
          <div>
            <label className='text-xs text-[var(--text-muted)]'>k results</label>
            <select value={k} onChange={e=>setK(parseInt(e.target.value))} className='px-2 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)]'><option value={3}>3</option><option value={5}>5</option><option value={10}>10</option></select>
          </div>
          <button onClick={search} className='px-4 py-2 text-sm rounded bg-[var(--accent)] text-white min-h-[40px]'>Search</button>
        </div>
        <div className='mt-2 flex gap-2 flex-wrap'>
          {['compressor fouling symptoms','chamber pressure drift','bearing wear','torque tool wear'].map(chip => (
            <button key={chip} onClick={() => { setQuery(chip); setTimeout(search, 100) }} className='px-2 py-1 text-xs rounded-full border border-[var(--border)] hover:bg-[var(--surface-hover)]'>{chip}</button>
          ))}
        </div>
      </Card>

      {loading ? <div className='text-xs'>Searching...</div> : (
        <div className='space-y-3'>
          {results.map((r,i) => (
            <Card key={i} className='p-4'>
              <div className='flex items-center gap-2 mb-1'>
                <span className='font-mono text-xs font-semibold'>[{r.index || i+1}] {r.source}</span>
                <span className='text-xs px-1.5 py-0.5 rounded bg-[var(--border)]'>{r.doc_type}</span>
                <span className='text-xs text-[var(--text-muted)]'>{r.section}</span>
              </div>
              <div className='text-sm font-mono bg-[var(--bg)] p-2 rounded border border-[var(--border)] mt-2' dangerouslySetInnerHTML={{ __html: (r.text || r.highlight || '').replace(new RegExp(query, 'gi'), (m) => query ? `<mark class="bg-[var(--warning)]/30">${m}</mark>` : m) }} />
              <div className='mt-2 flex items-center gap-2'>
                <div className='flex-1 h-2 bg-[var(--border)] rounded-full overflow-hidden'><div className='h-full bg-[var(--accent)]' style={{ width: `${(r.score*100)}%` }} /></div>
                <span className='text-xs font-mono'>{ (r.score*100).toFixed(0)}% similarity</span>
              </div>
              <div className='text-[10px] text-[var(--text-muted)] mt-1'>Higher percentage means closer match to your query. Based on cosine similarity of embeddings.</div>
            </Card>
          ))}
          {results.length===0 && query && <div className='text-xs text-[var(--text-muted)]'>No results. Try different terms. Manuals contain bearing wear, torque, chamber pressure sections.</div>}
        </div>
      )}
    </div>
  )
}
