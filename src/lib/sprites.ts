// Base species whose own names contain a hyphen; everything after the first
// hyphen in other names is a forme (e.g. Urshifu-Rapid-Strike).
const HYPHENATED_BASES = [
  'chien-pao', 'chi-yu', 'ting-lu', 'wo-chien', 'ho-oh', 'porygon-z',
  'jangmo-o', 'hakamo-o', 'kommo-o',
]

const toId = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '')

/** Converts a display species name to a Pokémon Showdown sprite id. */
export function showdownSpriteId(species: string): string {
  const lower = species.trim().toLowerCase()
  const base = HYPHENATED_BASES.find((b) => lower === b || lower.startsWith(`${b}-`))
  if (base) {
    const forme = lower.slice(base.length + 1)
    return forme ? `${toId(base)}-${toId(forme)}` : toId(base)
  }
  const [head, ...rest] = lower.split('-')
  return rest.length ? `${toId(head)}-${toId(rest.join(''))}` : toId(head)
}

export const spriteUrl = (species: string) =>
  `https://play.pokemonshowdown.com/sprites/gen5/${showdownSpriteId(species)}.png`

export const fallbackSpriteUrl = (species: string) =>
  `https://play.pokemonshowdown.com/sprites/dex/${showdownSpriteId(species)}.png`
