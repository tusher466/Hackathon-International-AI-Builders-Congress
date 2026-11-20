import { useState } from 'react'
import { Copy, Check } from 'lucide-react'

export const CopyButton = ({ text, label='Copy' }) => {
  const [copied, setCopied] = useState(false)
  const handle = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button onClick={handle} className='inline-flex items-center gap-1 px-2 py-1 text-xs border border-[var(--border)] rounded hover:bg-[var(--surface-hover)]'>
      {copied ? <Check size={12} /> : <Copy size={12} />}
      {copied ? 'Copied' : label}
    </button>
  )
}
