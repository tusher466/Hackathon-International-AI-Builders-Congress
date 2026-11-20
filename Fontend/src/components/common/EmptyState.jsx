export const EmptyState = ({ title, description, action, icon }) => {
  return (
    <div className='card p-8 flex flex-col items-center justify-center text-center'>
      {icon && <div className='mb-3 text-[var(--text-muted)]'>{icon}</div>}
      <h3 className='font-semibold text-[var(--text-primary)] mb-1'>{title}</h3>
      <p className='text-sm text-[var(--text-muted)] max-w-md mb-4'>{description}</p>
      {action}
    </div>
  )
}
