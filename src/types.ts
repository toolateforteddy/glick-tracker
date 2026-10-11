export type TopCutStatus = 'alive' | 'clinched' | 'eliminated'
export type MatchResult = 'W' | 'L' | 'T' | 'BYE'

export interface TeamMember {
  species: string
  item: string | null
  ability: string | null
  tera: string | null
  moves: string[]
}

export interface MatchRow {
  round: number
  phase: 'swiss' | 'topcut'
  label: string
  opponent: string | null
  opponentId: string | null
  result: MatchResult | null
  score: string | null
}

export interface TrackerPayload {
  updatedAt: string
  source?: 'limitless' | 'rk9'
  tournament: string
  tournamentId?: string | null
  tournamentUrl?: string | null
  status: string
  phase?: 'swiss' | 'topcut' | 'finished' | 'idle'
  round?: number | null
  swissRounds?: number | null
  topCutSize?: number | null
  players?: number | null
  record: { w: number; l: number; t?: number }
  standing: number | null
  opw: number | null
  topCutAlive: boolean
  topCutStatus?: TopCutStatus
  stream?: string | null
  roundStartedAt?: string | null
  currentMatchPending?: boolean
  team: TeamMember[]
  matches: MatchRow[]
}
