export const formatNumber = (num, decimals = 1) => {
  if (num == null || isNaN(num)) return '—'
  return Number(num).toFixed(decimals)
}

export const formatPercent = (value, decimals = 1) => {
  if (value == null) return '—'
  const pct = value <= 1 ? value * 100 : value
  return `${pct.toFixed(decimals)}%`
}

export const formatRelativeTime = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso)
  const now = new Date()
  const diff = now - d
  const s = Math.floor(diff / 1000)
  if (s < 60) return `${s}s ago`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  const days = Math.floor(h / 24)
  if (days < 7) return `${days}d ago`
  return d.toLocaleDateString()
}

export const formatAbsoluteTime = (iso) => {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

export const formatId = (id) => {
  if (!id) return '—'
  return id
}

export const formatMachineType = (type) => {
  const map = {
    secom: 'Semiconductor process (SECOM)',
    turbofan: 'Turbofan engine',
    bosch: 'Assembly line (Bosch)',
  }
  return map[type] || type
}

export const formatSensorValue = (val, unit = '') => {
  if (val == null) return '—'
  const n = typeof val === 'number' ? val.toFixed(2) : val
  return `${n}${unit ? ' ' + unit : ''}`
}
