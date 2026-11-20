import { lazy, Suspense } from 'react'
import { AppShell } from './layout/AppShell'
import { SkeletonCard } from './components/common/Skeleton'

const CommandCenter = lazy(() => import('./pages/CommandCenter').then(m => ({ default: m.CommandCenter })))
const Machines = lazy(() => import('./pages/Machines').then(m => ({ default: m.Machines })))
const MachineDetail = lazy(() => import('./pages/MachineDetail').then(m => ({ default: m.MachineDetail })))
const AskFactory = lazy(() => import('./pages/AskFactory').then(m => ({ default: m.AskFactory })))
const AgentActions = lazy(() => import('./pages/AgentActions').then(m => ({ default: m.AgentActions })))
const Alerts = lazy(() => import('./pages/Alerts').then(m => ({ default: m.Alerts })))
const AlertDetail = lazy(() => import('./pages/AlertDetail').then(m => ({ default: m.AlertDetail })))
const Approvals = lazy(() => import('./pages/Approvals').then(m => ({ default: m.Approvals })))
const Tickets = lazy(() => import('./pages/Tickets').then(m => ({ default: m.Tickets })))
const TicketDetail = lazy(() => import('./pages/TicketDetail').then(m => ({ default: m.TicketDetail })))
const Knowledge = lazy(() => import('./pages/Knowledge').then(m => ({ default: m.Knowledge })))
const Simulator = lazy(() => import('./pages/Simulator').then(m => ({ default: m.Simulator })))
const Impact = lazy(() => import('./pages/Impact').then(m => ({ default: m.Impact })))
const GuidedDemo = lazy(() => import('./pages/GuidedDemo').then(m => ({ default: m.GuidedDemo })))
const HowItWorks = lazy(() => import('./pages/HowItWorks').then(m => ({ default: m.HowItWorks })))
const NotFound = lazy(() => import('./pages/NotFound').then(m => ({ default: m.NotFound })))

const Loader = () => <div className='p-4'><SkeletonCard /></div>

export const routes = [
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Suspense fallback={<Loader />}><CommandCenter /></Suspense> },
      { path: 'machines', element: <Suspense fallback={<Loader />}><Machines /></Suspense> },
      { path: 'machines/:id', element: <Suspense fallback={<Loader />}><MachineDetail /></Suspense> },
      { path: 'ask', element: <Suspense fallback={<Loader />}><AskFactory /></Suspense> },
      { path: 'actions', element: <Suspense fallback={<Loader />}><AgentActions /></Suspense> },
      { path: 'alerts', element: <Suspense fallback={<Loader />}><Alerts /></Suspense> },
      { path: 'alerts/:alertId', element: <Suspense fallback={<Loader />}><AlertDetail /></Suspense> },
      { path: 'approvals', element: <Suspense fallback={<Loader />}><Approvals /></Suspense> },
      { path: 'tickets', element: <Suspense fallback={<Loader />}><Tickets /></Suspense> },
      { path: 'tickets/:ticketId', element: <Suspense fallback={<Loader />}><TicketDetail /></Suspense> },
      { path: 'knowledge', element: <Suspense fallback={<Loader />}><Knowledge /></Suspense> },
      { path: 'simulator', element: <Suspense fallback={<Loader />}><Simulator /></Suspense> },
      { path: 'impact', element: <Suspense fallback={<Loader />}><Impact /></Suspense> },
      { path: 'demo', element: <Suspense fallback={<Loader />}><GuidedDemo /></Suspense> },
      { path: 'how-it-works', element: <Suspense fallback={<Loader />}><HowItWorks /></Suspense> },
      { path: '*', element: <Suspense fallback={<Loader />}><NotFound /></Suspense> },
    ]
  }
]
