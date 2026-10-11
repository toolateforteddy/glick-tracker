// Writes src/data/move-types.json (move name -> type) from @pkmn/dex for colouring move pills.
// Run `npm run gen:moves` after bumping @pkmn/dex to pick up new moves.
import { writeFileSync } from 'node:fs'
import { Dex } from '@pkmn/dex'

const types = {}
for (const move of Dex.moves.all()) {
  if (!move.isNonstandard || move.isNonstandard === 'Past') types[move.name] = move.type
}
const sorted = Object.fromEntries(Object.entries(types).sort(([a], [b]) => a.localeCompare(b)))
writeFileSync(new URL('../src/data/move-types.json', import.meta.url), JSON.stringify(sorted, null, 0) + '\n')
console.log(`${Object.keys(sorted).length} moves`)
