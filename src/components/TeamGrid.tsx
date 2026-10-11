import { CircleDot } from 'lucide-react'
import { useState } from 'react'
import { fallbackSpriteUrl, spriteUrl } from '../lib/sprites'
import { teraClass } from '../lib/types-colors'
import type { TeamMember } from '../types'

export function TeamGrid({ team }: { team: TeamMember[] }) {
  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">Team Sheet</h2>
      {team.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-slate-800 p-6 text-center text-slate-500">
          Team list not published yet
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {team.map((mon, i) => (
            <PokemonCard key={`${mon.species}-${i}`} mon={mon} />
          ))}
        </div>
      )}
    </section>
  )
}

export function Sprite({ species, className = 'size-20' }: { species: string; className?: string }) {
  const [stage, setStage] = useState(0)
  if (stage > 1) {
    return (
      <div className={`flex ${className} items-center justify-center rounded-2xl bg-slate-800`}>
        <CircleDot className="size-8 text-slate-600" />
      </div>
    )
  }
  return (
    <img
      src={stage === 0 ? spriteUrl(species) : fallbackSpriteUrl(species)}
      alt={species}
      loading="lazy"
      onError={() => setStage((s) => s + 1)}
      className={`sprite ${className} shrink-0 rounded-2xl bg-slate-800/60 object-contain`}
    />
  )
}

function PokemonCard({ mon }: { mon: TeamMember }) {
  return (
    <article className="rounded-3xl border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-start gap-3">
        <Sprite species={mon.species} />
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="truncate text-lg font-bold">{mon.species}</h3>
            {mon.tera && (
              <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-bold ${teraClass(mon.tera)}`}>
                Tera {mon.tera}
              </span>
            )}
          </div>
          <dl className="mt-1 space-y-0.5 text-sm">
            <div className="flex gap-1.5">
              <dt className="text-slate-500">@</dt>
              <dd className="truncate text-slate-200">{mon.item || '—'}</dd>
            </div>
            <div className="flex gap-1.5">
              <dt className="text-slate-500">Ability</dt>
              <dd className="truncate text-slate-200">{mon.ability || '—'}</dd>
            </div>
            {mon.nature && (
              <div className="flex gap-1.5">
                <dt className="text-slate-500">Nature</dt>
                <dd className="truncate text-slate-200">{mon.nature}</dd>
              </div>
            )}
          </dl>
        </div>
      </div>
      <ul className="mt-3 grid grid-cols-2 gap-1.5">
        {Array.from({ length: 4 }, (_, i) => mon.moves[i]).map((move, i) => (
          <li key={i} className="truncate rounded-xl bg-slate-800/70 px-2.5 py-1.5 text-sm text-slate-200">
            {move || <span className="text-slate-600">—</span>}
          </li>
        ))}
      </ul>
    </article>
  )
}
