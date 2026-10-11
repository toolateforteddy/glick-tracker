import { describe, expect, it } from 'vitest'
import type { TrackerPayload } from '../types'
import { sourceLink, wolfeOut } from './status'

const base: TrackerPayload = {
  updatedAt: '2026-10-11T16:00:00Z',
  source: 'rk9',
  tournament: 'Louisville Regionals',
  tournamentId: 'LO002-drfp6esCSpyU3s',
  status: 'Round 11 in progress',
  phase: 'swiss',
  record: { w: 7, l: 3 },
  standing: null,
  opw: null,
  topCutAlive: true,
  topCutStatus: 'bubble',
  team: [],
  matches: [],
}

describe('wolfeOut', () => {
  it('is false while he can still make the cut', () => {
    expect(wolfeOut(base)).toBe(false)
  })

  it('is true once he is projected out of top cut', () => {
    expect(wolfeOut({ ...base, topCutStatus: 'eliminated', topCutAlive: false })).toBe(true)
  })

  it('is true after a top cut loss, a drop, or the end of the event', () => {
    const loss = { round: 15, phase: 'topcut' as const, label: 'Top 8', opponent: 'X', opponentId: null, result: 'L' as const, score: '0-2' }
    expect(wolfeOut({ ...base, phase: 'topcut', topCutStatus: 'clinched', matches: [loss] })).toBe(true)
    expect(wolfeOut({ ...base, status: 'Dropped after round 6' })).toBe(true)
    expect(wolfeOut({ ...base, phase: 'finished' })).toBe(true)
  })

  it('stays false in top cut until he loses', () => {
    const win = { round: 15, phase: 'topcut' as const, label: 'Top 8', opponent: 'X', opponentId: null, result: 'W' as const, score: '2-0' }
    expect(wolfeOut({ ...base, phase: 'topcut', topCutStatus: 'clinched', matches: [win] })).toBe(false)
  })
})

describe('sourceLink', () => {
  it('points RK9 events at their pairings page', () => {
    expect(sourceLink(base)?.href).toBe('https://rk9.gg/pairings/LO002-drfp6esCSpyU3s')
  })
})
