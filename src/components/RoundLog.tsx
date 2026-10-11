import type { MatchResult, MatchRow } from '../types'

const PILL: Record<MatchResult, { label: string; cls: string }> = {
  W: { label: 'Win', cls: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/40' },
  L: { label: 'Loss', cls: 'bg-rose-500/15 text-rose-300 ring-rose-500/40' },
  T: { label: 'Tie', cls: 'bg-slate-500/15 text-slate-300 ring-slate-500/40' },
  BYE: { label: 'Bye', cls: 'bg-sky-500/15 text-sky-300 ring-sky-500/40' },
}

export function RoundLog({ matches }: { matches: MatchRow[] }) {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900 p-5 sm:p-6">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Round Log</h2>
      {matches.length === 0 ? (
        <p className="mt-3 text-slate-500">No rounds played yet</p>
      ) : (
        <RoundTable matches={matches} showGames={matches.some((m) => m.score)} />
      )}
    </section>
  )
}

/** Wolfe's matches, Swiss first then top cut. */
export function RoundTable({ matches, showGames = true }: { matches: MatchRow[]; showGames?: boolean }) {
  const rows = [...matches].sort((a, b) =>
    a.phase === b.phase ? a.round - b.round : a.phase === 'swiss' ? -1 : 1,
  )
  return (
    <div className="-mx-2 mt-3 overflow-x-auto">
      <table className="w-full min-w-[18rem] text-left text-sm">
        <thead className="text-xs uppercase tracking-wider text-slate-500">
          <tr>
            <th className="px-2 py-2 font-semibold">Round</th>
            <th className="px-2 py-2 font-semibold">Opponent</th>
            {showGames && <th className="px-2 py-2 text-center font-semibold">Score</th>}
            <th className="px-2 py-2 text-right font-semibold">Result</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {rows.map((m) => (
            <tr key={`${m.phase}-${m.round}`}>
              <td className="px-2 py-2.5 font-mono text-slate-400">{m.label}</td>
              <td className="px-2 py-2.5">
                <div className="font-medium text-slate-100">{m.opponent ?? (m.result === 'BYE' ? 'Bye' : 'TBD')}</div>
              </td>
              {showGames && <td className="px-2 py-2.5 text-center font-mono text-slate-300">{m.score ?? '—'}</td>}
              <td className="px-2 py-2.5 text-right">
                {m.result ? (
                  <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-bold ring-1 ${PILL[m.result].cls}`}>
                    {PILL[m.result].label}
                  </span>
                ) : (
                  <span className="inline-block rounded-full bg-amber-500/15 px-2.5 py-0.5 text-xs font-bold text-amber-300 ring-1 ring-amber-500/40">
                    Live
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
