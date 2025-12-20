import { useState, useEffect } from 'react'
import { getGamesToday, getGamesUpcoming, getGamesLive, getGames } from '@/services/api'
import type { Game } from '@/types'

interface UseGamesOptions {
  mode?: 'today' | 'upcoming' | 'live' | 'all'
  limit?: number
}

interface UseGamesResult {
  games: Game[]
  loading: boolean
  error: string | null
  refetch: () => void
}

export function useGames(options: UseGamesOptions = {}): UseGamesResult {
  const { mode = 'upcoming', limit = 20 } = options

  const [games, setGames] = useState<Game[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchGames = async () => {
    try {
      setLoading(true)
      setError(null)

      let data: Game[]

      switch (mode) {
        case 'today':
          data = await getGamesToday()
          break
        case 'upcoming':
          data = await getGamesUpcoming(limit)
          break
        case 'live':
          data = await getGamesLive()
          break
        case 'all':
        default:
          data = await getGames(limit)
          break
      }

      setGames(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch games'
      setError(message)
      console.error('Error fetching games:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchGames()
  }, [mode, limit])

  return {
    games,
    loading,
    error,
    refetch: fetchGames,
  }
}
