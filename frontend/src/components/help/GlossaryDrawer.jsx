import { Drawer } from '../common/Drawer'
import { glossaryTerms } from '../../utils/glossary'

export const GlossaryDrawer = ({ open, onClose }) => {
  return (
    <Drawer open={open} onClose={onClose} title='Glossary - Plain explanations' width='w-[480px]'>
      <div className='space-y-4'>
        <p className='text-xs text-[var(--text-muted)]'>Technical terms explained simply. Every metric badge has an (i) icon with same explanation nearby.</p>
        {glossaryTerms.map(t => (
          <div key={t.term} className='border-b border-[var(--border)] pb-3'>
            <div className='font-semibold text-sm'>{t.term} - {t.short}</div>
            <div className='text-xs text-[var(--text-primary)] mt-1 leading-relaxed'>{t.definition}</div>
            {t.goodBad && <div className='text-[11px] text-[var(--text-muted)] mt-1'>{t.goodBad}</div>}
          </div>
        ))}
      </div>
    </Drawer>
  )
}
