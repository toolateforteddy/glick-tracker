import { describe, expect, it } from 'vitest'
import { goatCounterEndpoint } from './analytics'

describe('goatCounterEndpoint', () => {
  it('is off when no code is configured', () => {
    expect(goatCounterEndpoint(undefined)).toBeNull()
    expect(goatCounterEndpoint('')).toBeNull()
    expect(goatCounterEndpoint('  ')).toBeNull()
  })

  it('builds the count URL from a site code', () => {
    expect(goatCounterEndpoint('glick-tracker')).toBe('https://glick-tracker.goatcounter.com/count')
    expect(goatCounterEndpoint(' glick ')).toBe('https://glick.goatcounter.com/count')
  })

  it('rejects anything that is not a bare site code', () => {
    expect(goatCounterEndpoint('https://glick.goatcounter.com')).toBeNull()
    expect(goatCounterEndpoint('evil.com/x')).toBeNull()
  })
})
