import { Badge } from '@/components/ui/badge'
import { theme } from '@/config/theme'

interface SmartSuggestionsProps {
  suggestions: string[]
  onSelect: (suggestion: string) => void
}

export function SmartSuggestions({ suggestions, onSelect }: SmartSuggestionsProps) {
  if (suggestions.length === 0) return null

  return (
    <div className="px-4 pb-2">
      <div className="flex items-center space-x-2 mb-2">
        <div
          className="w-1.5 h-1.5 rounded-full"
          style={{ backgroundColor: 'var(--club-primary)' }}
        />
        <span className="text-xs font-display font-semibold tracking-wide uppercase" style={{ color: theme.colors.text.secondary }}>
          Try asking
        </span>
      </div>
      <div className="flex flex-wrap gap-2 max-w-3xl mx-auto">
        {suggestions.map((suggestion, idx) => (
          <Badge
            key={idx}
            onClick={() => onSelect(suggestion)}
            className="cursor-pointer transition-all duration-200 hover:scale-105"
            style={{
              backgroundColor: theme.colors.background.elevated,
              color: theme.colors.text.primary,
              border: `1px solid var(--club-primary, ${theme.colors.border.subtle})30`,
            }}
          >
            {suggestion}
          </Badge>
        ))}
      </div>
    </div>
  )
}

// Generate smart suggestions based on conversation context
export function generateSuggestions(messages: any[]): string[] {
  if (messages.length === 0) {
    return [
      "Who's top of the league?",
      "Show me today's games",
      "Tell me about Arsenal",
    ]
  }

  const lastBotMessage = [...messages].reverse().find(m => m.role === 'assistant')
  if (!lastBotMessage || !lastBotMessage.sources) {
    return [
      "Who's top of the league?",
      "When's the next big match?",
    ]
  }

  const suggestions: string[] = []
  const sources = lastBotMessage.sources

  // Team-related suggestions
  const teamSources = sources.filter((s: any) => s.type === 'team')
  if (teamSources.length > 0) {
    suggestions.push("Show me their upcoming fixtures")
    suggestions.push("How have they been performing?")
    if (teamSources.length >= 2) {
      suggestions.push("Compare these teams")
    }
  }

  // Game-related suggestions
  const gameSources = sources.filter((s: any) => s.type === 'game')
  if (gameSources.length > 0) {
    suggestions.push("Who won their last match?")
    suggestions.push("Show me the league table")
  }

  // Always add general fallbacks
  if (suggestions.length < 3) {
    suggestions.push("Show me today's games")
    suggestions.push("Who's in the top 4?")
  }

  return suggestions.slice(0, 3)
}
