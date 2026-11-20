export const severityConfig = {
  low: { label: 'Low - Watch', icon: 'info', color: 'text-offline' },
  medium: { label: 'Medium - Needs attention', icon: 'triangle', color: 'text-warning' },
  high: { label: 'High - Act soon', icon: 'triangle', color: 'text-warning' },
  critical: { label: 'Needs action now', icon: 'octagon', color: 'text-critical' },
}

export const statusConfig = {
  healthy: { label: 'Running well', icon: 'check', color: 'healthy' },
  warning: { label: 'Needs attention', icon: 'triangle', color: 'warning' },
  critical: { label: 'Needs action now', icon: 'octagon', color: 'critical' },
  offline: { label: 'No data', icon: 'dash', color: 'offline' },
}

export const alertStatusConfig = {
  detected: 'Detected',
  diagnosed: 'Diagnosed',
  planned: 'Plan ready',
  awaiting_approval: 'Awaiting approval',
  ticketed: 'Work order created',
  open: 'Open',
  in_progress: 'In progress',
  resolved: 'Resolved',
  rejected: 'Rejected',
  needs_human_review: 'Needs human review',
}

export const ticketStatusConfig = {
  open: { label: 'Open', desc: 'Ticket created, not started yet' },
  awaiting_approval: { label: 'Awaiting approval', desc: 'AI proposed action, waiting for human decision' },
  in_progress: { label: 'In progress', desc: 'Technician is working on it' },
  resolved: { label: 'Resolved', desc: 'Fix completed and verified' },
  rejected: { label: 'Rejected', desc: 'Human rejected the proposed action' },
  needs_human_review: { label: 'Needs human review', desc: 'The AI was not confident enough, a person must check' },
}
