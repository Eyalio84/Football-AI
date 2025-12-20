/**
 * ChatMessage Component
 *
 * Displays a single message bubble with club-themed styling.
 * User bubbles use club secondary colour; AI bubbles have club-tinted border.
 */

import { theme } from '../../config/theme'
import { useClubTheme } from '../../config/ClubThemeProvider'
import { RichChatMessage } from './RichChatMessage'
import type { Message } from '../../types'
import type { CSSProperties } from 'react'

interface ChatMessageProps {
  message: Message
  style?: CSSProperties
}

export function ChatMessage({ message, style: extraStyle }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const hasRichContent = !isUser && message.sources && message.sources.length > 0
  const { clubId, palette } = useClubTheme()

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-message-in`}
      style={extraStyle}
    >
      <div
        className={`${hasRichContent ? 'max-w-[90%]' : 'max-w-[80%]'} rounded-2xl px-4 py-3 transition-all duration-200 ${
          isUser ? 'rounded-br-sm' : 'rounded-bl-sm'
        }`}
        style={{
          backgroundColor: isUser
            ? (clubId ? palette.primary : theme.colors.bubbles.user)
            : theme.colors.bubbles.bot,
          color: isUser
            ? palette.textOnPrimary
            : theme.colors.bubbles.botText,
          borderLeft: !isUser && clubId
            ? `3px solid ${palette.primary}40`
            : undefined,
          boxShadow: isUser
            ? `0 2px 8px ${palette.primary}30`
            : '0 1px 4px rgba(0,0,0,0.2)',
        }}
      >
        {/* Message content */}
        <div className="text-sm md:text-base leading-relaxed whitespace-pre-wrap break-words">
          {message.isLoading ? (
            <TypingIndicator />
          ) : hasRichContent ? (
            <RichChatMessage content={message.content} sources={message.sources} />
          ) : (
            message.content
          )}
        </div>

        {/* Timestamp */}
        <div
          className="text-xs mt-1.5 opacity-60"
          style={{
            color: isUser
              ? palette.textOnPrimary
              : theme.colors.text.tertiary,
          }}
        >
          {formatTimestamp(message.timestamp)}
        </div>
      </div>
    </div>
  )
}

/**
 * Typing indicator — bouncing dots in club colour
 */
function TypingIndicator() {
  return (
    <div className="flex items-center space-x-1.5 py-1">
      <span className="typing-dot" />
      <span className="typing-dot" />
      <span className="typing-dot" />
    </div>
  )
}

function formatTimestamp(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`

  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
}
