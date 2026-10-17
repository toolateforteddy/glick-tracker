import { ExternalLink, Trophy } from 'lucide-react'
import { displayStatus, sourceLink, wolfeOut } from '../lib/status'
import type { TrackerPayload } from '../types'

export function HeroStatus({ data }: { data: TrackerPayload }) {
  const live = data.phase === 'swiss' || data.phase === 'topcut'
  // Once his run is over the round timer goes away, so the way out to the event lives here.
  const link = data.notCompeting
    ? data.tournamentUrl && { href: data.tournamentUrl, label: 'See the event on RK9' }
    : wolfeOut(data) ? sourceLink(data) : null
  return (
    <section className="rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/60 p-5 text-center sm:p-7">
      <div className="flex flex-col items-center gap-1 text-xs font-semibold uppercase tracking-wider text-slate-400">
        <Trophy className="mb-1 size-5 text-amber-400" />
        <div>
          {data.tournamentUrl ? (
            <a href={data.tournamentUrl} target="_blank" rel="noreferrer" className="hover:text-slate-200">
              {data.tournament}
            </a>
          ) : (
            <span>{data.tournament}</span>
          )}
        </div>
        {data.players ? <span className="text-slate-500">{data.players.toLocaleString('en-US')} players</span> : null}
      </div>

      <div className="mt-4 flex flex-col items-center gap-3">
        <span
          className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-lg font-bold sm:text-2xl ${
            live ? 'bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/40' : 'bg-slate-800 text-slate-200'
          }`}
        >
          {live && (
            <span className="relative flex size-2.5">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex size-2.5 rounded-full bg-emerald-400" />
            </span>
          )}
          {data.notCompeting ? "Wolfe isn't competing" : displayStatus(data)}
        </span>
        {data.notCompeting && (
          <p className="max-w-md text-sm text-slate-400">
            We spotted this tournament, but Wolfe isn't on the player list this time. Check back for his next event.
          </p>
        )}
        {link && (
          <a
            href={link.href}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-300 underline-offset-4 hover:text-slate-100 hover:underline"
          >
            <ExternalLink className="size-4" />
            {link.label.replace('live ', '')}
          </a>
        )}
      </div>
    </section>
  )
}
