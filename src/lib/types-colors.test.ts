import { describe, expect, it } from 'vitest'
import { moveClass, teraClass } from './types-colors'

const FALLBACK = 'bg-slate-700 text-slate-100'

describe('teraClass', () => {
  it('maps tera types case-insensitively', () => {
    expect(teraClass('Fire')).toBe('bg-orange-500 text-orange-950')
    expect(teraClass('GHOST')).toBe(teraClass('ghost'))
  })

  it('falls back for unknown or missing types', () => {
    expect(teraClass(null)).toBe(FALLBACK)
    expect(teraClass('')).toBe(FALLBACK)
    expect(teraClass('Shadow')).toBe(FALLBACK)
  })
})

describe('moveClass', () => {
  it('colours a move by its type', () => {
    expect(moveClass('Dragon Pulse')).toContain('bg-indigo-500/20')
    expect(moveClass('Knock Off')).toContain('bg-neutral-500/20')
    expect(moveClass('Protect')).toBe(moveClass('Follow Me'))
  })

  it('keeps the neutral pill for unknown moves', () => {
    expect(moveClass('Not A Move')).toBe('bg-slate-800/70 text-slate-200')
  })
})
