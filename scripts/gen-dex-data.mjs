// Writes the small lookup tables the Team Sheet bundles, so nothing is fetched at runtime:
//   src/data/move-types.json   move name -> type, for colouring move pills
//   src/data/item-sprites.json item id -> index in Showdown's item icon sheet
// Run `npm run gen:dex` after bumping @pkmn/dex or @pkmn/img to pick up new moves and items.
import { writeFileSync } from 'node:fs'
import { Dex } from '@pkmn/dex'
import { Icons } from '@pkmn/img'

const sorted = (obj) => Object.fromEntries(Object.entries(obj).sort(([a], [b]) => a.localeCompare(b)))
const write = (name, obj) => {
  writeFileSync(new URL(`../src/data/${name}`, import.meta.url), JSON.stringify(sorted(obj)) + '\n')
  console.log(`${name}: ${Object.keys(obj).length} entries`)
}

const moves = {}
for (const move of Dex.moves.all()) {
  if (!move.isNonstandard || move.isNonstandard === 'Past') moves[move.name] = move.type
}
write('move-types.json', moves)

// The sheet is 16 icons of 24px per row; index 0 is the "no item" icon, so it's left out.
const items = {}
for (const item of Dex.items.all()) {
  const { top, left } = Icons.getItem(item.name)
  const index = (-top / 24) * 16 + -left / 24
  if (index > 0) items[item.id] = index
}
write('item-sprites.json', items)
