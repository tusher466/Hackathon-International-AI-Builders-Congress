import { CheckCircle2, Triangle, Octagon, Minus, Info } from 'lucide-react'
import { statusConfig, severityConfig } from '../../utils/severity'
import clsx from 'clsx'

export const StatusDot = ({ status, size=16 }) => {
  const cfg = statusConfig[status] || { label: status, icon: 'dash', color: 'offline' }
  const colorMap = {
    healthy: 'text-[var(--healthy)]',
    warning: 'text-[var(--warning)]',
    critical: 'text-[var(--critical)]',
    offline: 'text-[var(--offline)]',
  }
  const Icon = cfg.icon === 'check' ? CheckCircle2 : cfg.icon === 'triangle' ? Triangle : cfg.icon === 'octagon' ? Octagon : Minus
  return (
    <span className={clsx('inline-flex items-center gap-1.5', colorMap[cfg.color])} title={cfg.label}>
      <Icon size={size} />
      <span className='text-xs font-medium'>{cfg.label}</span>
    </span>
  )
}

export const SeverityBadge = ({ severity }) => {
  const cfg = severityConfig[severity] || { label: severity, icon: 'info', color: 'text-offline' }
  const Icon = cfg.icon === 'check' ? CheckCircle2 : cfg.icon === 'triangle' ? Triangle : cfg.icon === 'octagon' ? Octagon : Info
  const colorCls = severity === 'critical' ? 'bg-[var(--critical)]/15 text-[var(--critical)] border-[var(--critical)]/30' : severity === 'high' || severity === 'medium' ? 'bg-[var(--warning)]/15 text-[var(--warning)] border-[var(--warning)]/30' : severity === 'low' ? 'bg-[var(--offline)]/15 text-[var(--offline)] border-[var(--border)]' : 'bg-[var(--border)] text-[var(--text-primary)]'
  return (
    <span className={clsx('inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border', colorCls)}>
      <Icon size={12} />
      {cfg.label}
    </span>
  )
}
