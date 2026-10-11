import { ExternalLink, Hourglass, Timer } from 'lucide-react'
import type { ReactNode } from 'react'
import { sourceLink, wolfeOut } from '../lib/status'
import { useNow } from '../lib/usePolling'
import type { TrackerPayload } from '../types'

// After this long a Bo3 has almost certainly ended; the slip just isn't in yet.
const STALE_AFTER_MIN = 75

export function RoundTimer({ data }: { data: TrackerPayload }) {
  const now = useNow(1000)
  const link = sourceLink(data)
  const started = data.roundStartedAt ? Date.parse(data.roundStartedAt) : NaN
  const elapsedMs = now - started
  const showTimer =
    data.currentMatchPending !== false && Number.isFinite(started) && elapsedMs >= 0 && elapsedMs < STALE_AFTER_MIN * 60_000

  // No more rounds for him to time; the hero card carries the link to the event instead.
  if (wolfeOut(data)) return null

  if (!data.currentMatchPending && data.phase !== 'swiss' && data.phase !== 'topcut') {
    return (
      <Shell link={link}>
        <Hourglass className="size-6 text-slate-500" />
        <div className="text-slate-400">No active round</div>
      </Shell>
    )
  }

  if (data.currentMatchPending === false) {
    // His match this round is reported (or a bye); the next pairings aren't up yet.
    const bye = data.matches?.at(-1)?.result === 'BYE'
    return (
      <Shell link={link}>
        <Hourglass className="size-6 text-slate-500" />
        <div className="text-slate-300">
          {bye ? 'Bye this round' : 'Match finished'} - waiting for the next round
        </div>
      </Shell>
    )
  }

  if (!showTimer) {
    return (
      <Shell link={link}>
        <Hourglass className="size-6 animate-pulse text-amber-400" />
        <div className="font-semibold text-amber-200">Match in progress</div>
      </Shell>
    )
  }

  const totalSec = Math.floor(elapsedMs / 1000)
  const mm = Math.floor(totalSec / 60)
  const ss = String(totalSec % 60).padStart(2, '0')
  return (
    <Shell link={link}>
      <Timer className="size-6 text-sky-400" />
      <div>
        <div className="font-mono text-3xl font-bold tabular-nums">
          {mm}:{ss}
        </div>
        <div className="text-xs text-slate-400">since the round started</div>
      </div>
    </Shell>
  )
}

function Shell({ children, link }: { children: ReactNode; link: { href: string; label: string } | null }) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900 p-5 sm:p-6">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Round Timer</h2>
      <div className="mt-3 flex items-center gap-3">{children}</div>
      {link && <LinkButton link={link} className="mt-4" />}
    </section>
  )
}

function LinkButton({ link, className = '' }: { link: { href: string; label: string }; className?: string }) {
  return (
    <a
      href={link.href}
      target="_blank"
      rel="noreferrer"
      className={`inline-flex items-center gap-1.5 rounded-full bg-slate-800 px-3 py-1.5 text-sm font-semibold text-slate-200 transition hover:bg-slate-700 ${className}`}
    >
      <ExternalLink className="size-4" />
      {link.label}
    </a>
  )
}
