import { TeamCard } from './TeamCard'
import { theme } from '@/config/theme'
import type { Team } from '@/types'

interface Standing {
  team_id: number
  position: number
  points: number
  form?: string
}

interface TeamGridProps {
  teams: Team[]
  standings?: Standing[]
}

export function TeamGrid({ teams, standings }: TeamGridProps) {
  // Create a map of team_id to standing for quick lookup
  const standingsMap = new Map(
    standings?.map(s => [s.team_id, s]) || []
  )

  if (teams.length === 0) {
    return (
      <div
        className="text-center py-12 rounded-lg"
        style={{
          backgroundColor: theme.colors.background.elevated,
          border: `1px solid ${theme.colors.border.subtle}`,
        }}
      >
        <p
          className="text-lg"
          style={{ color: theme.colors.text.secondary }}
        >
          No teams found
        </p>
        <p
          className="text-sm mt-2"
          style={{ color: theme.colors.text.tertiary }}
        >
          Try adjusting your search or filters
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {teams.map((team) => (
        <TeamCard
          key={team.id}
          team={team}
          standing={standingsMap.get(team.id)}
        />
      ))}
    </div>
  )
}
