import { Link } from 'react-router-dom'
import { PageHeader } from '../layout/PageHeader'
import { useMachines } from '../hooks/useMachines'
import { useAlerts } from '../hooks/useAlerts'
import { useOee } from '../hooks/useOee'
import { useBottlenecks } from '../hooks/useBottlenecks'
import { useImpact } from '../hooks/useMetrics'
import { useLiveStore } from '../store/liveStore'
import { OeeSummary } from '../components/oee/OeeSummary'
import { BottleneckCard } from '../components/oee/BottleneckCard'
import { MachineCard } from '../components/machines/MachineCard'
import { AlertFeed } from '../components/alerts/AlertFeed'
import { PipelineFlow } from '../components/pipeline/PipelineFlow'
import { BigNumber } from '../components/common/BigNumber'
import { Card } from '../components/common/Card'
import { SkeletonCard } from '../components/common/Skeleton'
import { OutcomeButton } from '../components/common/OutcomeButton'
import { outcomes } from '../utils/outcomes'
import { api } from '../api/endpoints'
import { toast } from '../components/common/Toast'

export const CommandCenter = () => {
  const { data: machines, isLoading: mLoading } = useMachines()
  const { data: alerts, isLoading: aLoading } = useAlerts({ limit: '20' })
  const { data: oee, isLoading: oeeLoading } = useOee()
  const { data: bottlenecks } = useBottlenecks()
  const { data: impact } = useImpact()
  const live = useLiveStore(s => s)

  const healthyCount = machines?.filter(m=>m.status==='healthy').length || 0
  const attentionCount = machines?.filter(m=>m.status!=='healthy' && m.status!=='offline').length || 0
  const pendingApprovals = alerts?.filter(a=>a.status==='awaiting_approval').length || 0

  const handleInjectDemo = async () => {
    try {
      const res = await api.injectFault({ machine_id: 'TURBO-01', fault_type: 'drift', magnitude: 0.8, duration_ticks: 100 })
      toast.success(`Demo fault injected on TURBO-01. Watch live chain: chart → alert → agents → ticket.`, { href: `/alerts/${res.alert_id}`, label: 'View alert' })
    } catch (e) {
      toast.error('Failed to inject fault: ' + e.message)
    }
  }

  return (
    <div className='space-y-6'>
      <PageHeader
        title='Command Center - Live Factory Overview'
        purpose='Everything at a glance: health, problems detected, what AI is doing now, and what needs your decision.'
        bullets={[
          'See OEE (how efficiently lines run) and bottleneck (biggest loss)',
          'Check machine health scores and click for sensor trends',
          'Review active alerts - click to see full diagnosis story',
          'Approve or reject AI work orders that need human decision',
        ]}
      />

      <div className='card p-4 flex items-center gap-2'>
        <span className='w-2 h-2 rounded-full bg-[var(--healthy)] live-dot' />
        <span className='text-sm'>Factory Brain is watching {machines?.length || 0} machines. {healthyCount} healthy, {attentionCount} need attention. Last agent activity: {live.agentActivity?.text || 'Monitoring sensor streams...'}</span>
      </div>

      <div className='grid grid-cols-1 lg:grid-cols-3 gap-4'>
        <div className='lg:col-span-2 space-y-4'>
          {oeeLoading ? <SkeletonCard /> : <OeeSummary data={oee} isDemo={false} />}
          <BottleneckCard bottleneck={bottlenecks?.[0]} />
        </div>
        <div className='space-y-3'>
          <div className='grid grid-cols-2 gap-3'>
            <BigNumber label='Healthy machines' value={healthyCount} info={{ title:'Healthy', content:'Machines with health_score 80-100. Running well.' }} />
            <BigNumber label='Open alerts' value={alerts?.length || 0} />
            <BigNumber label='Pending approvals' value={pendingApprovals} info={{ title:'Awaiting approval', content:'High-risk AI actions waiting for human decision.' }} />
            <BigNumber label='Downtime avoided' value={`${impact?.downtime_avoided || 0}`} unit='min' info={{ title:'Downtime avoided', content:'Estimated total minutes saved by early detection.' }} />
          </div>
          <Card className='p-3'>
            <div className='text-sm font-medium mb-2'>Quick actions</div>
            <div className='flex flex-wrap gap-2'>
              <OutcomeButton label='Inject demo fault' outcomes={outcomes.injectFault.preview} onConfirm={handleInjectDemo} variant='primary' />
              <Link to='/actions' className='px-3 py-2 text-xs rounded bg-[var(--surface)] border border-[var(--border)] inline-flex items-center min-h-[44px]'>Review work orders</Link>
              <Link to='/ask' className='px-3 py-2 text-xs rounded bg-[var(--surface)] border border-[var(--border)] inline-flex items-center min-h-[44px]'>Ask the Factory</Link>
              <Link to='/demo' className='px-3 py-2 text-xs rounded border border-[var(--accent)] text-[var(--accent)] inline-flex items-center min-h-[44px]'>Start guided demo</Link>
            </div>
          </Card>
        </div>
      </div>

      <PipelineFlow counters={{ sensors: machines?.length, detection: alerts?.length, diagnosis: alerts?.filter(a=>a.status!=='open').length, planning: alerts?.filter(a=>['planned','awaiting_approval','ticketed'].includes(a.status)).length, action: pendingApprovals, ticket: 3 }} />

      <div className='grid grid-cols-1 lg:grid-cols-3 gap-4'>
        <div className='lg:col-span-2'>
          <h3 className='font-semibold mb-3'>Machine Health Scores</h3>
          {mLoading ? <div className='grid grid-cols-1 md:grid-cols-3 gap-3'><SkeletonCard /><SkeletonCard /><SkeletonCard /></div> : (
            <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3'>
              {machines?.map(m => <MachineCard key={m.machine_id} machine={m} />)}
            </div>
          )}
        </div>
        <div>
          <h3 className='font-semibold mb-3'>Active Alerts & Live Activity</h3>
          {aLoading ? <SkeletonCard /> : <AlertFeed alerts={alerts} limit={8} />}
          {live.agentActivity && (
            <Card className='p-3 mt-3'>
              <div className='text-xs font-medium'>Live agent activity</div>
              <div className='text-xs text-[var(--text-muted)] mt-1'>{live.agentActivity.text}</div>
              <div className='text-[10px] font-mono mt-1'>{new Date(live.agentActivity.ts).toLocaleTimeString()}</div>
            </Card>
          )}
          <div className='mt-3 grid grid-cols-2 gap-2'>
            <BigNumber label='Defects prevented' value={impact?.defects_prevented || 0} />
            <BigNumber label='Energy saved' value={impact?.energy_saved || 0} unit='kWh' />
          </div>
        </div>
      </div>
    </div>
  )
}
