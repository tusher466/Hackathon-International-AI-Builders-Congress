import clsx from 'clsx'

export const Skeleton = ({ className, ...props }) => {
  return <div className={clsx('skeleton rounded', className)} {...props} />
}

export const SkeletonCard = () => {
  return (
    <div className='card p-4 space-y-3'>
      <Skeleton className='h-4 w-1/2' />
      <Skeleton className='h-8 w-3/4' />
      <Skeleton className='h-20 w-full' />
    </div>
  )
}
