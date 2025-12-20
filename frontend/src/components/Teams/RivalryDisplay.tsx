/**
 * RivalryDisplay Component
 *
 * Shows team rivalries with intensity bars.
 * Displays derby names and historical context.
 */

import { Flame, Swords } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Rivalry } from '@/types'

interface RivalryDisplayProps {
  rivalries: Rivalry[]
  teamName?: string
}

export function RivalryDisplay({ rivalries, teamName }: RivalryDisplayProps) {
  if (rivalries.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No rivalry data available
      </div>
    )
  }

  // Sort by intensity (highest first)
  const sortedRivalries = [...rivalries].sort((a, b) => b.intensity - a.intensity)

  return (
    <div className="space-y-4">
      {teamName && (
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Swords className="h-5 w-5 text-red-500" />
          {teamName} Rivalries
        </h3>
      )}

      <div className="space-y-3">
        {sortedRivalries.map((rivalry) => (
          <RivalryCard key={rivalry.id} rivalry={rivalry} />
        ))}
      </div>
    </div>
  )
}

interface RivalryCardProps {
  rivalry: Rivalry
}

function RivalryCard({ rivalry }: RivalryCardProps) {
  const intensityColor = getIntensityColor(rivalry.intensity)
  const intensityLabel = getIntensityLabel(rivalry.intensity)

  return (
    <Card>
      <CardContent className="py-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              {rivalry.intensity >= 9 ? (
                <Flame className="h-5 w-5 text-orange-500" />
              ) : (
                <Swords className="h-5 w-5 text-red-400" />
              )}
              <span className="font-semibold">
                {rivalry.derby_name || `vs ${rivalry.rival_team_name || `Team ${rivalry.rival_team_id}`}`}
              </span>
            </div>

            {rivalry.rival_team_name && !rivalry.derby_name && (
              <p className="text-sm text-muted-foreground">
                vs {rivalry.rival_team_name}
              </p>
            )}

            {rivalry.historical_context && (
              <p className="text-sm text-muted-foreground">
                {rivalry.historical_context}
              </p>
            )}
          </div>

          <div className="text-right">
            <div className="text-sm font-medium">{intensityLabel}</div>
            <div className="text-xs text-muted-foreground">{rivalry.intensity}/10</div>
          </div>
        </div>

        {/* Intensity bar */}
        <div className="mt-3">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${rivalry.intensity * 10}%`,
                backgroundColor: intensityColor,
              }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function getIntensityColor(intensity: number): string {
  if (intensity >= 9) return '#ef4444'  // red-500
  if (intensity >= 7) return '#f97316'  // orange-500
  if (intensity >= 5) return '#eab308'  // yellow-500
  return '#22c55e'  // green-500
}

function getIntensityLabel(intensity: number): string {
  if (intensity >= 9) return 'Fierce'
  if (intensity >= 7) return 'Intense'
  if (intensity >= 5) return 'Competitive'
  return 'Friendly'
}

export default RivalryDisplay
