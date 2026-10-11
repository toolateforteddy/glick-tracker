import { AlertTriangle, Loader2, RefreshCw } from 'lucide-react'
import { HeroStatus } from './components/HeroStatus'
import { RecordCard } from './components/RecordCard'
import { RoundLog } from './components/RoundLog'
import { RoundTimer } from './components/RoundTimer'
import { Socials } from './components/Socials'
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
      <header className="mb-6 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-3xl font-black tracking-tight sm:text-4xl">
            The Glick Tracker
          </h1>
          <p className="text-sm text-slate-400">Live VGC tournament tracking for Wolfe Glick</p>
        </div>
        {live && data && (
          <div className="flex items-center gap-1.5 text-xs text-slate-500" title={lastFetched?.toLocaleTimeString()}>
            <RefreshCw className="size-3.5" />
            Data updated {formatAgo(data.updatedAt)}
          </div>
        )}
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
        <Socials />
      </div>

      <footer className="mt-10 text-center text-xs text-slate-600">
        Fan-made tracker. Data from {data?.source === 'rk9' ? 'RK9' : 'Limitless VGC'}, sprites from Pokémon Showdown.
      </footer>
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
