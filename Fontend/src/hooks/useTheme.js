import { useState, useEffect } from 'react'

export const useTheme = () => {
  const [theme, setTheme] = useState(() => {
    const stored = localStorage.getItem('factory-brain-theme')
    if (stored) return stored
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    return prefersDark ? 'dark' : 'dark' // default dark per spec
  })
  const [floorMode, setFloorMode] = useState(() => {
    return localStorage.getItem('factory-brain-floor') === 'true'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('factory-brain-theme', theme)
  }, [theme])

  useEffect(() => {
    localStorage.setItem('factory-brain-floor', floorMode)
    if (floorMode) {
      document.body.classList.add('floor-mode')
    } else {
      document.body.classList.remove('floor-mode')
    }
  }, [floorMode])

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark')
  const toggleFloor = () => setFloorMode(f => !f)

  return { theme, toggleTheme, floorMode, toggleFloor }
}
