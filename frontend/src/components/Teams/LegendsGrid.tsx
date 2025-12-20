/**
 * LegendsGrid Component
 *
 * Displays club legends in a card grid format.
 * Shows name, position, era, and achievements.
 */

import { Star } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Legend } from '@/types'

interface LegendsGridProps {
  legends: Legend[]
  teamName?: string
}

export function LegendsGrid({ legends, teamName }: LegendsGridProps) {
  if (legends.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No legends data available
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {teamName && (
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Star className="h-5 w-5 text-yellow-500" />
          {teamName} Legends
        </h3>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {legends.map((legend) => (
          <LegendCard key={legend.id} legend={legend} />
        ))}
      </div>
    </div>
  )
}

interface LegendCardProps {
  legend: Legend
}

function LegendCard({ legend }: LegendCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Star className="h-5 w-5 text-yellow-500 fill-yellow-500" />
            <CardTitle className="text-lg">{legend.name}</CardTitle>
          </div>
          {legend.position && (
            <Badge variant="secondary">{legend.position}</Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-2">
        {legend.era && (
          <div className="text-sm text-muted-foreground">
            Era: {legend.era}
          </div>
        )}

        <div className="flex gap-4 text-sm">
          {legend.goals !== undefined && legend.goals > 0 && (
            <div>
              <span className="font-semibold">{legend.goals}</span>
              <span className="text-muted-foreground"> goals</span>
            </div>
          )}
          {legend.appearances !== undefined && legend.appearances > 0 && (
            <div>
              <span className="font-semibold">{legend.appearances}</span>
              <span className="text-muted-foreground"> apps</span>
            </div>
          )}
        </div>

        {legend.achievements && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {legend.achievements}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export default LegendsGrid
