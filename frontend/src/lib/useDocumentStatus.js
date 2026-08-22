import { useState, useEffect, useRef } from 'react'
import { getDocumentStatus } from '../lib/api'

/**
 * Polls GET /documents/{fileId}/status every `intervalMs` until the
 * document reaches a terminal state ("done" or "failed"), then stops.
 *
 * WHY POLLING INSTEAD OF A WEBSOCKET: the backend's upload endpoint is
 * fire-and-forget (a FastAPI BackgroundTask - see backend/routers/upload.py),
 * with no push mechanism back to the client. Polling is the simplest
 * correct approach for that design. A websocket/SSE upgrade would be
 * a reasonable future improvement, but isn't needed at this scale.
 */
export function useDocumentStatus(fileId, { intervalMs = 2500 } = {}) {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [pollError, setPollError] = useState(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    if (!fileId) return

    setLoading(true)
    setStatus(null)
    setPollError(null)

    const poll = async () => {
      try {
        const data = await getDocumentStatus(fileId)
        setStatus(data)
        setLoading(false)
        if (data.processing_status === 'done' || data.processing_status === 'failed') {
          clearInterval(intervalRef.current)
        }
      } catch (err) {
        setPollError(err)
        setLoading(false)
        clearInterval(intervalRef.current)
      }
    }

    poll() // fire immediately, don't wait for the first interval tick
    intervalRef.current = setInterval(poll, intervalMs)

    return () => clearInterval(intervalRef.current)
  }, [fileId, intervalMs])

  return { status, loading, pollError }
}
