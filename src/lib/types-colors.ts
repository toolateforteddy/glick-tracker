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
