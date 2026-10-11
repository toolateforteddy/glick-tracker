import { describe, expect, it } from 'vitest'
import { fallbackSpriteUrl, showdownSpriteId, spriteUrl } from './sprites'

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
