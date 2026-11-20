const suggestions = [
  'Why did Line 3 stop at 2 AM?',
  'Which machine is most likely to fail this week?',
  'What fixed compressor fouling last time?',
  'What is slowing down the line right now?',
]

export const SuggestedQuestions = ({ onSelect }) => {
  return (
    <div className='flex flex-wrap gap-2'>
      {suggestions.map(q => (
        <button key={q} onClick={() => onSelect(q)} className='px-3 py-1.5 text-xs rounded-full border border-[var(--border)] hover:bg-[var(--surface-hover)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'>
          {q}
        </button>
      ))}
    </div>
  )
}
