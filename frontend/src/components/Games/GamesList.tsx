import { format, isToday, isTomorrow, parseISO } from 'date-fns'
import { GameCard } from './GameCard'
import { theme } from '@/config/theme'
import type { Game } from '@/types'

interface GamesListProps {
  games: Game[]
}

interface GroupedGames {
  [key: string]: Game[]
}

export function GamesList({ games }: GamesListProps) {
  // Group games by date
  const groupedGames: GroupedGames = games.reduce((acc, game) => {
    if (!game.date) return acc

    const date = typeof game.date === 'string' ? parseISO(game.date) : game.date
    let groupLabel: string

    if (isToday(date)) {
      groupLabel = 'Today'
    } else if (isTomorrow(date)) {
      groupLabel = 'Tomorrow'
    } else {
      groupLabel = format(date, 'EEEE, MMMM d')
    }

    if (!acc[groupLabel]) {
      acc[groupLabel] = []
    }
    acc[groupLabel].push(game)

    return acc
  }, {} as GroupedGames)

  // Sort groups by date (Today, Tomorrow, then chronological)
  const sortedGroupLabels = Object.keys(groupedGames).sort((a, b) => {
    if (a === 'Today') return -1
    if (b === 'Today') return 1
    if (a === 'Tomorrow') return -1
    if (b === 'Tomorrow') return 1

    // Parse dates from labels for comparison
    const dateA = groupedGames[a][0].date
    const dateB = groupedGames[b][0].date

    if (!dateA || !dateB) return 0

    return new Date(dateA).getTime() - new Date(dateB).getTime()
  })

  if (games.length === 0) {
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
          No games scheduled
        </p>
        <p
          className="text-sm mt-2"
          style={{ color: theme.colors.text.tertiary }}
        >
          Check back later for upcoming matches
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {sortedGroupLabels.map((groupLabel) => (
        <div key={groupLabel}>
          {/* Date Header */}
          <h2
            className="text-xl font-bold mb-4"
            style={{ color: theme.colors.text.primary }}
          >
            {groupLabel}
          </h2>

          {/* Games Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {groupedGames[groupLabel].map((game, index) => (
              <GameCard key={game.id || index} game={game} />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
