import moveTypes from '../data/move-types.json'

const TYPE_COLORS: Record<string, string> = {
  normal: 'bg-stone-400 text-stone-950',
  fire: 'bg-orange-500 text-orange-950',
  water: 'bg-blue-500 text-blue-50',
  electric: 'bg-yellow-400 text-yellow-950',
  grass: 'bg-green-500 text-green-950',
  ice: 'bg-cyan-300 text-cyan-950',
  fighting: 'bg-red-700 text-red-50',
  poison: 'bg-purple-500 text-purple-50',
  ground: 'bg-amber-600 text-amber-50',
  flying: 'bg-indigo-300 text-indigo-950',
  psychic: 'bg-pink-500 text-pink-50',
  bug: 'bg-lime-500 text-lime-950',
  rock: 'bg-yellow-700 text-yellow-50',
  ghost: 'bg-violet-700 text-violet-50',
  dragon: 'bg-indigo-600 text-indigo-50',
  dark: 'bg-stone-700 text-stone-50',
  steel: 'bg-slate-400 text-slate-950',
  fairy: 'bg-pink-300 text-pink-950',
  stellar: 'bg-gradient-to-r from-sky-400 via-fuchsia-400 to-amber-300 text-slate-950',
}

export const teraClass = (type: string | null) =>
  (type && TYPE_COLORS[type.toLowerCase()]) || 'bg-slate-700 text-slate-100'

// Tinted rather than solid so eight pills per card stay calm on the dark theme.
const MOVE_COLORS: Record<string, string> = {
  bug: 'bg-lime-500/20 text-lime-100 ring-1 ring-inset ring-lime-500/50',
  dark: 'bg-neutral-500/20 text-neutral-100 ring-1 ring-inset ring-neutral-500/50',
  dragon: 'bg-indigo-500/20 text-indigo-100 ring-1 ring-inset ring-indigo-500/50',
  electric: 'bg-yellow-400/20 text-yellow-100 ring-1 ring-inset ring-yellow-400/50',
  fairy: 'bg-pink-300/20 text-pink-100 ring-1 ring-inset ring-pink-300/50',
  fighting: 'bg-red-600/20 text-red-100 ring-1 ring-inset ring-red-600/50',
  fire: 'bg-orange-500/20 text-orange-100 ring-1 ring-inset ring-orange-500/50',
  flying: 'bg-sky-400/20 text-sky-100 ring-1 ring-inset ring-sky-400/50',
  ghost: 'bg-violet-500/20 text-violet-100 ring-1 ring-inset ring-violet-500/50',
  grass: 'bg-green-500/20 text-green-100 ring-1 ring-inset ring-green-500/50',
  ground: 'bg-amber-600/20 text-amber-100 ring-1 ring-inset ring-amber-600/50',
  ice: 'bg-cyan-300/20 text-cyan-100 ring-1 ring-inset ring-cyan-300/50',
  normal: 'bg-stone-400/20 text-stone-100 ring-1 ring-inset ring-stone-400/50',
  poison: 'bg-purple-500/20 text-purple-100 ring-1 ring-inset ring-purple-500/50',
  psychic: 'bg-pink-500/20 text-pink-100 ring-1 ring-inset ring-pink-500/50',
  rock: 'bg-yellow-700/20 text-yellow-100 ring-1 ring-inset ring-yellow-700/50',
  steel: 'bg-slate-400/20 text-slate-100 ring-1 ring-inset ring-slate-400/50',
  water: 'bg-blue-500/20 text-blue-100 ring-1 ring-inset ring-blue-500/50',
}

const MOVE_TYPES: Record<string, string> = moveTypes

/** The type colour for a move pill, or the neutral pill style for a move we don't know. */
export const moveClass = (move: string) => {
  const type = MOVE_TYPES[move]
  return (type && MOVE_COLORS[type.toLowerCase()]) || 'bg-slate-800/70 text-slate-200'
}
