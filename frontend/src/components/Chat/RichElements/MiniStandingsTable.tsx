import { Badge } from '@/components/ui/badge'
import { theme } from '@/config/theme'

interface Standing {
  position: number
  team_name: string
  played: number
  points: number
  form?: string
}

interface MiniStandingsTableProps {
  standings: Standing[]
  title?: string
}

const getFormBadgeStyle = (result: string) => {
  switch (result) {
    case 'W': return { backgroundColor: '#10B981', color: '#FFFFFF' }
    case 'D': return { backgroundColor: '#F59E0B', color: '#FFFFFF' }
    case 'L': return { backgroundColor: '#EF4444', color: '#FFFFFF' }
    default: return { backgroundColor: '#6B7280', color: '#FFFFFF' }
  }
}

export function MiniStandingsTable({ standings, title = 'Standings' }: MiniStandingsTableProps) {
  return (
    <div
      className="rounded-lg p-3 my-2 inline-block min-w-[320px] animate-slideUp"
      style={{
        backgroundColor: theme.colors.background.elevated,
        border: `1px solid ${theme.colors.border.subtle}`,
      }}
    >
      <h4 className="font-bold mb-3 text-sm" style={{ color: theme.colors.text.primary }}>
        {title}
      </h4>
      <div className="space-y-2">
        {standings.map((standing) => (
          <div
            key={standing.position}
            className="flex items-center justify-between text-sm"
          >
            <div className="flex items-center space-x-3 flex-1">
              <span className="font-bold w-6" style={{ color: theme.colors.text.secondary }}>
                {standing.position}
              </span>
              <span className="font-medium" style={{ color: theme.colors.text.primary }}>
                {standing.team_name}
              </span>
            </div>

            <div className="flex items-center space-x-3">
              <span className="text-xs" style={{ color: theme.colors.text.secondary }}>
                {standing.played}P
              </span>
              <span className="font-bold w-8 text-right" style={{ color: theme.colors.text.primary }}>
                {standing.points}
              </span>
              {standing.form && (
                <div className="flex space-x-0.5">
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
          </div>
        ))}
      </div>
    </div>
  )
}
