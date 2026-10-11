import { AlertTriangle, Loader2, RefreshCw } from 'lucide-react'
import { HeroStatus } from './components/HeroStatus'
import { PastEvents } from './components/PastEvents'
import { RecordCard } from './components/RecordCard'
import { RoundLog } from './components/RoundLog'
import { RoundTimer } from './components/RoundTimer'
import { SocialIcons, Socials } from './components/Socials'
import { TeamGrid } from './components/TeamGrid'
import { usePolling } from './lib/usePolling'

const DEFAULT_GIST_RAW_URL =
  'https://gist.githubusercontent.com/toolateforteddy/f63b15c0e419f0d8cd3bdce9ceb01372/raw/glick_live.json'

// `?demo` loads the bundled sample payload so the UI can be previewed off-season.
const DATA_URL = new URLSearchParams(window.location.search).has('demo')
  ? './demo.json'
  : import.meta.env.VITE_GIST_RAW_URL || DEFAULT_GIST_RAW_URL

export default function App() {
  const { data, error, lastFetched } = usePolling(DATA_URL)
  // The gist starts out as a placeholder until the sync job writes its first payload.
  const live = Boolean(data?.record && Array.isArray(data.matches))

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:py-10">
      <header className="mb-6 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-3xl font-black tracking-tight sm:text-4xl">
            The Glick Tracker
          </h1>
          <p className="text-sm text-slate-400">Live VGC tournament tracking for Wolfe Glick</p>
          {live && data && <Updated at={data.updatedAt} fetched={lastFetched} className="mt-2 sm:hidden" />}
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2 pt-1 sm:pt-0">
          <SocialIcons />
          {live && data && <Updated at={data.updatedAt} fetched={lastFetched} className="hidden sm:flex" />}
        </div>
      </header>

      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-2xl bg-rose-500/10 px-4 py-2 text-sm text-rose-300 ring-1 ring-rose-500/30">
          <AlertTriangle className="size-4 shrink-0" />
          Couldn't refresh tracker data ({error}). {data ? 'Showing the last update.' : 'Retrying every 30s.'}
        </div>
      )}

      {!data ? (
        !error && (
          <div className="flex items-center justify-center gap-2 py-24 text-slate-400">
            <Loader2 className="size-5 animate-spin" /> Loading tracker…
          </div>
        )
      ) : !live ? (
        <div className="rounded-3xl border border-dashed border-slate-800 py-20 text-center text-slate-400">
          No tournament data yet. This fills in once Wolfe's next event is picked up.
        </div>
      ) : (
        <main className="space-y-4">
          <HeroStatus data={data} />
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <div className="min-w-0 space-y-4 lg:col-span-1">
              <RecordCard data={data} />
              <RoundTimer data={data} />
            </div>
            <div className="min-w-0 lg:col-span-2">
              <RoundLog matches={data.matches} />
            </div>
          </div>
          <TeamGrid team={data.team ?? []} />
        </main>
      )}

      <div className="mt-8">
        <PastEvents />
      </div>

      <div className="mt-8">
        <Socials />
      </div>

      <footer className="mt-10 text-center text-xs text-slate-600">
        Fan-made tracker. Pairings and results come from{' '}
        <a href="https://rk9.gg" target="_blank" rel="noreferrer" className="text-slate-400 underline hover:text-slate-200">
          RK9
        </a>{' '}
        and{' '}
        <a href="https://limitlessvgc.com" target="_blank" rel="noreferrer" className="text-slate-400 underline hover:text-slate-200">
          Limitless VGC
        </a>
        {data?.tournamentUrl && (
          <>
            {' '}(
            <a href={data.tournamentUrl} target="_blank" rel="noreferrer" className="text-slate-400 underline hover:text-slate-200">
              this event on {data.source === 'rk9' ? 'RK9' : 'Limitless'}
            </a>
            )
          </>
        )}
        . Sprites from Pokémon Showdown.
      </footer>
    </div>
  )
}

function Updated({ at, fetched, className }: { at: string; fetched: Date | null; className: string }) {
  return (
    <div className={`flex items-center gap-1.5 text-xs text-slate-500 ${className}`} title={fetched?.toLocaleTimeString()}>
      <RefreshCw className="size-3.5" />
      Data updated {formatAgo(at)}
    </div>
  )
}

function formatAgo(iso: string): string {
  const diff = Math.round((Date.now() - Date.parse(iso)) / 1000)
  if (!Number.isFinite(diff)) return 'unknown'
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return new Date(iso).toLocaleDateString()
}
