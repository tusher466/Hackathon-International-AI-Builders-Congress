export const SourceChip = ({ citation, onClick }) => {
  return (
    <button onClick={onClick} className='inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--surface-hover)]'>
      [{citation.index}] {citation.source.slice(0,20)}... {citation.score ? `${(citation.score*100).toFixed(0)}%` : ''}
    </button>
  )
}
