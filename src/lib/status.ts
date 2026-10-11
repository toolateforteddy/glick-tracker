import type { TrackerPayload } from '../types'

/**
 * Wolfe has actually left the event: a cut went up without him or the event ended (the sync marks
 * both as finished), he dropped, or he lost in top cut. Being projected out isn't enough.
 */
export function wolfeOut(data: TrackerPayload): boolean {
  if (data.phase === 'finished' || data.status.startsWith('Dropped')) return true
  const cut = data.matches.filter((m) => m.phase === 'topcut')
  return data.phase === 'topcut' && cut.at(-1)?.result === 'L'
}

/** Where viewers can check the event themselves; our data lags by design since we poll gently. */
export function sourceLink(data: TrackerPayload): { href: string; label: string } | null {
  if (data.source === 'rk9' && data.tournamentId) {
    return { href: `https://rk9.gg/pairings/${data.tournamentId}`, label: 'View live pairings on RK9' }
  }
  if (data.tournamentUrl) return { href: data.tournamentUrl, label: 'View live standings on Limitless' }
  return null
}
