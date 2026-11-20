import { Moon, Sun, Monitor, BookOpen, Play } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'
import { useHealth } from '../hooks/useMetrics'

export const TopBar = ({ liveStatus, isDemo, onGlossary, onTour }) => {
  const { theme, toggleTheme, floorMode, toggleFloor } = useTheme()
  const { data: health } = useHealth()

  const liveLabel = liveStatus === 'live' ? 'Live' : liveStatus === 'reconnecting' ? 'Reconnecting' : liveStatus === 'connecting' ? 'Connecting' : 'Offline'
  const liveColor = liveStatus === 'live' ? 'bg-[var(--healthy)]' : liveStatus === 'reconnecting' ? 'bg-[var(--warning)]' : 'bg-[var(--critical)]'

  return (
    <header className='h-14 sticky top-0 z-30 bg-[var(--surface)] border-b border-[var(--border)] flex items-center justify-between px-4 gap-2'>
      <div className='flex items-center gap-3'>
        <div className='flex items-center gap-2'>
          <span className={`w-2 h-2 rounded-full ${liveColor} live-dot`} />
          <span className='text-xs font-mono'>{liveLabel}</span>
          {isDemo && <span className='text-[10px] px-1.5 py-0.5 rounded bg-[var(--border)] font-mono'>Demo data</span>}
        </div>
        {health && (
          <span className={`text-[10px] px-2 py-0.5 rounded-full border text-xs ${health.status==='degraded' ? 'bg-[var(--warning)]/15 text-[var(--warning)] border-[var(--warning)]/30' : 'bg-[var(--healthy)]/15 text-[var(--healthy)] border-[var(--healthy)]/30'}`}>
            System: {health.message || health.status} • {health.connected_machines} machines
          </span>
        )}
      </div>
      <div className='flex items-center gap-2'>
        <button onClick={toggleFloor} title='Floor display mode scales numbers larger for factory floor' className='p-2 rounded border border-[var(--border)] hover:bg-[var(--surface-hover)]'>
          <Monitor size={16} />
        </button>
        <button onClick={onGlossary} className='inline-flex items-center gap-1 px-2 py-1.5 text-xs rounded border border-[var(--border)] hover:bg-[var(--surface-hover)]'>
          <BookOpen size={14} /> Glossary
        </button>
        <button onClick={onTour} className='inline-flex items-center gap-1 px-2 py-1.5 text-xs rounded border border-[var(--border)] hover:bg-[var(--surface-hover)]'>
          <Play size={14} /> Tour
        </button>
        <button onClick={toggleTheme} aria-label='Toggle theme' className='p-2 rounded border border-[var(--border)] hover:bg-[var(--surface-hover)]'>
          {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>
        {floorMode && <span className='text-[10px] px-1.5 py-0.5 rounded bg-[var(--accent)] text-white'>Floor mode ON</span>}
      </div>
    </header>
  )
}
