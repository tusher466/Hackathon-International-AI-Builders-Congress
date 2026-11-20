import { SourceChip } from './SourceChip'
import { Link } from 'react-router-dom'

export const ChatMessage = ({ message, onSourceClick }) => {
  const isUser = message.role === 'user'
  if (isUser) {
    return (
      <div className='flex justify-end'>
        <div className='max-w-[80%] p-3 rounded-[8px] bg-[var(--accent)] text-white text-sm'>{message.content}</div>
      </div>
    )
  }
  // assistant
  const hasEvidence = message.citations && message.citations.length>0
  return (
    <div className='flex gap-2'>
      <div className='w-6 h-6 rounded-full bg-[var(--accent)] text-white flex items-center justify-center text-[10px] font-bold'>AI</div>
      <div className='flex-1'>
        <div className='p-3 rounded-[8px] bg-[var(--bg)] border border-[var(--border)] text-sm leading-relaxed'>
          {message.answer || message.content}
          {!hasEvidence && message.answer && <div className='mt-2 p-2 rounded bg-[var(--warning)]/10 border border-[var(--warning)]/30 text-xs'>Not enough evidence in the manuals or logs - this answer is based on weak matches. Verify with alerts and machine data.</div>}
          {hasEvidence && (
            <div className='mt-2 flex flex-wrap gap-1'>
              {message.citations.map(c => (
                <SourceChip key={c.index} citation={c} onClick={() => onSourceClick(message)} />
              ))}
            </div>
          )}
          {message.related_alert_ids?.length>0 && (
            <div className='mt-2 text-xs'>Related alerts: {message.related_alert_ids.map(id => <Link key={id} to={`/alerts/${id}`} className='text-[var(--accent)] underline mr-2'>{id}</Link>)}</div>
          )}
        </div>
        <div className='mt-1 flex gap-2 text-[10px] text-[var(--text-muted)]'>
          <button className='hover:text-[var(--text-primary)]'>👍 Helpful</button>
          <button className='hover:text-[var(--text-primary)]'>👎 Not helpful</button>
        </div>
      </div>
    </div>
  )
}
