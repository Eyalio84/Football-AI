/**
 * MomentsTimeline Component
 *
 * Displays historic moments in a vertical timeline.
 * Shows emotion icons, dates, and significance.
 */

import { Trophy, Heart, Frown, Smile, Star, Zap } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Moment } from '@/types'

interface MomentsTimelineProps {
  moments: Moment[]
  teamName?: string
}

export function MomentsTimeline({ moments, teamName }: MomentsTimelineProps) {
  if (moments.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No historic moments available
      </div>
    )
  }

  // Sort by date (most recent first)
  const sortedMoments = [...moments].sort((a, b) => {
    if (!a.date || !b.date) return 0
    return new Date(b.date).getTime() - new Date(a.date).getTime()
  })

  return (
    <div className="space-y-4">
      {teamName && (
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Trophy className="h-5 w-5 text-amber-500" />
          {teamName} Memorable Moments
        </h3>
      )}

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />

        <div className="space-y-4">
          {sortedMoments.map((moment) => (
            <MomentCard key={moment.id} moment={moment} />
          ))}
        </div>
      </div>
    </div>
  )
}

interface MomentCardProps {
  moment: Moment
}

function MomentCard({ moment }: MomentCardProps) {
  const EmotionIcon = getEmotionIcon(moment.emotion)
  const emotionColor = getEmotionColor(moment.emotion)

  return (
    <div className="relative pl-10">
      {/* Timeline dot */}
      <div
        className="absolute left-2 w-5 h-5 rounded-full border-2 bg-background flex items-center justify-center"
        style={{ borderColor: emotionColor }}
      >
        <EmotionIcon className="h-3 w-3" style={{ color: emotionColor }} />
      </div>

      <Card>
        <CardContent className="py-4">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1 flex-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold">{moment.title}</span>
                {moment.emotion && (
                  <Badge
                    variant="outline"
                    className="text-xs capitalize"
                    style={{ borderColor: emotionColor, color: emotionColor }}
                  >
                    {moment.emotion}
                  </Badge>
                )}
              </div>

              {moment.opponent && moment.result && (
                <p className="text-sm text-muted-foreground">
                  vs {moment.opponent} • {moment.result}
                </p>
              )}

              {moment.competition && (
                <p className="text-sm text-muted-foreground">
                  {moment.competition}
                </p>
              )}

              {moment.significance && (
                <p className="text-sm mt-2">{moment.significance}</p>
              )}
            </div>

            {moment.date && (
              <div className="text-right text-sm text-muted-foreground whitespace-nowrap">
                {formatDate(moment.date)}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function getEmotionIcon(emotion?: string) {
  switch (emotion?.toLowerCase()) {
    case 'triumph':
      return Trophy
    case 'heartbreak':
      return Frown
    case 'joy':
      return Smile
    case 'defiance':
      return Zap
    case 'vindication':
      return Star
    default:
      return Heart
  }
}

function getEmotionColor(emotion?: string): string {
  switch (emotion?.toLowerCase()) {
    case 'triumph':
      return '#f59e0b'  // amber-500
    case 'heartbreak':
      return '#ef4444'  // red-500
    case 'joy':
      return '#22c55e'  // green-500
    case 'defiance':
      return '#8b5cf6'  // violet-500
    case 'vindication':
      return '#3b82f6'  // blue-500
    default:
      return '#6b7280'  // gray-500
  }
}

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    // Check if it's just a year
    if (dateStr.length === 4) {
      return dateStr
    }
    // Check if it's year-month (like "2003-04")
    if (dateStr.includes('-') && dateStr.split('-').length === 2) {
      return dateStr
    }
    // Full date formatting
    return date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  } catch {
    return dateStr
  }
}

export default MomentsTimeline
