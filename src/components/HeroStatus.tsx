import { Radio, Trophy, Tv } from 'lucide-react'
import type { TrackerPayload } from '../types'

export function HeroStatus({ data }: { data: TrackerPayload }) {
  const live = data.phase === 'swiss' || data.phase === 'topcut'
  return (
    <section className="rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/60 p-5 sm:p-7">
      <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
        <Trophy className="size-4 text-amber-400" />
        {data.tournamentUrl ? (
          <a href={data.tournamentUrl} target="_blank" rel="noreferrer" className="hover:text-slate-200">
            {data.tournament}
          </a>
        ) : (
          <span>{data.tournament}</span>
        )}
        {data.players ? <span className="text-slate-500">· {data.players} players</span> : null}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
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
          {data.status}
        </span>

        {data.stream && (
          <a
            href={data.stream}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-full bg-purple-600 px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-purple-500"
          >
            {live ? <Radio className="size-4" /> : <Tv className="size-4" />}
            Watch stream
          </a>
        )}
      </div>
    </section>
  )
}
