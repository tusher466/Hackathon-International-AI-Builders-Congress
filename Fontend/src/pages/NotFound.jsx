import { Link } from 'react-router-dom'
import { PageHeader } from '../layout/PageHeader'

export const NotFound = () => {
  return (
    <div className='space-y-4'>
      <PageHeader title='404 - Page not found' purpose='The page you tried does not exist. Use navigation to go to a valid area.' bullets={['Sidebar has all valid routes','Overview is the main entry','Check URL spelling']} />
      <div className='text-sm'><Link to='/' className='text-[var(--accent)] underline'>Go to Overview (Command Center)</Link></div>
    </div>
  )
}
