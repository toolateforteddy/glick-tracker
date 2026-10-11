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
  table: number | null
  opponent: string | null
  opponentId: string | null
  result: MatchResult | null
  score: string | null
}

export interface TrackerPayload {
  updatedAt: string
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
  table: number | null
  opw: number | null
  topCutAlive: boolean
  topCutStatus?: TopCutStatus
  stream?: string | null
  roundStartedAt?: string | null
  currentMatchPending?: boolean
  team: TeamMember[]
  matches: MatchRow[]
}
