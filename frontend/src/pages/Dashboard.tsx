import { useGames } from '@/hooks/useGames'
import { GamesList } from '@/components/Games/GamesList'
import { GamesLoadingSkeleton } from '@/components/ui/LoadingSkeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import { theme } from '@/config/theme'

export function Dashboard() {
  const { games, loading, error, refetch } = useGames({ mode: 'upcoming' })

  return (
    <div>
      <h1
        className="text-3xl font-bold mb-6"
        style={{ color: theme.colors.text.primary }}
      >
        Live & Upcoming Matches
      </h1>

      {loading && <GamesLoadingSkeleton />}
      {error && <ErrorState message={error} onRetry={refetch} />}
      {!loading && !error && <GamesList games={games} />}
    </div>
  )
}
