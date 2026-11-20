import clsx from 'clsx'

export const Card = ({ children, className, hover=false, ...props }) => {
  return (
    <div className={clsx('card p-4', hover && 'hover:border-[var(--border-hover)] transition-colors', className)} {...props}>
      {children}
    </div>
  )
}
