import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Cpu, MessageCircleQuestion, ClipboardList, AlertTriangle, Ticket, BookOpen, FlaskConical, BarChart3, PlayCircle, HelpCircle, ChevronLeft, ChevronRight } from 'lucide-react'
import clsx from 'clsx'

const nav = [
  { path: '/', label: 'Overview', subtitle: 'Everything at a glance', icon: LayoutDashboard, exact: true },
  { path: '/machines', label: 'Machines', subtitle: 'Health of every machine', icon: Cpu },
  { path: '/ask', label: 'Ask the Factory', subtitle: 'Ask questions, get sourced answers', icon: MessageCircleQuestion },
  { path: '/actions', label: 'Agent Actions', subtitle: 'Work orders waiting for you, and the audit log', icon: ClipboardList },
  { path: '/alerts', label: 'Alerts', subtitle: 'Problems the system detected', icon: AlertTriangle },
  { path: '/tickets', label: 'Tickets', subtitle: 'Repair jobs', icon: Ticket },
  { path: '/knowledge', label: 'Knowledge', subtitle: 'Search manuals and past failures', icon: BookOpen },
  { path: '/simulator', label: 'Simulator', subtitle: 'Trigger a fault and watch the AI react', icon: FlaskConical },
  { path: '/impact', label: 'Impact', subtitle: 'Downtime, defects and energy saved', icon: BarChart3 },
  { path: '/demo', label: 'Guided Demo', subtitle: 'Step-by-step walkthrough', icon: PlayCircle },
  { path: '/how-it-works', label: 'How It Works', subtitle: 'Understand the system', icon: HelpCircle },
]

export const Sidebar = ({ collapsed, onToggle, pendingCount }) => {
  return (
    <aside className={clsx('h-screen sticky top-0 bg-[var(--surface)] border-r border-[var(--border)] flex flex-col transition-all', collapsed ? 'w-16' : 'w-64')}>
      <div className='flex items-center justify-between p-4 border-b border-[var(--border)]'>
        {!collapsed && (
          <div>
            <div className='font-bold text-[var(--text-primary)]'>Factory Brain</div>
            <div className='text-[10px] text-[var(--text-muted)]'>AI operations layer</div>
          </div>
        )}
        <button onClick={onToggle} className='p-1.5 rounded hover:bg-[var(--surface-hover)]'>
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
      <nav className='flex-1 overflow-auto py-2'>
        {nav.map(item => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.exact}
              className={({ isActive }) => clsx('flex items-center gap-3 px-3 py-2.5 mx-2 rounded-[8px] text-sm transition-colors', isActive ? 'bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/20' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-hover)]')}
              title={collapsed ? `${item.label}: ${item.subtitle}` : ''}
            >
              <Icon size={18} className='shrink-0' />
              {!collapsed && (
                <div className='flex-1 min-w-0'>
                  <div className='font-medium leading-tight'>{item.label}</div>
                  <div className='text-[10px] text-[var(--text-muted)] leading-tight truncate'>{item.subtitle}</div>
                </div>
              )}
              {!collapsed && item.path === '/actions' && pendingCount >0 && (
                <span className='px-1.5 py-0.5 text-[10px] rounded-full bg-[var(--accent)] text-white font-mono'>{pendingCount}</span>
              )}
            </NavLink>
          )
        })}
      </nav>
      {!collapsed && (
        <div className='p-3 border-t border-[var(--border)] text-[10px] text-[var(--text-muted)]'>
          <div>Theme: dark default, toggle in top bar</div>
          <div className='mt-1'>Keyboard: Tab to navigate, Enter to activate</div>
        </div>
      )}
    </aside>
  )
}
