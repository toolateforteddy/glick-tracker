import { describe, expect, it } from 'vitest'
import { fallbackSpriteUrl, itemIconPosition, showdownSpriteId, spriteUrl } from './sprites'

describe('showdownSpriteId', () => {
  it.each([
    ['Incineroar', 'incineroar'],
    ['Urshifu-Rapid-Strike', 'urshifu-rapidstrike'],
    ['Ogerpon-Wellspring', 'ogerpon-wellspring'],
    ['Calyrex-Shadow', 'calyrex-shadow'],
    ['Flutter Mane', 'fluttermane'],
    ["Farfetch'd", 'farfetchd'],
    ['Mr. Mime', 'mrmime'],
    ['  Amoonguss ', 'amoonguss'],
  ])('%s -> %s', (species, id) => {
    expect(showdownSpriteId(species)).toBe(id)
  })

  it('keeps hyphenated base species whole', () => {
    expect(showdownSpriteId('Chien-Pao')).toBe('chienpao')
    expect(showdownSpriteId('Ho-Oh')).toBe('hooh')
    expect(showdownSpriteId('Porygon-Z')).toBe('porygonz')
    expect(showdownSpriteId('Kommo-o')).toBe('kommoo')
  })

  it('splits formes off hyphenated base species', () => {
    expect(showdownSpriteId('Ting-Lu-Totem')).toBe('tinglu-totem')
  })
})

describe('sprite urls', () => {
  it('point at Showdown sprite sets', () => {
    expect(spriteUrl('Rillaboom')).toBe('https://play.pokemonshowdown.com/sprites/gen5/rillaboom.png')
    expect(fallbackSpriteUrl('Rillaboom')).toBe('https://play.pokemonshowdown.com/sprites/dex/rillaboom.png')
  })
})

describe('itemIconPosition', () => {
  it('finds an item in the icon sheet by name', () => {
    expect(itemIconPosition('Sceptilite')).toBe('-120px -912px')
    expect(itemIconPosition('Focus Sash')).toBe('-168px -216px')
  })

  it('returns null for unknown or missing items', () => {
    expect(itemIconPosition('Not An Item')).toBeNull()
    expect(itemIconPosition(null)).toBeNull()
  })
})
