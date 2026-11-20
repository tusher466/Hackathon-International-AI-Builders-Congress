import clsx from 'clsx'

export const Badge = ({ children, variant='neutral', className, ...props }) => {
  const variants = {
    neutral: 'bg-[var(--border)] text-[var(--text-primary)]',
    healthy: 'bg-[var(--healthy)]/15 text-[var(--healthy)] border border-[var(--healthy)]/30',
    warning: 'bg-[var(--warning)]/15 text-[var(--warning)] border border-[var(--warning)]/30',
    critical: 'bg-[var(--critical)]/15 text-[var(--critical)] border border-[var(--critical)]/30',
    offline: 'bg-[var(--offline)]/15 text-[var(--offline)] border border-[var(--offline)]/30',
    orange: 'bg-[var(--accent)] text-white',
    steel: 'bg-[var(--steel)]/15 text-[var(--steel)] border border-[var(--border)]',
  }
  return (
    <span className={clsx('inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium font-mono', variants[variant], className)} {...props}>
      {children}
    </span>
  )
}
