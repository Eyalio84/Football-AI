import { useStandings } from '@/hooks/useStandings'
import { StandingsTable } from '@/components/Standings/StandingsTable'
import { StandingsLoadingSkeleton } from '@/components/ui/LoadingSkeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import { theme } from '@/config/theme'

export function Standings() {
  const { standings, loading, error, refetch } = useStandings()

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1
          className="text-3xl font-bold"
          style={{ color: theme.colors.text.primary }}
        >
          Premier League Standings
        </h1>
        {!loading && !error && (
          <p
            className="text-sm"
            style={{ color: theme.colors.text.secondary }}
          >
            {standings.length} teams
          </p>
        )}
      </div>

      {loading && <StandingsLoadingSkeleton />}
      {error && <ErrorState message={error} onRetry={refetch} />}
      {!loading && !error && <StandingsTable standings={standings} />}
    </div>
  )
}
