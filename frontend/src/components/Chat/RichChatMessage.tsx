import { useState, useEffect } from 'react'
import { MiniTeamCard } from './RichElements/MiniTeamCard'
import { MiniGameCard } from './RichElements/MiniGameCard'
import { MiniStandingsTable } from './RichElements/MiniStandingsTable'
import { getTeam, getGame, getStandings } from '@/services/api'
import { theme } from '@/config/theme'
import type { Source } from '@/types'

interface RichChatMessageProps {
  content: string
  sources?: Source[]
}

interface EnrichedData {
  teams: Map<number, any>
  games: Map<number, any>
  standings: any[]
}

export function RichChatMessage({ content, sources = [] }: RichChatMessageProps) {
  const [enrichedData, setEnrichedData] = useState<EnrichedData>({
    teams: new Map(),
    games: new Map(),
    standings: [],
  })
  const [loading, setLoading] = useState(true)

  // Fetch entity data based on sources
  useEffect(() => {
    const fetchEnrichedData = async () => {
      if (!sources || sources.length === 0) {
        setLoading(false)
        return
      }

      const teams = new Map()
      const games = new Map()
      let standings: any[] = []

      try {
        // Fetch teams
        const teamSources = sources.filter(s => s.type === 'team')
        await Promise.all(
          teamSources.slice(0, 3).map(async (source) => {
            try {
              const team = await getTeam(source.id)
              teams.set(source.id, team)
            } catch (err) {
              console.error(`Failed to fetch team ${source.id}:`, err)
            }
          })
        )

        // Fetch games
        const gameSources = sources.filter(s => s.type === 'game')
        await Promise.all(
          gameSources.slice(0, 3).map(async (source) => {
            try {
              const game = await getGame(source.id)
              games.set(source.id, game)
            } catch (err) {
              console.error(`Failed to fetch game ${source.id}:`, err)
            }
          })
        )

        // Fetch standings if mentioned
        if (content.toLowerCase().includes('standing') || content.toLowerCase().includes('table') || content.toLowerCase().includes('top')) {
          try {
            const standingsData = await getStandings()
            // Show top 5 for mini view
            standings = standingsData.slice(0, 5)
          } catch (err) {
            console.error('Failed to fetch standings:', err)
          }
        }

        setEnrichedData({ teams, games, standings })
      } catch (err) {
        console.error('Error fetching enriched data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchEnrichedData()
  }, [sources, content])

  if (loading) {
    return (
      <div style={{ color: theme.colors.text.secondary }} className="animate-pulse">
        {content}
      </div>
    )
  }

  // Render content with embedded rich elements
  return (
    <div className="space-y-2">
      {/* Main text content */}
      <div style={{ color: theme.colors.text.primary }}>
        {content}
      </div>

      {/* Embedded rich elements */}
      {enrichedData.teams.size > 0 && (
        <div className="flex flex-col space-y-2">
          {Array.from(enrichedData.teams.values()).map((team) => (
            <MiniTeamCard
              key={team.id}
              team={team}
              standing={enrichedData.standings.find(s => s.team_id === team.id)}
            />
          ))}
        </div>
      )}

      {enrichedData.games.size > 0 && (
        <div className="flex flex-col space-y-2">
          {Array.from(enrichedData.games.values()).map((game) => (
            <MiniGameCard key={game.id} game={game} />
          ))}
        </div>
      )}

      {enrichedData.standings.length > 0 && enrichedData.teams.size === 0 && (
        <MiniStandingsTable
          standings={enrichedData.standings}
          title="Current Standings"
        />
      )}
    </div>
  )
}
