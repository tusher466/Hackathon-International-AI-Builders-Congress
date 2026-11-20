import { useState } from 'react'
import { ChatMessage } from './ChatMessage'
import { SuggestedQuestions } from './SuggestedQuestions'
import { OutcomeButton } from '../common/OutcomeButton'
import { outcomes } from '../../utils/outcomes'
import { useChat } from '../../hooks/useChat'

export const ChatPanel = () => {
  const { history, send, isLoading } = useChat()
  const [input, setInput] = useState('')
  const [selectedSources, setSelectedSources] = useState(null)

  const handleSend = () => {
    if (!input.trim()) return
    send(input)
    setInput('')
  }

  return (
    <div className='flex flex-col h-[70vh]'>
      <div className='flex-1 overflow-auto p-4 space-y-4'>
        {history.length===0 && (
          <div>
            <div className='text-sm text-[var(--text-muted)] mb-3'>Ask questions in plain language. Answers come only from your manuals, failure logs and sensor data, and every answer shows its sources.</div>
            <SuggestedQuestions onSelect={(q) => { setInput(q); send(q) }} />
          </div>
        )}
        {history.map((m,i) => (
          <ChatMessage key={i} message={m} onSourceClick={setSelectedSources} />
        ))}
        {isLoading && <div className='text-xs text-[var(--text-muted)]'>AI is searching manuals and logs...</div>}
      </div>
      <div className='p-3 border-t border-[var(--border)]'>
        <div className='flex gap-2'>
          <textarea
            value={input}
            onChange={e=>setInput(e.target.value)}
            onKeyDown={e=>{ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); handleSend() } }}
            placeholder='Ask: Why did Line 3 stop at 2 AM? Which machine will fail?'
            className='flex-1 px-3 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)] resize-none min-h-[44px]'
            rows={2}
          />
          <OutcomeButton label='Ask' variant='primary' outcomes={outcomes.ask.preview} onConfirm={handleSend} confirmRequired={false} />
        </div>
        <div className='text-[10px] text-[var(--text-muted)] mt-1'>Enter to send, Shift+Enter for new line</div>
      </div>

      {selectedSources && (
        <div className='fixed inset-0 z-50 flex justify-end'>
          <div className='flex-1 bg-black/40' onClick={() => setSelectedSources(null)} />
          <div className='w-96 max-w-[90vw] bg-[var(--surface)] border-l border-[var(--border)] h-full overflow-auto p-4'>
            <div className='flex justify-between items-center mb-3'>
              <h3 className='font-semibold'>Sources</h3>
              <button onClick={() => setSelectedSources(null)} className='text-xs'>Close</button>
            </div>
            {selectedSources?.citations?.map(c => (
              <div key={c.index} className='mb-3 p-3 rounded border border-[var(--border)]'>
                <div className='text-xs font-mono'>[{c.index}] {c.source} - {c.section}</div>
                <div className='text-xs mt-1'>{c.excerpt}</div>
                <div className='text-[10px] text-[var(--text-muted)] mt-1'>Score: {(c.score*100).toFixed(0)}% • Type: {c.doc_type}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
