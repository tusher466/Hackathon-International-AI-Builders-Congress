import { Card } from '../common/Card'

export const ReasoningBlock = ({ reasoning }) => {
  return (
    <Card className='p-4'>
      <h4 className='text-sm font-medium mb-2'>Reasoning (how AI decided)</h4>
      <p className='text-sm text-[var(--text-muted)] leading-relaxed'>{reasoning || 'No reasoning provided'}</p>
    </Card>
  )
}
