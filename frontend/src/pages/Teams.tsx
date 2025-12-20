import { useTeams } from '@/hooks/useTeams'
import { useStandings } from '@/hooks/useStandings'
import { TeamGrid } from '@/components/Teams/TeamGrid'
import { TeamsLoadingSkeleton } from '@/components/ui/LoadingSkeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import { theme } from '@/config/theme'

export function Teams() {
  const { teams, loading: teamsLoading, error: teamsError, refetch: refetchTeams } = useTeams()
  const { standings, loading: standingsLoading } = useStandings()

  const loading = teamsLoading || standingsLoading
  const error = teamsError

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1
          className="text-3xl font-bold"
          style={{ color: theme.colors.text.primary }}
        >
          Premier League Teams
        </h1>
        {!loading && !error && (
          <p
            className="text-sm"
            style={{ color: theme.colors.text.secondary }}
          >
            {teams.length} teams
          </p>
        )}
      </div>

      {loading && <TeamsLoadingSkeleton />}
      {error && <ErrorState message={error} onRetry={refetchTeams} />}
      {!loading && !error && <TeamGrid teams={teams} standings={standings} />}
    </div>
  )
}
