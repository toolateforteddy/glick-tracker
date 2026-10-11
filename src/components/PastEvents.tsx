import { ChevronDown, History as HistoryIcon, Trophy } from 'lucide-react'
import { useState } from 'react'
import history from '../data/history.json'
import type { History, PastEvent } from '../types'
import { RoundTable } from './RoundLog'
import { Sprite } from './TeamGrid'

const EVENTS = (history as History).events

export function PastEvents() {
  if (EVENTS.length === 0) return null
  const cuts = EVENTS.filter((e) => e.madeTopCut).length
  const best = Math.min(...EVENTS.map((e) => e.placing ?? Infinity))

  return (
    <section>
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="flex items-center gap-1.5 text-sm font-semibold uppercase tracking-wider text-slate-400">
          <HistoryIcon className="size-4" /> Past Events
        </h2>
        <p className="text-xs text-slate-500">
          {EVENTS.length} events · {cuts} top {cuts === 1 ? 'cut' : 'cuts'}
          {Number.isFinite(best) ? ` · best finish ${ordinal(best)}` : ''}
        </p>
      </div>
      <ul className="space-y-2">
        {EVENTS.map((e) => (
          <EventRow key={e.id} event={e} />
        ))}
      </ul>
    </section>
  )
}

function EventRow({ event: e }: { event: PastEvent }) {
  const [open, setOpen] = useState(false)
  const { w, l, t } = e.record

  return (
    <li className="rounded-3xl border border-slate-800 bg-slate-900">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center gap-3 rounded-3xl px-4 py-3 text-left hover:bg-slate-800/40 sm:px-5"
      >
        <PlacingBadge event={e} />
        <div className="min-w-0 flex-1">
          <div className="font-semibold leading-snug text-slate-100 sm:truncate">{shortName(e.name)}</div>
          <div className="text-xs text-slate-500 sm:truncate">
            {formatDates(e.startDate, e.endDate)}
            {e.location ? ` · ${e.location}` : ''}
            {e.players ? ` · ${e.players.toLocaleString('en-US')} players` : ''}
          </div>
        </div>
        <div className="shrink-0 text-right font-mono text-lg font-bold">
          <span className="text-emerald-400">{w}</span>
          <span className="text-slate-600">-</span>
          <span className="text-rose-400">{l}</span>
          {t > 0 && (
            <>
              <span className="text-slate-600">-</span>
              <span className="text-slate-300">{t}</span>
            </>
          )}
        </div>
        <ChevronDown className={`size-4 shrink-0 text-slate-500 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="grid grid-cols-1 gap-4 border-t border-slate-800 px-4 pb-4 pt-3 sm:px-5 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Team</h3>
            {e.team.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500">Team list not published</p>
            ) : (
              <ul className="mt-2 space-y-1.5">
                {e.team.map((mon, i) => (
                  <li key={`${mon.species}-${i}`} className="flex items-center gap-2.5">
                    <Sprite species={mon.species} className="size-10" />
                    <div className="min-w-0 text-sm">
                      <div className="truncate font-medium text-slate-100">
                        {mon.species}
                        {mon.item && <span className="font-normal text-slate-400"> @ {mon.item}</span>}
                      </div>
                      <div className="truncate text-xs text-slate-500">{mon.moves.join(' · ')}</div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="min-w-0 lg:col-span-3">
            <h3 className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-500">
              Rounds
              <a href={e.url} target="_blank" rel="noreferrer" className="normal-case tracking-normal hover:text-slate-300">
                RK9 ↗
              </a>
            </h3>
            <RoundTable matches={e.matches} showGames={false} />
          </div>
        </div>
      )}
    </li>
  )
}

function PlacingBadge({ event: e }: { event: PastEvent }) {
  const p = e.placing
  const cls =
    p === 1
      ? 'bg-amber-400/20 text-amber-300 ring-amber-400/50'
      : p != null && p <= 4
        ? 'bg-slate-300/15 text-slate-200 ring-slate-300/40'
        : e.madeTopCut
          ? 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/40'
          : 'bg-slate-800 text-slate-400 ring-slate-700'
  return (
    <div
      className={`flex size-12 shrink-0 flex-col items-center justify-center rounded-2xl ring-1 ${cls}`}
      title={e.madeTopCut ? 'Made top cut' : 'Final standing'}
    >
      {p != null && p <= 4 && <Trophy className="size-3.5" />}
      <span className="text-sm font-black leading-tight">{p != null ? ordinal(p) : '—'}</span>
    </div>
  )
}

/** '2027 Baltimore Pokémon Regional Championships' -> '2027 Baltimore Regional Championships'. */
function shortName(name: string): string {
  return name.replace(/\s*Pokémon\s*/, ' ').replace(/\s+VGC\s+/, ' ').trim()
}

function ordinal(n: number): string {
  const s = n % 100 >= 11 && n % 100 <= 13 ? 'th' : ({ 1: 'st', 2: 'nd', 3: 'rd' } as Record<number, string>)[n % 10] ?? 'th'
  return `${n}${s}`
}

function formatDates(start: string, end: string): string {
  const opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric', timeZone: 'UTC' }
  const a = new Date(`${start}T00:00:00Z`)
  const b = new Date(`${end}T00:00:00Z`)
  const year = b.getUTCFullYear()
  return start === end
    ? `${a.toLocaleDateString(undefined, opts)}, ${year}`
    : `${a.toLocaleDateString(undefined, opts)} – ${b.toLocaleDateString(undefined, opts)}, ${year}`
}
