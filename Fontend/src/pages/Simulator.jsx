import { useState } from 'react'
import { PageHeader } from '../layout/PageHeader'
import { Card } from '../components/common/Card'
import { OutcomeButton } from '../components/common/OutcomeButton'
import { outcomes } from '../utils/outcomes'
import { api } from '../api/endpoints'
import { toast } from '../components/common/Toast'
import { useLiveStore } from '../store/liveStore'
import { Link } from 'react-router-dom'

export const Simulator = () => {
  const [machineId, setMachineId] = useState('TURBO-03')
  const [faultType, setFaultType] = useState('degradation')
  const [magnitude, setMagnitude] = useState(0.7)
  const [duration, setDuration] = useState(100)
  const [streamState, setStreamState] = useState('running')
  const live = useLiveStore(s => s)

  const faultDescriptions = {
    drift: 'Gradual drift of sensor value over time (e.g. chamber pressure +2 sigma). Usually early indication.',
    spike: 'Sudden spike that may self-clear. Could be loose connection or transient load.',
    stuck: 'Sensor stuck at fixed value. Indicates sensor failure or communication issue.',
    degradation: 'Progressive wear pattern: vibration rising, temperature rising. RUL estimate decreases. Most serious.',
  }

  const expectedResult = {
    drift: 'Alert type anomaly after 20-30 ticks, low/medium severity, monitor_only or reduce_load plan.',
    spike: 'Anomaly detected quickly, confidence may be lower, monitoring continues.',
    stuck: 'Offline or anomaly, may trigger sensor fault ticket.',
    degradation: 'High severity alert, RUL prediction, requires approval for maintenance - see full chain.',
  }

  const handleControl = async (action) => {
    try {
      if (action==='start') { await api.controlStart(); setStreamState('running'); toast.success('Stream started. Charts live.') }
      if (action==='pause') { await api.controlPause(); setStreamState('paused'); toast.info('Stream paused.') }
      if (action==='resume') { await api.controlResume(); setStreamState('running'); toast.success('Stream resumed.') }
      if (action==='stop') { await api.controlStop(); setStreamState('stopped'); toast.info('Stream stopped.') }
    } catch (e) { toast.error(e.message) }
  }

  const handleInject = async () => {
    try {
      const res = await api.injectFault({ machine_id: machineId, fault_type: faultType, magnitude, duration_ticks: duration })
      toast.success(`Injected ${faultType} on ${machineId}. Fault ID ${res.fault_id}. Watch What is happening now panel.`, { href: `/alerts/${res.alert_id}`, label: 'View created alert' })
    } catch (e) { toast.error(e.message) }
  }

  const handleReset = async () => {
    if (!confirm('Reset will clear all injected faults and mock alerts. This cannot be undone in demo mode. Proceed?')) return
    try {
      await api.reset()
      toast.success('Simulation reset. Machines return to healthy baseline, OEE reset.')
    } catch (e) { toast.error(e.message) }
  }

  const presets = [
    { label: 'Engine wear on TURBO-01', machine: 'TURBO-01', type: 'degradation', mag: 0.85 },
    { label: 'Process drift on SECOM-01', machine: 'SECOM-01', type: 'drift', mag: 0.6 },
    { label: 'Torque wear BOSCH-02', machine: 'BOSCH-02', type: 'degradation', mag: 0.75 },
  ]

  return (
    <div className='space-y-4'>
      <PageHeader title='Simulator' purpose='Trigger a fault and watch the AI react live: chart change → alert → agent steps → diagnosis with citations → plan → approval request → ticket → audit entries.' bullets={['Stream controls start/pause/resume/stop with outcome previews','Inject fault form with machine, type, magnitude, duration','Plain description and Expected result per fault type','One-click presets','Live What is happening now panel shows chain step by step with links','Reset button danger style with strong confirm']} />

      <div className='grid grid-cols-1 lg:grid-cols-3 gap-4'>
        <Card className='p-4'>
          <h4 className='font-medium text-sm mb-2'>Stream Controls - Current: {streamState}</h4>
          <div className='flex flex-wrap gap-2'>
            <OutcomeButton label='Start' outcomes={outcomes.startStream.preview} onConfirm={() => handleControl('start')} variant='primary' />
            <OutcomeButton label='Pause' outcomes={outcomes.pauseStream.preview} onConfirm={() => handleControl('pause')} variant='outline' />
            <OutcomeButton label='Resume' outcomes={outcomes.resumeStream.preview} onConfirm={() => handleControl('resume')} variant='outline' />
            <OutcomeButton label='Stop' outcomes={outcomes.stopStream.preview} onConfirm={() => handleControl('stop')} variant='outline' />
          </div>
        </Card>

        <Card className='p-4 lg:col-span-2'>
          <h4 className='font-medium text-sm mb-3'>Inject Fault - watch full incident chain</h4>
          <div className='grid grid-cols-1 md:grid-cols-2 gap-3'>
            <div>
              <label className='text-xs text-[var(--text-muted)]'>Machine</label>
              <select value={machineId} onChange={e=>setMachineId(e.target.value)} className='w-full px-2 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)]'>
                <option>TURBO-01</option><option>TURBO-02</option><option>TURBO-03</option><option>SECOM-01</option><option>SECOM-02</option><option>BOSCH-01</option><option>BOSCH-02</option><option>BOSCH-03</option>
              </select>
            </div>
            <div>
              <label className='text-xs text-[var(--text-muted)]'>Fault type</label>
              <select value={faultType} onChange={e=>setFaultType(e.target.value)} className='w-full px-2 py-2 text-sm rounded border border-[var(--border)] bg-[var(--bg)]'>
                <option value='drift'>drift - slow drift</option><option value='spike'>spike - sudden</option><option value='stuck'>stuck - sensor stuck</option><option value='degradation'>degradation - wear</option>
              </select>
              <div className='text-[11px] text-[var(--text-muted)] mt-1'>{faultDescriptions[faultType]}</div>
              <div className='text-[11px] text-[var(--text-muted)] mt-1'><strong>Expected result:</strong> {expectedResult[faultType]}</div>
            </div>
            <div>
              <label className='text-xs text-[var(--text-muted)]'>Magnitude {magnitude}</label>
              <input type='range' min='0.1' max='1' step='0.1' value={magnitude} onChange={e=>setMagnitude(parseFloat(e.target.value))} className='w-full' />
            </div>
            <div>
              <label className='text-xs text-[var(--text-muted)]'>Duration ticks {duration}</label>
              <input type='range' min='10' max='500' step='10' value={duration} onChange={e=>setDuration(parseInt(e.target.value))} className='w-full' />
            </div>
          </div>
          <div className='mt-3 flex gap-2'>
            <OutcomeButton label='Inject Fault' outcomes={outcomes.injectFault.preview} onConfirm={handleInject} variant='primary' />
            <button onClick={handleReset} className='px-4 py-2 text-sm rounded bg-[var(--critical)] text-white min-h-[44px]'>Reset simulation</button>
          </div>
          <div className='mt-3'>
            <div className='text-xs font-medium mb-1'>One-click presets:</div>
            <div className='flex flex-wrap gap-2'>
              {presets.map(p => (
                <button key={p.label} onClick={() => { setMachineId(p.machine); setFaultType(p.type); setMagnitude(p.mag); }} className='px-2 py-1 text-xs rounded border border-[var(--border)] hover:bg-[var(--surface-hover)]'>{p.label}</button>
              ))}
            </div>
          </div>
        </Card>
      </div>

      <Card className='p-4'>
        <h4 className='font-medium text-sm mb-2'>What is happening now (live chain)</h4>
        <div className='space-y-1 text-xs'>
          {live.recentEvents.slice(0,10).map(ev => (
            <div key={ev.id} className='flex gap-2 p-1 rounded hover:bg-[var(--surface-hover)]'>
              <span className='font-mono text-[10px] text-[var(--text-muted)]'>{new Date(ev.ts).toLocaleTimeString()}</span>
              <span className='px-1.5 py-0.5 rounded bg-[var(--border)] font-mono text-[10px]'>{ev.type}</span>
              <span className='flex-1'>{ev.payload?.machine_id || ev.payload?.alert_id || JSON.stringify(ev.payload).slice(0,80)}</span>
              {ev.payload?.alert_id && <Link to={`/alerts/${ev.payload.alert_id}`} className='text-[var(--accent)] underline'>View alert</Link>}
            </div>
          ))}
          {live.recentEvents.length===0 && <div className='text-[var(--text-muted)]'>No events yet. Inject a fault to see: reading anomalies → alert_created → agent_step (Monitor) → diagnosis_ready → plan_ready → approval_required → ticket_updated</div>}
        </div>
      </Card>
    </div>
  )
}
