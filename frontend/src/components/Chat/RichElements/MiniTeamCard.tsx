import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Trophy } from 'lucide-react'
import { theme } from '@/config/theme'

interface MiniTeamCardProps {
  team: {
    id: number
    name: string
    stadium?: string | null
  }
  standing?: {
    position: number
    points: number
    form?: string
  }
}

const getTeamInitials = (name: string) => {
  return name.split(' ').map(w => w[0]).join('').slice(0, 3).toUpperCase()
}

const getFormBadgeStyle = (result: string) => {
  switch (result) {
    case 'W': return { backgroundColor: '#10B981', color: '#FFFFFF' }
    case 'D': return { backgroundColor: '#F59E0B', color: '#FFFFFF' }
    case 'L': return { backgroundColor: '#EF4444', color: '#FFFFFF' }
    default: return { backgroundColor: '#6B7280', color: '#FFFFFF' }
  }
}

export function MiniTeamCard({ team, standing }: MiniTeamCardProps) {
  return (
    <div
      className="inline-flex items-center space-x-3 px-4 py-3 rounded-lg my-2 animate-slideUp"
      style={{
        backgroundColor: theme.colors.background.elevated,
        border: `1px solid ${theme.colors.border.subtle}`,
      }}
    >
      <Avatar className="h-12 w-12">
        <AvatarFallback style={{ backgroundColor: theme.colors.primary + '20' }}>
          {getTeamInitials(team.name)}
        </AvatarFallback>
      </Avatar>

      <div className="flex-1">
        <h4 className="font-bold" style={{ color: theme.colors.text.primary }}>
          {team.name}
        </h4>
        {team.stadium && (
          <p className="text-sm" style={{ color: theme.colors.text.secondary }}>
            {team.stadium}
          </p>
        )}
      </div>

      {standing && (
        <div className="flex flex-col items-end space-y-1">
          <div className="flex items-center space-x-1">
            <Trophy size={14} style={{ color: theme.colors.primary }} />
            <span className="font-bold text-sm" style={{ color: theme.colors.text.primary }}>
              {standing.position}
              {standing.position === 1 ? 'st' : standing.position === 2 ? 'nd' : standing.position === 3 ? 'rd' : 'th'}
            </span>
            <span className="text-sm" style={{ color: theme.colors.text.secondary }}>
              • {standing.points}pts
            </span>
          </div>
          {standing.form && (
            <div className="flex items-center space-x-0.5">
              {standing.form.split('').slice(-3).map((result, idx) => (
                <Badge
                  key={idx}
                  className="w-4 h-4 p-0 text-[10px] flex items-center justify-center"
                  style={getFormBadgeStyle(result)}
                >
                  {result}
                </Badge>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
