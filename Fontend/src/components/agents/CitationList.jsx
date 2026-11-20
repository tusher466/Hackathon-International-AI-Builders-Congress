import { useState } from 'react'
import { Card } from '../common/Card'

export const CitationList = ({ citations }) => {
  const [openIdx, setOpenIdx] = useState(null)
  if (!citations || citations.length===0) {
    return (
      <Card className='p-4 border-l-4 border-[var(--warning)]'>
        <div className='text-sm font-medium'>⚠ Insufficient evidence</div>
        <p className='text-xs text-[var(--text-muted)] mt-1'>The AI did not find strong matching passages in manuals or logs. Recommendation is based on sensor pattern only. A human should review.</p>
      </Card>
    )
  }
  return (
    <div className='space-y-2'>
      {citations.map((c) => (
        <Card key={c.index} className='p-3'>
          <div className='flex items-start justify-between gap-2'>
            <div>
              <div className='text-xs font-mono'>[{c.index}] {c.source} • {c.section} <span className='px-1.5 py-0.5 rounded bg-[var(--border)] ml-1'>{c.doc_type}</span></div>
              <div className='text-xs text-[var(--text-muted)] mt-1'>Similarity score: {(c.score*100).toFixed(0)}% - higher means closer match</div>
            </div>
            <button onClick={() => setOpenIdx(openIdx===c.index ? null : c.index)} className='text-xs text-[var(--accent)] underline'>{openIdx===c.index ? 'Hide' : 'Show excerpt'}</button>
          </div>
          {openIdx===c.index && (
            <div className='mt-2 p-2 rounded bg-[var(--bg)] border border-[var(--border)] text-xs font-mono leading-relaxed'>"{c.excerpt}"</div>
          )}
        </Card>
      ))}
    </div>
  )
}
