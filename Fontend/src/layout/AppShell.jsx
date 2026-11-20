import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { useLiveSocket } from '../hooks/useLiveSocket'
import { useApprovals } from '../hooks/useApprovals'
import { GlossaryDrawer } from '../components/help/GlossaryDrawer'
import { GuidedTour } from '../components/help/GuidedTour'
import { ToastContainer } from '../components/common/Toast'

export const AppShell = () => {
  const [collapsed, setCollapsed] = useState(false)
  const [glossaryOpen, setGlossaryOpen] = useState(false)
  const [tourOpen, setTourOpen] = useState(() => !localStorage.getItem('factory-brain-tour-done'))
  const { status, isDemo } = useLiveSocket()
  const { data: approvals } = useApprovals()

  return (
    <div className='flex min-h-screen bg-[var(--bg)] text-[var(--text-primary)]'>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} pendingCount={approvals?.length || 0} />
      <div className='flex-1 flex flex-col min-w-0'>
        <TopBar liveStatus={status} isDemo={isDemo} onGlossary={() => setGlossaryOpen(true)} onTour={() => setTourOpen(true)} />
        <main className='flex-1 p-4 md:p-6 overflow-auto'>
          <Outlet />
        </main>
      </div>
      <GlossaryDrawer open={glossaryOpen} onClose={() => setGlossaryOpen(false)} />
      <GuidedTour open={tourOpen} onClose={() => { setTourOpen(false); localStorage.setItem('factory-brain-tour-done','true') }} />
      <ToastContainer />
    </div>
  )
}
