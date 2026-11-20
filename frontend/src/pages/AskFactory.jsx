import { PageHeader } from '../layout/PageHeader'
import { ChatPanel } from '../components/chat/ChatPanel'
import { Card } from '../components/common/Card'

export const AskFactory = () => {
  return (
    <div className='space-y-4'>
      <PageHeader title='Ask the Factory' purpose='Ask questions, get sourced answers. Answers come only from your manuals, failure logs and sensor data, and every answer shows its sources you can click to verify.' bullets={['Answers include clickable citation markers [1][2] showing manual/log excerpt and similarity score','If evidence is weak, you see "Not enough evidence" warning instead of authoritative answer','Suggested chips start common investigations','Links to related alerts/tickets when relevant']} />
      <div className='grid grid-cols-1 lg:grid-cols-3 gap-4'>
        <div className='lg:col-span-2'>
          <Card className='p-0 overflow-hidden'>
            <ChatPanel />
          </Card>
        </div>
        <div className='space-y-3'>
          <Card className='p-4'>
            <h4 className='text-sm font-medium mb-2'>How RAG works</h4>
            <p className='text-xs text-[var(--text-muted)] leading-relaxed'>When you ask, the system searches knowledge base (manuals, failure logs, sensor logs) for relevant passages. AI generates answer only from those passages. Every claim has citation you can verify.</p>
            <div className='mt-2 text-xs'><span className='font-mono px-1.5 py-0.5 rounded bg-[var(--border)]'>SourceChip</span> shows source file, section, doc type (manual/failure log/sensor log).</div>
          </Card>
          <Card className='p-4'>
            <h4 className='text-sm font-medium mb-2'>Example answers</h4>
            <ul className='text-xs text-[var(--text-muted)] space-y-1 list-disc ml-4'>
              <li>"Why did Line 3 stop at 2 AM?" → cites incident log 2024-02 and tooling manual</li>
              <li>"Which machine most likely to fail?" → cites bearing wear manual + failure log RUL</li>
              <li>"What is slowing line now?" → cites bottleneck + torque tool manual</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  )
}
