import { useNavigate } from 'react-router-dom'
import { Card } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { MapPin, Trophy } from 'lucide-react'
import { theme } from '@/config/theme'
import type { Team } from '@/types'

interface TeamCardProps {
  team: Team
  standing?: {
    position: number
    points: number
    form?: string
  }
}

// Get team initials for avatar
const getTeamInitials = (name: string) => {
  const words = name.split(' ').filter(w => w.length > 0)
  return words.map(w => w[0]).join('').slice(0, 3).toUpperCase()
}

// Form badge styling
const getFormBadgeStyle = (result: string) => {
  switch (result) {
    case 'W':
      return { backgroundColor: '#10B981', color: '#FFFFFF' }
    case 'D':
      return { backgroundColor: '#F59E0B', color: '#FFFFFF' }
    case 'L':
      return { backgroundColor: '#EF4444', color: '#FFFFFF' }
    default:
      return { backgroundColor: '#6B7280', color: '#FFFFFF' }
  }
}

export function TeamCard({ team, standing }: TeamCardProps) {
  const navigate = useNavigate()

  const handleClick = () => {
    navigate(`/teams/${team.id}`)
  }

  return (
    <Card
      className="p-6 hover:shadow-lg transition-all cursor-pointer group"
      onClick={handleClick}
    >
      <div className="flex flex-col items-center space-y-4">
        {/* Team Logo/Avatar */}
        <Avatar className="h-20 w-20 group-hover:scale-110 transition-transform">
          <AvatarFallback
            className="text-xl font-bold"
            style={{ backgroundColor: theme.colors.primary + '20' }}
          >
            {getTeamInitials(team.name)}
          </AvatarFallback>
        </Avatar>

        {/* Team Name */}
        <h3
          className="text-lg font-bold text-center"
          style={{ color: theme.colors.text.primary }}
        >
          {team.name}
        </h3>

        {/* Stadium */}
        {team.stadium && (
          <div className="flex items-center space-x-1 text-sm">
            <MapPin size={14} style={{ color: theme.colors.text.secondary }} />
            <span style={{ color: theme.colors.text.secondary }}>
              {team.stadium}
            </span>
          </div>
        )}

        {/* Divider */}
        {standing && <div className="w-full border-t" style={{ borderColor: theme.colors.border.subtle }} />}

        {/* Standing Info */}
        {standing && (
          <div className="w-full space-y-2">
            {/* Position and Points */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Trophy size={16} style={{ color: theme.colors.primary }} />
                <span className="font-semibold" style={{ color: theme.colors.text.primary }}>
                  {standing.position}{getOrdinalSuffix(standing.position)}
                </span>
              </div>
              <span className="font-bold" style={{ color: theme.colors.text.primary }}>
                {standing.points} pts
              </span>
            </div>

            {/* Form */}
            {standing.form && (
              <div className="flex items-center justify-center space-x-1">
                {standing.form.split('').map((result, idx) => (
                  <Badge
                    key={idx}
                    className="w-6 h-6 p-0 text-xs flex items-center justify-center"
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
    </Card>
  )
}

// Helper to get ordinal suffix (1st, 2nd, 3rd, etc.)
function getOrdinalSuffix(position: number): string {
  const j = position % 10
  const k = position % 100

  if (j === 1 && k !== 11) return 'st'
  if (j === 2 && k !== 12) return 'nd'
  if (j === 3 && k !== 13) return 'rd'
  return 'th'
}
