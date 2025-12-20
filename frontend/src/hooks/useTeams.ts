import { useState, useEffect } from 'react'
import {
  getTeams,
  getTeam,
  getTeamFixtures,
  getTeamResults,
  getTeamPersonality,
} from '@/services/api'
import type { Team, Game, TeamPersonality } from '@/types'

// Hook for fetching all teams
export function useTeams() {
  const [teams, setTeams] = useState<Team[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTeams = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getTeams(50) // Fetch all teams
      setTeams(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch teams'
      setError(message)
      console.error('Error fetching teams:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTeams()
  }, [])

  return {
    teams,
    loading,
    error,
    refetch: fetchTeams,
  }
}

// Hook for fetching a single team with its details
export function useTeam(teamId: number | string) {
  const [team, setTeam] = useState<Team | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTeam = async () => {
    try {
      setLoading(true)
      setError(null)
      const id = typeof teamId === 'string' ? parseInt(teamId, 10) : teamId
      const data = await getTeam(id)
      setTeam(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch team'
      setError(message)
      console.error('Error fetching team:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (teamId) {
      fetchTeam()
    }
  }, [teamId])

  return {
    team,
    loading,
    error,
    refetch: fetchTeam,
  }
}

// Hook for fetching team fixtures (upcoming games)
export function useTeamFixtures(teamId: number | string) {
  const [fixtures, setFixtures] = useState<Game[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchFixtures = async () => {
    try {
      setLoading(true)
      setError(null)
      const id = typeof teamId === 'string' ? parseInt(teamId, 10) : teamId
      const data = await getTeamFixtures(id)
      setFixtures(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch fixtures'
      setError(message)
      console.error('Error fetching fixtures:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (teamId) {
      fetchFixtures()
    }
  }, [teamId])

  return {
    fixtures,
    loading,
    error,
    refetch: fetchFixtures,
  }
}

// Hook for fetching team results (recent games)
export function useTeamResults(teamId: number | string) {
  const [results, setResults] = useState<Game[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchResults = async () => {
    try {
      setLoading(true)
      setError(null)
      const id = typeof teamId === 'string' ? parseInt(teamId, 10) : teamId
      const data = await getTeamResults(id)
      setResults(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch results'
      setError(message)
      console.error('Error fetching results:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (teamId) {
      fetchResults()
    }
  }, [teamId])

  return {
    results,
    loading,
    error,
    refetch: fetchResults,
  }
}

// Hook for fetching team personality (legends, rivalries, moments, mood)
export function useTeamPersonality(teamId: number | string) {
  const [personality, setPersonality] = useState<TeamPersonality | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPersonality = async () => {
    try {
      setLoading(true)
      setError(null)
      const id = typeof teamId === 'string' ? parseInt(teamId, 10) : teamId
      const data = await getTeamPersonality(id)
      setPersonality(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch personality'
      setError(message)
      console.error('Error fetching personality:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (teamId) {
      fetchPersonality()
    }
  }, [teamId])

  return {
    personality,
    loading,
    error,
    refetch: fetchPersonality,
  }
}
