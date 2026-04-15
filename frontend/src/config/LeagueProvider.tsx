/**
 * League Context Provider
 *
 * Provides the currently selected league (competition code, display name, clubs)
 * to the entire app. Fetches available leagues from /api/v1/leagues on mount.
 * Persists selection to localStorage so the user's choice survives page refresh.
 */

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

export interface LeagueClub {
  id: string
  display_name: string
}

export interface League {
  league_id: string
  display_name: string
  country: string
  sport: string
  competition_code: string
  club_count: number
  clubs: LeagueClub[]
}

interface LeagueContextValue {
  competition: string          // e.g. "PL", "PD"
  currentLeague: League | null
  leagues: League[]
  setCompetition: (code: string) => void
  clubsForLeague: LeagueClub[]
}

const DEFAULT_COMPETITION = 'PL'
const STORAGE_KEY = 'soccer_ai_league'

const LeagueContext = createContext<LeagueContextValue>({
  competition: DEFAULT_COMPETITION,
  currentLeague: null,
  leagues: [],
  setCompetition: () => {},
  clubsForLeague: [],
})

import { runtimeConfig } from './runtimeConfig'

export function LeagueProvider({ children }: { children: ReactNode }) {
  const [competition, setCompetitionState] = useState<string>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || DEFAULT_COMPETITION
    } catch {
      return DEFAULT_COMPETITION
    }
  })
  const [leagues, setLeagues] = useState<League[]>([])

  useEffect(() => {
    fetch(`${runtimeConfig.apiUrl}/api/v1/leagues`, {
      headers: { 'ngrok-skip-browser-warning': 'true' },
    })
      .then(r => r.json())
      .then(json => {
        const data: League[] = json.data ?? []
        setLeagues(data)
      })
      .catch(() => {
        // Fallback: at least show PL so app works without backend
        setLeagues([{
          league_id: 'premier_league',
          display_name: 'Premier League',
          country: 'England',
          sport: 'football',
          competition_code: 'PL',
          club_count: 20,
          clubs: [],
        }])
      })
  }, [])

  const setCompetition = (code: string) => {
    setCompetitionState(code)
    try {
      localStorage.setItem(STORAGE_KEY, code)
    } catch { /* ignore */ }
  }

  const currentLeague = leagues.find(l => l.competition_code === competition) ?? null
  const clubsForLeague = currentLeague?.clubs ?? []

  return (
    <LeagueContext.Provider value={{ competition, currentLeague, leagues, setCompetition, clubsForLeague }}>
      {children}
    </LeagueContext.Provider>
  )
}

export function useLeague() {
  return useContext(LeagueContext)
}
