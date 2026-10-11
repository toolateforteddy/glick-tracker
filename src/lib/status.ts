import type { TrackerPayload } from '../types'

/** Wolfe has no more rounds to play: projected out of top cut, lost in top cut, dropped, or the event ended. */
export function wolfeOut(data: TrackerPayload): boolean {
  if (data.phase === 'finished' || data.status.startsWith('Dropped')) return true
  if (data.topCutStatus === 'eliminated' || (!data.topCutStatus && !data.topCutAlive && data.phase === 'swiss')) return true
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
