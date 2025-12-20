import { format } from 'date-fns'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { MapPin, Clock } from 'lucide-react'
import { theme } from '@/config/theme'
import type { Game } from '@/types'

interface GameCardProps {
  game: Game
}

const statusConfig = {
  live: { label: 'LIVE', color: '#EF4444', bgColor: '#FEE2E2' },
  in_progress: { label: 'LIVE', color: '#EF4444', bgColor: '#FEE2E2' },
  finished: { label: 'FT', color: '#6B7280', bgColor: '#F3F4F6' },
  scheduled: { label: 'Scheduled', color: '#3B82F6', bgColor: '#DBEAFE' },
}

export function GameCard({ game }: GameCardProps) {
  const config = statusConfig[game.status as keyof typeof statusConfig] || statusConfig.scheduled

  // Format date and time
  const gameDate = game.date ? new Date(game.date) : null
  const dateStr = gameDate ? format(gameDate, 'EEE, MMM d') : ''
  const timeStr = game.time || ''

  // Get team initials for avatars
  const getInitials = (name: string) => {
    const words = name.split(' ')
    return words.map(w => w[0]).join('').slice(0, 3).toUpperCase()
  }

  const homeInitials = getInitials(game.home_team?.name || 'HOME')
  const awayInitials = getInitials(game.away_team?.name || 'AWAY')

  const hasScore = game.home_team?.score !== null && game.home_team?.score !== undefined

  return (
    <Card className="p-4 hover:shadow-lg transition-shadow cursor-pointer">
      {/* Status Badge */}
      <div className="flex justify-between items-center mb-4">
        <Badge
          style={{
            backgroundColor: config.bgColor,
            color: config.color,
            border: 'none',
          }}
          className="font-semibold"
        >
          {config.label}
        </Badge>
        {game.status === 'in_progress' && game.home_team?.score !== undefined && (
          <span
            className="text-sm font-medium"
            style={{ color: theme.colors.text.secondary }}
          >
            {/* Could show minute here if available */}
          </span>
        )}
      </div>

      {/* Teams and Scores */}
      <div className="space-y-3">
        {/* Home Team */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1">
            <Avatar className="h-10 w-10">
              <AvatarFallback style={{ backgroundColor: theme.colors.primary + '20' }}>
                {homeInitials}
              </AvatarFallback>
            </Avatar>
            <span
              className="font-semibold text-base"
              style={{ color: theme.colors.text.primary }}
            >
              {game.home_team?.name || 'TBD'}
            </span>
          </div>
          {hasScore && (
            <span
              className="text-2xl font-bold ml-4"
              style={{ color: theme.colors.text.primary }}
            >
              {game.home_team?.score}
            </span>
          )}
        </div>

        {/* Away Team */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1">
            <Avatar className="h-10 w-10">
              <AvatarFallback style={{ backgroundColor: theme.colors.primary + '20' }}>
                {awayInitials}
              </AvatarFallback>
            </Avatar>
            <span
              className="font-semibold text-base"
              style={{ color: theme.colors.text.primary }}
            >
              {game.away_team?.name || 'TBD'}
            </span>
          </div>
          {hasScore && (
            <span
              className="text-2xl font-bold ml-4"
              style={{ color: theme.colors.text.primary }}
            >
              {game.away_team?.score}
            </span>
          )}
        </div>
      </div>

      {/* Match Details */}
      <div className="mt-4 pt-4 border-t flex items-center justify-between text-sm">
        <div className="flex items-center space-x-4">
          {dateStr && (
            <div className="flex items-center space-x-1">
              <Clock size={14} style={{ color: theme.colors.text.secondary }} />
              <span style={{ color: theme.colors.text.secondary }}>
                {dateStr} {timeStr}
              </span>
            </div>
          )}
        </div>
        {game.venue && (
          <div className="flex items-center space-x-1">
            <MapPin size={14} style={{ color: theme.colors.text.secondary }} />
            <span
              className="truncate max-w-[120px]"
              style={{ color: theme.colors.text.secondary }}
            >
              {game.venue}
            </span>
          </div>
        )}
      </div>
    </Card>
  )
}
