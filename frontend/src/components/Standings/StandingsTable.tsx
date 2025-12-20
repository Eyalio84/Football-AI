import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { theme } from '@/config/theme'

interface Standing {
  position: number
  team_id: number
  team_name: string
  played: number
  won: number
  drawn: number
  lost: number
  goals_for: number
  goals_against: number
  goal_difference: number
  points: number
  form?: string
  team_logo?: string
}

interface StandingsTableProps {
  standings: Standing[]
}

// Position-based zone styling — tells the story of the season
const getPositionStyle = (position: number) => {
  if (position <= 2) {
    // Title race (gold tint)
    return {
      borderLeft: '4px solid #EAB308',
      backgroundColor: 'rgba(234, 179, 8, 0.04)',
    }
  } else if (position <= 4) {
    // Champions League (blue)
    return {
      borderLeft: '4px solid #3B82F6',
      backgroundColor: 'rgba(59, 130, 246, 0.03)',
    }
  } else if (position <= 6) {
    // Europa League (amber)
    return {
      borderLeft: '4px solid #F59E0B',
      backgroundColor: 'rgba(245, 158, 11, 0.02)',
    }
  } else if (position >= 18) {
    // Relegation zone (red danger tint)
    return {
      borderLeft: '4px solid #EF4444',
      backgroundColor: 'rgba(239, 68, 68, 0.05)',
    }
  }
  return { borderLeft: '4px solid transparent' }
}

// Form badge styling
const getFormBadgeStyle = (result: string) => {
  switch (result) {
    case 'W':
      return { backgroundColor: '#10B981', color: '#FFFFFF' } // Green
    case 'D':
      return { backgroundColor: '#F59E0B', color: '#FFFFFF' } // Amber
    case 'L':
      return { backgroundColor: '#EF4444', color: '#FFFFFF' } // Red
    default:
      return { backgroundColor: '#6B7280', color: '#FFFFFF' } // Gray
  }
}

// Get team initials for avatar
const getTeamInitials = (name: string) => {
  const words = name.split(' ').filter(w => w.length > 0)
  return words.map(w => w[0]).join('').slice(0, 3).toUpperCase()
}

export function StandingsTable({ standings }: StandingsTableProps) {
  if (standings.length === 0) {
    return (
      <div
        className="text-center py-12 rounded-lg"
        style={{
          backgroundColor: theme.colors.background.elevated,
          border: `1px solid ${theme.colors.border.subtle}`,
        }}
      >
        <p className="text-lg" style={{ color: theme.colors.text.secondary }}>
          No standings data available
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border" style={{ borderColor: theme.colors.border.subtle }}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12 text-center">Pos</TableHead>
            <TableHead>Team</TableHead>
            <TableHead className="text-center hidden sm:table-cell">P</TableHead>
            <TableHead className="text-center hidden md:table-cell">W</TableHead>
            <TableHead className="text-center hidden md:table-cell">D</TableHead>
            <TableHead className="text-center hidden md:table-cell">L</TableHead>
            <TableHead className="text-center hidden lg:table-cell">GF</TableHead>
            <TableHead className="text-center hidden lg:table-cell">GA</TableHead>
            <TableHead className="text-center hidden sm:table-cell">GD</TableHead>
            <TableHead className="text-center font-bold">Pts</TableHead>
            <TableHead className="text-center hidden lg:table-cell">Form</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {standings.map((standing) => (
            <TableRow
              key={standing.team_id}
              className="hover:bg-muted/50"
              style={getPositionStyle(standing.position)}
            >
              {/* Position */}
              <TableCell className="text-center font-semibold">
                {standing.position}
              </TableCell>

              {/* Team Name with Avatar */}
              <TableCell>
                <div className="flex items-center space-x-3">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback
                      style={{ backgroundColor: theme.colors.primary + '20' }}
                      className="text-xs"
                    >
                      {getTeamInitials(standing.team_name)}
                    </AvatarFallback>
                  </Avatar>
                  <span className="font-medium">{standing.team_name}</span>
                </div>
              </TableCell>

              {/* Stats */}
              <TableCell className="text-center hidden sm:table-cell">
                {standing.played}
              </TableCell>
              <TableCell className="text-center hidden md:table-cell text-green-600">
                {standing.won}
              </TableCell>
              <TableCell className="text-center hidden md:table-cell text-amber-600">
                {standing.drawn}
              </TableCell>
              <TableCell className="text-center hidden md:table-cell text-red-600">
                {standing.lost}
              </TableCell>
              <TableCell className="text-center hidden lg:table-cell">
                {standing.goals_for}
              </TableCell>
              <TableCell className="text-center hidden lg:table-cell">
                {standing.goals_against}
              </TableCell>
              <TableCell className="text-center hidden sm:table-cell font-medium">
                {standing.goal_difference > 0 ? '+' : ''}
                {standing.goal_difference}
              </TableCell>
              <TableCell className="text-center font-bold text-lg">
                {standing.points}
              </TableCell>

              {/* Form (Last 5 Games) — coloured circles */}
              <TableCell className="text-center hidden lg:table-cell">
                {standing.form && (
                  <div className="flex items-center justify-center space-x-1">
                    {standing.form.split('').map((result, idx) => (
                      <div
                        key={idx}
                        className="w-3 h-3 rounded-full"
                        title={result === 'W' ? 'Win' : result === 'D' ? 'Draw' : 'Loss'}
                        style={getFormBadgeStyle(result)}
                      />
                    ))}
                  </div>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Legend */}
      <div className="p-4 border-t flex flex-wrap gap-4 text-xs font-display tracking-wide uppercase">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#EAB308' }} />
          <span style={{ color: theme.colors.text.secondary }}>Title Race</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#3B82F6' }} />
          <span style={{ color: theme.colors.text.secondary }}>Champions League</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#F59E0B' }} />
          <span style={{ color: theme.colors.text.secondary }}>Europa</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: '#EF4444' }} />
          <span style={{ color: theme.colors.text.secondary }}>Relegation</span>
        </div>
      </div>
    </div>
  )
}
