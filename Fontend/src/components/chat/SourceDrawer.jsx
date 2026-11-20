import { Drawer } from '../common/Drawer'

export const SourceDrawer = ({ open, onClose, citation }) => {
  return (
    <Drawer open={open} onClose={onClose} title='Source Detail'>
      {citation && (
        <div>
          <div className='text-xs font-mono'>{citation.source}</div>
          <div className='text-xs text-[var(--text-muted)]'>{citation.section} • {citation.doc_type}</div>
          <div className='mt-3 p-3 rounded bg-[var(--bg)] border border-[var(--border)] text-sm'>{citation.excerpt}</div>
          <div className='text-xs mt-2'>Similarity: {(citation.score*100).toFixed(0)}%</div>
        </div>
      )}
    </Drawer>
  )
}
