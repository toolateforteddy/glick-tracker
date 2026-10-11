import { HeartHandshake, Play, Tv } from 'lucide-react'
import type { ComponentType } from 'react'

interface Social {
  name: string
  url: string
  cta: string
  blurb: string
  Icon: ComponentType<{ className?: string }>
  tone: string
}

const SOCIALS: Social[] = [
  {
    name: 'YouTube',
    url: 'https://www.youtube.com/@WolfeyVGC?sub_confirmation=1',
    cta: 'Subscribe',
    blurb: 'Team breakdowns, tournament recaps and battles',
    Icon: Play,
    tone: 'bg-red-600 hover:bg-red-500',
  },
  {
    name: 'Patreon',
    url: 'https://www.patreon.com/c/WolfeyVGC',
    cta: 'Become a patron',
    blurb: 'Early teams, tournament prep and early videos',
    Icon: HeartHandshake,
    tone: 'bg-orange-600 hover:bg-orange-500',
  },
  {
    name: 'Twitch',
    url: 'https://www.twitch.tv/wolfeyvgc',
    cta: 'Follow',
    blurb: 'Live streams when he is not at an event',
    Icon: Tv,
    tone: 'bg-purple-600 hover:bg-purple-500',
  },
]

export function Socials() {
  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-400">Socials</h2>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {SOCIALS.map(({ name, url, cta, blurb, Icon, tone }) => (
          <a
            key={name}
            href={url}
            target="_blank"
            rel="noreferrer"
            className="group flex items-center gap-3 rounded-2xl border border-slate-800 bg-slate-900 p-4 transition hover:border-slate-600"
          >
            <span className={`grid size-10 shrink-0 place-items-center rounded-xl text-white transition ${tone}`}>
              <Icon className="size-5" />
            </span>
            <span className="min-w-0">
              <span className="block font-semibold text-slate-100">
                {cta} on {name}
              </span>
              <span className="block text-xs text-slate-400">{blurb}</span>
            </span>
          </a>
        ))}
      </div>
    </section>
  )
}

/** Logo-only links for the page header; the full cards stay at the bottom. */
export function SocialIcons() {
  return (
    <nav aria-label="Wolfe's socials" className="flex items-center gap-1.5 sm:gap-2">
      {SOCIALS.map(({ name, url, cta, Icon, tone }) => (
        <a
          key={name}
          href={url}
          target="_blank"
          rel="noreferrer"
          title={`${cta} on ${name}`}
          aria-label={`${cta} on ${name}`}
          className={`grid size-7 place-items-center rounded-lg text-white transition sm:size-9 sm:rounded-xl ${tone}`}
        >
          <Icon className="size-3.5 sm:size-4" />
        </a>
      ))}
    </nav>
  )
}
