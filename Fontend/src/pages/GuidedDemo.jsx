import { useState } from 'react'
import { PageHeader } from '../layout/PageHeader'
import { Card } from '../components/common/Card'
import { OutcomeButton } from '../components/common/OutcomeButton'
import { outcomes } from '../utils/outcomes'
import { api } from '../api/endpoints'
import { toast } from '../components/common/Toast'
import { Link } from 'react-router-dom'

const steps = [
  { id:1, title:'Meet the factory', desc:'Factory Brain watches 10 machines across 3 lines (Turbofan engines, Semiconductor SECOM, Assembly Bosch). Overview shows health scores and OEE.', action:'Go to Overview', link:'/' },
  { id:2, title:'Start the data stream', desc:'Sensor data streams 1Hz via WebSocket. Charts update live. Detection models watch for anomalies.', action:'Start Stream', api: 'start' },
  { id:3, title:'Inject a fault', desc:'Simulate bearing wear. Choose machine, fault type degradation, magnitude 0.8. Watch chart drift.', action:'Inject fault on TURBO-03', api: 'inject' },
  { id:4, title:'Watch detection', desc:'When anomaly_score crosses 0.6, Monitor Agent creates alert with severity, confidence, top sensors.', action:'View alerts', link:'/alerts' },
  { id:5, title:'See the agents think', desc:'Diagnosis Agent searches manuals. You see agent timeline: Monitor → Diagnosis → Planner, each with reasoning and duration.', action:'View alert trace', link:'/alerts/ALT-1001' },
  { id:6, title:'Read diagnosis and sources', desc:'Root cause with citations [1][2] showing manual excerpts. If evidence weak, you see insufficient evidence warning.', action:'Check diagnosis', link:'/alerts/ALT-1001' },
  { id:7, title:'Approve the work order', desc:'High-risk plan requires approval. Approve button shows outcome preview: agents resume, ticket moves to In Progress, technician notified.', action:'Approve in Agent Actions', link:'/actions' },
  { id:8, title:'See ticket, audit log and impact', desc:'Ticket created with repair steps and safety warnings. Audit log shows your approval. Impact numbers increase.', action:'View Impact', link:'/impact' },
]

export const GuidedDemo = () => {
  const [current, setCurrent] = useState(0)
  const [completed, setCompleted] = useState([])
  const [liveInfo, setLiveInfo] = useState('Ready to start demo walkthrough. Each step has Run this step button that performs real API call in mock mode.')

  const runStep = async (step) => {
    setLiveInfo(`Running step ${step.id}: ${step.title}...`)
    try {
      if (step.api==='start') {
        await api.controlStart()
        toast.success('Stream started')
        setLiveInfo('Stream started: sensor charts now updating live every second. Detection models active.')
      } else if (step.api==='inject') {
        const res = await api.injectFault({ machine_id: 'TURBO-03', fault_type: 'degradation', magnitude: 0.8, duration_ticks: 100 })
        toast.success(`Fault injected, alert ${res.alert_id} created`, { href: `/alerts/${res.alert_id}`, label: 'View' })
        setLiveInfo(`Fault injected on TURBO-03. Alert ${res.alert_id} created. Check Alerts page. In a few seconds agent steps will appear.`)
      } else {
        setLiveInfo(`Step ${step.id} would navigate to ${step.link}. In real demo, you would see ${step.desc}`)
      }
      setCompleted(c => [...c, step.id])
    } catch (e) {
      toast.error(e.message)
      setLiveInfo(`Error: ${e.message}`)
    }
  }

  return (
    <div className='space-y-4'>
      <PageHeader title='Guided Demo - 8 steps' purpose='Step-by-step walkthrough of full incident chain from sensor to ticket.' bullets={['Progress bar shows where you are','Each step has Run this step button with real mock API','Live panel shows what just happened','Back/next and Skip to full app']} />

      <div className='w-full h-2 bg-[var(--border)] rounded-full overflow-hidden'>
        <div className='h-full bg-[var(--accent)] transition-all' style={{ width: `${((current+1)/steps.length)*100}%` }} />
      </div>

      <div className='grid grid-cols-1 lg:grid-cols-3 gap-4'>
        <div className='lg:col-span-2 space-y-3'>
          {steps.map((s,i) => (
            <Card key={s.id} className={`p-4 ${i===current ? 'border-[var(--accent)]' : ''}`}>
              <div className='flex items-start justify-between gap-2'>
                <div>
                  <div className='flex items-center gap-2'><span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border ${completed.includes(s.id) ? 'bg-[var(--healthy)] text-white border-[var(--healthy)]' : i===current ? 'bg-[var(--accent)] text-white border-[var(--accent)]' : 'border-[var(--border)]'}`}>{s.id}</span><h4 className='font-medium text-sm'>{s.title}</h4></div>
                  <p className='text-xs text-[var(--text-muted)] mt-1'>{s.desc}</p>
                </div>
                <OutcomeButton label='Run this step' outcomes={[`Step ${s.id}: ${s.desc}`, 'Updates live panels']} onConfirm={() => runStep(s)} variant={i===current ? 'primary' : 'outline'} confirmRequired={false} />
              </div>
              {s.link && <Link to={s.link} className='mt-2 inline-block text-xs text-[var(--accent)] underline'>{s.action} →</Link>}
            </Card>
          ))}

          <div className='flex justify-between'>
            <button disabled={current===0} onClick={() => setCurrent(c=>Math.max(0,c-1))} className='px-4 py-2 text-sm rounded border border-[var(--border)] disabled:opacity-50'>Back</button>
            <div className='flex gap-2'>
              <Link to='/' className='px-4 py-2 text-sm rounded border border-[var(--border)]'>Skip to full app</Link>
              <button disabled={current===steps.length-1} onClick={() => setCurrent(c=>Math.min(steps.length-1,c+1))} className='px-4 py-2 text-sm rounded bg-[var(--accent)] text-white disabled:opacity-50'>Next</button>
            </div>
          </div>
        </div>

        <Card className='p-4 h-fit sticky top-20'>
          <h4 className='font-medium text-sm mb-2'>What is happening now (live)</h4>
          <div className='text-xs text-[var(--text-muted)] leading-relaxed bg-[var(--bg)] p-3 rounded border border-[var(--border)] min-h-[120px]'>{liveInfo}</div>
          <div className='mt-3 text-xs'>
            <div>Completed: {completed.length}/{steps.length}</div>
            <div className='mt-2 p-2 rounded bg-[var(--bg)] border border-[var(--border)]'><strong>Tip:</strong> Injecting a fault drives full chain: chart change → alert → agent steps → diagnosis with citations → plan → approval request → ticket → audit entries.</div>
          </div>
        </Card>
      </div>
    </div>
  )
}
