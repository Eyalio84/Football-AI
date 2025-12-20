import { Badge } from '@/components/ui/badge'
import { Calendar, Clock } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import { theme } from '@/config/theme'
import type { Game } from '@/types'

interface MiniGameCardProps {
  game: Game
}

const statusConfig = {
  live: { label: 'LIVE', color: '#EF4444', bgColor: '#FEE2E2' },
  in_progress: { label: 'LIVE', color: '#EF4444', bgColor: '#FEE2E2' },
  finished: { label: 'FT', color: '#6B7280', bgColor: '#F3F4F6' },
  scheduled: { label: 'Upcoming', color: '#3B82F6', bgColor: '#DBEAFE' },
}

export function MiniGameCard({ game }: MiniGameCardProps) {
  const config = statusConfig[game.status as keyof typeof statusConfig] || statusConfig.scheduled
  const gameDate = game.date ? parseISO(game.date) : null

  return (
    <div
      className="inline-flex flex-col px-4 py-3 rounded-lg my-2 min-w-[300px] animate-slideUp"
      style={{
        backgroundColor: theme.colors.background.elevated,
        border: `1px solid ${theme.colors.border.subtle}`,
      }}
    >
      <Badge
        className="self-start mb-2"
        style={{ backgroundColor: config.bgColor, color: config.color, border: 'none' }}
      >
        {config.label}
      </Badge>

      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold" style={{ color: theme.colors.text.primary }}>
          {game.home_team?.name || 'TBD'}
        </span>
        {game.home_score !== null && game.home_score !== undefined && (
          <span className="text-xl font-bold ml-2" style={{ color: theme.colors.text.primary }}>
            {game.home_score}
          </span>
        )}
      </div>

      <div className="flex items-center justify-between mb-3">
        <span className="font-semibold" style={{ color: theme.colors.text.primary }}>
          {game.away_team?.name || 'TBD'}
        </span>
        {game.away_score !== null && game.away_score !== undefined && (
          <span className="text-xl font-bold ml-2" style={{ color: theme.colors.text.primary }}>
            {game.away_score}
          </span>
        )}
      </div>

      <div className="flex items-center space-x-3 text-xs" style={{ color: theme.colors.text.secondary }}>
        {gameDate && (
          <div className="flex items-center space-x-1">
            <Calendar size={12} />
            <span>{format(gameDate, 'MMM d')}</span>
          </div>
        )}
        {game.time && (
          <div className="flex items-center space-x-1">
            <Clock size={12} />
            <span>{game.time}</span>
          </div>
        )}
      </div>
    </div>
  )
}
