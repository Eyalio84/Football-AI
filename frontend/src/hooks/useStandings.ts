import { useState, useEffect } from 'react'
import { getStandings } from '@/services/api'

interface Standing {
  position: number
  team_id: number
  team_name: string
  played: number
  won: number
  drawn: number
  lost: number
  goals_for: number
  goals_against: number
  goal_difference: number
  points: number
  form?: string // Last 5 games: "WWDWL"
  team_logo?: string
}

interface UseStandingsOptions {
  league?: string
}

interface UseStandingsResult {
  standings: Standing[]
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useStandings(options: UseStandingsOptions = {}): UseStandingsResult {
  const { league = 'Premier League' } = options

  const [standings, setStandings] = useState<Standing[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStandings = async () => {
    try {
      setLoading(true)
      setError(null)

      const data = await getStandings(league)
      setStandings(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch standings'
      setError(message)
      console.error('Error fetching standings:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStandings()
  }, [league])

  return {
    standings,
    loading,
    error,
    refetch: fetchStandings,
  }
}
