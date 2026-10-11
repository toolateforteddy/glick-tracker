import { useEffect, useState } from 'react'
import type { TrackerPayload } from '../types'

const POLL_MS = 30_000

export interface PollState {
  data: TrackerPayload | null
  error: string | null
  lastFetched: Date | null
}

export function usePolling(url: string): PollState {
  const [state, setState] = useState<PollState>({ data: null, error: null, lastFetched: null })

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const sep = url.includes('?') ? '&' : '?'
        const res = await fetch(`${url}${sep}t=${Date.now()}`, { cache: 'no-store' })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = (await res.json()) as TrackerPayload
        if (!cancelled) setState({ data, error: null, lastFetched: new Date() })
      } catch (err) {
        // Keep showing the last good payload; just surface the error.
        if (!cancelled) setState((s) => ({ ...s, error: String(err), lastFetched: new Date() }))
      }
    }

    load()
    const id = window.setInterval(load, POLL_MS)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [url])

  return state
}

export function useNow(intervalMs = 1000): number {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), intervalMs)
    return () => window.clearInterval(id)
  }, [intervalMs])
  return now
}
