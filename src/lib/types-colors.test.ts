import { describe, expect, it } from 'vitest'
import { teraClass } from './types-colors'

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
