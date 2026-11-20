import { useParams, Link } from 'react-router-dom'
import { useMachine, useMachineReadings } from '../hooks/useMachines'
import { useAlerts } from '../hooks/useAlerts'
import { useLiveStore } from '../store/liveStore'
import { PageHeader } from '../layout/PageHeader'
import { Card } from '../components/common/Card'
import { StatusDot } from '../components/common/StatusDot'
import { HealthGauge } from '../components/machines/HealthGauge'
import { SensorChart } from '../components/machines/SensorChart'
import { HealthHistoryChart } from '../components/machines/HealthHistoryChart'
import { ForecastCard } from '../components/machines/ForecastCard'
import { AnomalyExplainer } from '../components/machines/AnomalyExplainer'
import { OutcomeButton } from '../components/common/OutcomeButton'
import { outcomes } from '../utils/outcomes'
import { api } from '../api/endpoints'
import { toast } from '../components/common/Toast'
import { formatMachineType } from '../utils/format'
import { useState, useEffect } from 'react'

export const MachineDetail = () => {
  const { id } = useParams()
  const { data: machine } = useMachine(id)
  const { data: readings } = useMachineReadings(id, 100)
  const { data: alerts } = useAlerts({ machine_id: id })
  const live = useLiveStore(s => s.readings[id])
  const [sensorList, setSensorList] = useState(['vibration','temperature','current'])
  const [liveData, setLiveData] = useState([])

  useEffect(() => {
    if (readings) setLiveData(readings)
  }, [readings])

  useEffect(() => {
    if (live) {
      setLiveData(prev => [...prev.slice(-99), live])
    }
  }, [live])

  const latestAlert = alerts?.[0]

  const handleInject = async () => {
    try {
      const res = await api.injectFault({ machine_id: id, fault_type: 'degradation', magnitude: 0.7, duration_ticks: 50 })
      toast.success(`Fault injected on ${id}. Watch alert appear.`, { href: `/alerts/${res.alert_id}`, label: 'View alert' })
    } catch (e) { toast.error(e.message) }
  }

  if (!machine) return <div className='text-sm'>Loading machine {id}...</div>

  return (
    <div className='space-y-4'>
      <PageHeader title={`Machine ${id}`} purpose={`${formatMachineType(machine.machine_type)} on line ${machine.line_id}. Shows health, live sensor trends, failure forecast, and open alerts.`} bullets={['Health score combines anomaly, RUL, defect risk','Live charts update from WebSocket every second','Forecast shows RUL or defect probability with confidence','Anomaly explainer in plain language']} />

      <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <HealthGauge value={machine.health_score} size={80} />
            <div>
              <div className='font-mono font-bold'>{machine.machine_id}</div>
              <div className='text-xs text-[var(--text-muted)]'>{formatMachineType(machine.machine_type)}</div>
              <StatusDot status={machine.status} />
            </div>
          </div>
          <div className='mt-3 text-sm'>
            <div className='font-medium'>Why is this machine {machine.status}?</div>
            <ul className='text-xs text-[var(--text-muted)] mt-1 list-disc ml-4 space-y-1'>
              {machine.health_score < 50 && <li>Health score {machine.health_score} below 50 threshold</li>}
              {machine.open_alert_count>0 && <li>{machine.open_alert_count} open alerts</li>}
              {latestAlert && <li>Anomaly score {latestAlert.anomaly_score} on {latestAlert.top_sensors?.[0]?.name}</li>}
              {latestAlert?.predicted_rul && <li>RUL only {latestAlert.predicted_rul}h left</li>}
              {latestAlert?.defect_probability && <li>Defect probability {(latestAlert.defect_probability*100).toFixed(0)}%</li>}
            </ul>
          </div>
        </Card>
        <ForecastCard machine={machine} alert={latestAlert} />
        <Card className='p-4'>
          <h4 className='text-sm font-medium mb-2'>Actions</h4>
          <OutcomeButton label={`Inject fault on ${id}`} outcomes={outcomes.injectFault.preview} onConfirm={handleInject} variant='primary' />
          <div className='mt-3 text-xs text-[var(--text-muted)]'>
            <Link to={`/alerts?machine_id=${id}`} className='text-[var(--accent)] underline'>View alerts for this machine</Link> • <Link to={`/tickets?machine_id=${id}`} className='text-[var(--accent)] underline'>Tickets</Link>
          </div>
        </Card>
      </div>

      <div className='flex gap-2 items-center text-xs'>
        <span>Sensor selector:</span>
        {['vibration','temperature','current','vibration_bearing_7','torque_station_4','chamber_pressure'].map(k => (
          <button key={k} onClick={() => setSensorList(list => list.includes(k) ? list.filter(x=>x!==k) : [...list,k])} className={`px-2 py-1 rounded border ${sensorList.includes(k) ? 'bg-[var(--accent)] text-white border-[var(--accent)]' : 'border-[var(--border)]'}`}>{k}</button>
        ))}
      </div>

      <div className='grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3'>
        {sensorList.map(key => (
          <SensorChart key={key} data={liveData} dataKey={key} label={key.replace('_',' ')} unit='' />
        ))}
      </div>

      <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
        <HealthHistoryChart data={liveData} />
        <AnomalyExplainer alert={latestAlert} diagnosis={latestAlert?.diagnosis} />
      </div>

      <Card className='p-4'>
        <h4 className='font-medium text-sm mb-2'>Open alerts for this machine</h4>
        {alerts?.length===0 ? <div className='text-xs text-[var(--text-muted)]'>No open alerts. When anomaly score crosses threshold, alert appears here.</div> : (
          <div className='space-y-2'>
            {alerts?.map(a => (
              <Link key={a.alert_id} to={`/alerts/${a.alert_id}`} className='block p-2 rounded border border-[var(--border)] hover:bg-[var(--surface-hover)]'>
                <div className='flex gap-2 items-center'><span className='font-mono text-xs'>{a.alert_id}</span><span className='text-xs'>{a.severity}</span><span className='text-xs font-mono'>{a.alert_type}</span></div>
                <div className='text-xs text-[var(--text-muted)]'>{a.description}</div>
              </Link>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
