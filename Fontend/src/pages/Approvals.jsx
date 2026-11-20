import { PageHeader } from '../layout/PageHeader'
import { useApprovals } from '../hooks/useApprovals'
import { WorkOrderCard } from '../components/agents/WorkOrderCard'
import { EmptyState } from '../components/common/EmptyState'

export const Approvals = () => {
  const { data: pending, isLoading } = useApprovals()

  return (
    <div className='space-y-4'>
      <PageHeader title='Pending Approvals' purpose='Same data as Agent Actions > Pending tab, shown standalone. High-risk AI actions waiting for your decision.' bullets={['Approve moves ticket to In Progress, technician notified','Reject cancels action, system continues monitoring','Comment and decided_by optional but recorded in audit log','Optimistic UI with rollback on error']} />
      {isLoading ? <div className='text-xs'>Loading...</div> : pending?.length===0 ? <EmptyState title='No pending approvals' description='Nothing waiting. High-risk actions like stopping a machine appear here.' /> : (
        <div className='grid grid-cols-1 md:grid-cols-2 gap-3'>
          {pending.map(item => <WorkOrderCard key={item.alert_id} item={item} />)}
        </div>
      )}
    </div>
  )
}
