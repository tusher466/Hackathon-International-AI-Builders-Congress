import { useEffect, useRef, useState } from 'react'
import { getWsUrl, isMockMode } from '../api/client'
import { MockSocket } from '../api/mock/mockServer'
import { useLiveStore } from '../store/liveStore'

export const useLiveSocket = () => {
  const [status, setStatus] = useState('connecting') // live, reconnecting, offline
  const [isDemo, setIsDemo] = useState(false)
  const store = useLiveStore()
  const wsRef = useRef(null)
  const mockRef = useRef(null)
  const retryRef = useRef(0)
  const timerRef = useRef(null)

  useEffect(() => {
    const useMock = isMockMode()
    if (useMock) {
      setIsDemo(true)
      setStatus('live')
      const mock = new MockSocket((msg) => {
        store.dispatch(msg)
      })
      mockRef.current = mock
      mock.start()
      return () => mock.stop()
    }

    const connect = () => {
      const url = getWsUrl()
      try {
        const ws = new WebSocket(url)
        wsRef.current = ws
        setStatus('connecting')

        ws.onopen = () => {
          setStatus('live')
          retryRef.current = 0
          setIsDemo(false)
        }
        ws.onmessage = (ev) => {
          try {
            const data = JSON.parse(ev.data)
            store.dispatch(data)
          } catch {}
        }
        ws.onclose = () => {
          setStatus('reconnecting')
          // fallback to mock after 3 retries
          if (retryRef.current >= 3) {
            setIsDemo(true)
            setStatus('live')
            const mock = new MockSocket((msg) => store.dispatch(msg))
            mockRef.current = mock
            mock.start()
            return
          }
          const backoff = Math.min(1000 * Math.pow(2, retryRef.current), 10000)
          retryRef.current++
          timerRef.current = setTimeout(connect, backoff)
        }
        ws.onerror = () => {
          ws.close()
        }
      } catch {
        setIsDemo(true)
        setStatus('live')
        const mock = new MockSocket((msg) => store.dispatch(msg))
        mockRef.current = mock
        mock.start()
      }
    }

    connect()

    return () => {
      if (wsRef.current) wsRef.current.close()
      if (mockRef.current) mockRef.current.stop()
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  return { status, isDemo, mockSocket: mockRef.current }
}
