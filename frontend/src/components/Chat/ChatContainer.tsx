/**
 * ChatContainer Component
 *
 * The main chat interface that combines messages and input.
 * Handles auto-scrolling, empty states, and overall layout.
 */

import { useEffect, useRef } from 'react'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { SmartSuggestions, generateSuggestions } from './SmartSuggestions'
import { theme } from '../../config/theme'
import { useClubTheme } from '../../config/ClubThemeProvider'
import { FourDRadar } from '../Teams/FourDRadar'
import type { Message } from '../../types'

interface ChatContainerProps {
  messages: Message[]
  onSendMessage: (message: string) => void
  isLoading: boolean
  conversationId: string | null
  onClearChat?: () => void
  clubId?: string
  streamingEnabled?: boolean
  onToggleStreaming?: () => void
}

export function ChatContainer({
  messages,
  onSendMessage,
  isLoading,
  onClearChat,
  clubId,
  streamingEnabled = true,
  onToggleStreaming,
}: ChatContainerProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const { palette } = useClubTheme()

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const clubDisplayName = clubId
    ? clubId.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    : null

  return (
    <div
      className="flex flex-col h-screen relative"
      style={{ backgroundColor: theme.colors.background.main }}
    >
      {/* Stadium floodlight glow behind messages */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `radial-gradient(ellipse 90% 40% at 50% 0%, ${palette.glowColor} 0%, transparent 70%)`,
        }}
      />

      {/* Header */}
      <header
        className="relative z-10 border-b px-6 flex items-center justify-between backdrop-blur-sm"
        style={{
          backgroundColor: theme.colors.background.surface + 'DD',
          borderColor: palette.primary + '25',
          height: theme.layout.headerHeight,
        }}
      >
        <div className="flex items-center gap-3">
          {/* Compact 4D radar in chat header */}
          {clubId && (
            <FourDRadar clubId={clubId} size={44} compact />
          )}
          <div>
            <h1
              className="font-display text-lg font-bold tracking-wide uppercase"
              style={{ color: theme.colors.text.primary }}
            >
              {clubDisplayName || 'FOOTBALL AI'}
            </h1>
            <p className="text-xs" style={{ color: theme.colors.text.secondary }}>
              {clubId ? 'Fan at heart. Analyst in nature.' : 'Neutral analyst mode'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {onToggleStreaming && (
            <button
              onClick={onToggleStreaming}
              className="px-3 py-1.5 rounded-lg text-xs font-display font-semibold tracking-wide uppercase transition-colors hover:opacity-80 flex items-center gap-1"
              style={{
                backgroundColor: streamingEnabled
                  ? palette.primary
                  : theme.colors.background.elevated,
                color: streamingEnabled
                  ? palette.textOnPrimary
                  : theme.colors.text.secondary,
              }}
            >
              {streamingEnabled ? 'STREAM' : 'INSTANT'}
            </button>
          )}

          {messages.length > 0 && onClearChat && (
            <button
              onClick={onClearChat}
              className="px-3 py-1.5 rounded-lg text-xs font-display font-semibold tracking-wide uppercase transition-colors hover:opacity-80"
              style={{
                backgroundColor: theme.colors.background.elevated,
                color: theme.colors.text.secondary,
              }}
            >
              SWITCH CLUB
            </button>
          )}
        </div>
      </header>

      {/* Messages area */}
      <div
        ref={messagesContainerRef}
        className="relative z-10 flex-1 overflow-y-auto px-4 py-6"
      >
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 ? (
            <EmptyState clubId={clubId} onSuggest={onSendMessage} />
          ) : (
            <>
              {messages.map((message, idx) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  style={{ animationDelay: `${idx * 50}ms` }}
                />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Smart Suggestions */}
      {!isLoading && (
        <div className="relative z-10">
          <SmartSuggestions
            suggestions={generateSuggestions(messages)}
            onSelect={onSendMessage}
          />
        </div>
      )}

      {/* Input area */}
      <div className="relative z-10">
        <ChatInput onSend={onSendMessage} disabled={isLoading} />
      </div>
    </div>
  )
}

/**
 * Atmospheric empty state with stadium silhouette feel
 */
function EmptyState({ clubId, onSuggest }: { clubId?: string; onSuggest: (msg: string) => void }) {
  const suggestions = clubId
    ? [
        "How are we doing this season?",
        "Tell me about our greatest moment",
        "What do you think of our rivals?",
        "Any big matches coming up?",
        "Test my knowledge with some trivia",
      ]
    : [
        "Who will win the Premier League?",
        "Which teams are getting relegated?",
        "Any big matches this weekend?",
        "Compare Arsenal and Man City",
        "What's the state of the title race?",
      ]

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      {/* Atmospheric quote */}
      <div className="mb-10 max-w-lg">
        <p
          className="text-lg italic leading-relaxed"
          style={{ color: theme.colors.text.secondary }}
        >
          "That lad on the tip of his toes, split second before Beckham's freekick.
          That's the feeling. That's always the feeling."
        </p>
        <div
          className="w-12 h-0.5 mx-auto mt-4 rounded-full"
          style={{ backgroundColor: 'var(--club-primary)' }}
        />
      </div>

      {/* Prompt */}
      <h2
        className="font-display text-2xl font-bold tracking-wide uppercase mb-2"
        style={{ color: theme.colors.text.primary }}
      >
        {clubId ? "What's on your mind?" : "Ask the analyst"}
      </h2>
      <p
        className="text-sm mb-8"
        style={{ color: theme.colors.text.muted }}
      >
        {clubId
          ? "I bleed your colours. Ask me anything."
          : "Neutral. Data-driven. No allegiances."}
      </p>

      {/* Suggestion chips */}
      <div className="flex flex-wrap gap-2 justify-center max-w-xl">
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onSuggest(suggestion)}
            className="px-4 py-2 rounded-full text-sm transition-all duration-200 hover:scale-105 animate-fade-up border"
            style={{
              animationDelay: `${index * 80}ms`,
              backgroundColor: theme.colors.background.surface,
              color: theme.colors.text.secondary,
              borderColor: 'var(--club-primary)' + '30',
            }}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  )
}
