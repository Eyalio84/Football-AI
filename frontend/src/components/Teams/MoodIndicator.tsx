/**
 * MoodIndicator Component
 *
 * Shows current team mood with emoji and intensity bar.
 * Displays mood factors when available.
 */

import { Smile, Meh, Frown, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { TeamMood } from '@/types'

interface MoodIndicatorProps {
  mood: TeamMood | null | undefined
  size?: 'sm' | 'md' | 'lg'
}

export function MoodIndicator({ mood, size = 'md' }: MoodIndicatorProps) {
  if (!mood) {
    return (
      <div className="text-muted-foreground text-sm">
        Mood data unavailable
      </div>
    )
  }

  const { icon: MoodIcon, color, label } = getMoodDetails(mood.current_mood)
  const sizeClasses = getSizeClasses(size)

  return (
    <div className="flex items-center gap-3">
      <div
        className={`flex items-center justify-center rounded-full ${sizeClasses.container}`}
        style={{ backgroundColor: color + '20' }}
      >
        <MoodIcon className={sizeClasses.icon} style={{ color }} />
      </div>

      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className={`font-medium ${sizeClasses.text}`}>{label}</span>
          <Badge variant="outline" className="text-xs">
            {mood.mood_intensity}/10
          </Badge>
        </div>

        {/* Intensity bar */}
        <div className="h-1.5 bg-muted rounded-full overflow-hidden mt-1 w-24">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${mood.mood_intensity * 10}%`,
              backgroundColor: color,
            }}
          />
        </div>

        {mood.last_result && (
          <p className="text-xs text-muted-foreground mt-1">
            Last: {mood.last_result}
          </p>
        )}
      </div>
    </div>
  )
}

interface MoodBadgeProps {
  mood: TeamMood | null | undefined
}

export function MoodBadge({ mood }: MoodBadgeProps) {
  if (!mood) return null

  const { icon: MoodIcon, color, label } = getMoodDetails(mood.current_mood)

  return (
    <Badge
      variant="outline"
      className="flex items-center gap-1"
      style={{ borderColor: color, color }}
    >
      <MoodIcon className="h-3 w-3" />
      {label}
    </Badge>
  )
}

function getMoodDetails(moodStr: string) {
  const moodLower = moodStr.toLowerCase()

  if (moodLower.includes('happy') || moodLower.includes('confident') || moodLower.includes('elated')) {
    return { icon: Smile, color: '#22c55e', label: moodStr }
  }
  if (moodLower.includes('sad') || moodLower.includes('frustrated') || moodLower.includes('disappointed')) {
    return { icon: Frown, color: '#ef4444', label: moodStr }
  }
  if (moodLower.includes('optimistic') || moodLower.includes('hopeful')) {
    return { icon: TrendingUp, color: '#3b82f6', label: moodStr }
  }
  if (moodLower.includes('pessimistic') || moodLower.includes('worried')) {
    return { icon: TrendingDown, color: '#f97316', label: moodStr }
  }
  if (moodLower.includes('neutral') || moodLower.includes('calm')) {
    return { icon: Minus, color: '#6b7280', label: moodStr }
  }

  return { icon: Meh, color: '#6b7280', label: moodStr }
}

function getSizeClasses(size: 'sm' | 'md' | 'lg') {
  switch (size) {
    case 'sm':
      return { container: 'h-8 w-8', icon: 'h-4 w-4', text: 'text-sm' }
    case 'lg':
      return { container: 'h-14 w-14', icon: 'h-8 w-8', text: 'text-lg' }
    default:
      return { container: 'h-10 w-10', icon: 'h-5 w-5', text: 'text-base' }
  }
}

export default MoodIndicator
