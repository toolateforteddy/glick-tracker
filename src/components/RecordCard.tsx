import { ShieldCheck, ShieldQuestion, ShieldX } from 'lucide-react'
import type { TopCutStatus, TrackerPayload } from '../types'

const CUT_STYLES: Record<TopCutStatus, { label: string; cls: string; Icon: typeof ShieldCheck }> = {
  alive: { label: 'Alive', cls: 'bg-amber-500/15 text-amber-300 ring-amber-500/40', Icon: ShieldQuestion },
  bubble: { label: 'Must Win Out', cls: 'bg-orange-500/15 text-orange-300 ring-orange-500/40', Icon: ShieldQuestion },
  clinched: { label: 'Cut Clinched', cls: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/40', Icon: ShieldCheck },
  eliminated: { label: 'Eliminated', cls: 'bg-rose-500/15 text-rose-300 ring-rose-500/40', Icon: ShieldX },
}

export function RecordCard({ data }: { data: TrackerPayload }) {
  const { w, l, t = 0 } = data.record
  const cut: TopCutStatus = data.topCutStatus ?? (data.topCutAlive ? 'alive' : 'eliminated')
  const { label, cls, Icon } = CUT_STYLES[cut]

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-900 p-5 sm:p-6">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Record &amp; Standing</h2>
      <div className="mt-3 font-mono text-5xl font-black tracking-tight sm:text-6xl">
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

      <dl className="mt-5 grid grid-cols-2 gap-3">
        <Stat label={data.source === 'rk9' ? 'Rank (by points)' : 'Rank'} value={data.standing != null ? `#${data.standing}` : '—'} />
        <Stat label="OPW%" value={data.opw != null ? `${data.opw.toFixed(2)}%` : '—'} />
      </dl>

      <div className={`mt-5 flex items-center gap-2 rounded-2xl px-4 py-3 ring-1 ${cls}`}>
        <Icon className="size-5 shrink-0" />
        <div>
          <div className="font-bold">{label}</div>
          {data.topCutSize ? (
            <div className="text-xs opacity-80">
              {data.source === 'rk9' ? 'Projected: t' : 'T'}op {data.topCutSize} cut
              {data.swissRounds ? ` after ${data.swissRounds} Swiss rounds` : ''}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-slate-800/60 px-4 py-3">
      <dt className="text-xs uppercase tracking-wider text-slate-400">{label}</dt>
      <dd className="mt-1 text-2xl font-bold">{value}</dd>
    </div>
  )
}
