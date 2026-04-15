/**
 * LaLigaChat
 *
 * Dedicated chat page for La Liga's 6 MVP clubs.
 * Completely isolated from the PL /chat page — no dependency on LeagueProvider
 * for club identity. The 6 clubs are hardcoded here so there is zero race-condition
 * or fallback path that could accidentally swap club_id for an Arsenal default.
 *
 * Clubs: Real Madrid, FC Barcelona, Atletico Madrid, Sevilla, Athletic Bilbao, Valencia
 */

import { useState, useEffect } from 'react'
import { ChatContainer } from '@/components/Chat/ChatContainer'
import { useChat } from '@/hooks/useChat'
import { useClubTheme } from '@/config/ClubThemeProvider'
import { theme } from '@/config/theme'
import { CLUB_PALETTES, DEFAULT_PALETTE, type ClubPalette } from '@/config/clubThemes'
import { runtimeConfig } from '@/config/runtimeConfig'

// ─── Hardcoded La Liga 6 MVP clubs ────────────────────────────────────────────
// These must match backend/Leagues/La_Liga/league_config.json club ids exactly.

interface LaLigaClub {
  id: string
  displayName: string
  stadium: string
  city: string
  tagline: string
}

const LA_LIGA_CLUBS: LaLigaClub[] = [
  {
    id: 'real_madrid',
    displayName: 'Real Madrid',
    stadium: 'Santiago Bernabéu',
    city: 'Madrid',
    tagline: '14 European Cups. Hala Madrid.',
  },
  {
    id: 'barcelona',
    displayName: 'FC Barcelona',
    stadium: 'Spotify Camp Nou',
    city: 'Barcelona',
    tagline: 'Més que un club. Visca el Barça.',
  },
  {
    id: 'atletico_madrid',
    displayName: 'Atlético Madrid',
    stadium: 'Cívitas Metropolitano',
    city: 'Madrid',
    tagline: 'Blood, sweat and Cholismo.',
  },
  {
    id: 'sevilla',
    displayName: 'Sevilla FC',
    stadium: 'Ramón Sánchez-Pizjuán',
    city: 'Seville',
    tagline: '7 Europa Leagues. Ole mi Sevilla.',
  },
  {
    id: 'athletic_bilbao',
    displayName: 'Athletic Club',
    stadium: 'San Mamés',
    city: 'Bilbao',
    tagline: 'Cantera only. Aupa Athletic.',
  },
  {
    id: 'valencia',
    displayName: 'Valencia CF',
    stadium: 'Mestalla',
    city: 'Valencia',
    tagline: 'La che. Amunt Valencia.',
  },
]

// ─── Mood badge ───────────────────────────────────────────────────────────────

interface MoodData {
  current_mood: string
  form?: string
}

function MoodBadge({ clubId }: { clubId: string }) {
  const [mood, setMood] = useState<MoodData | null>(null)

  useEffect(() => {
    fetch(`${runtimeConfig.apiUrl}/api/v1/fan/${clubId}/mood`, {
      headers: { 'ngrok-skip-browser-warning': 'true' },
    })
      .then(r => r.json())
      .then(json => setMood(json.mood ?? null))
      .catch(() => {})
  }, [clubId])

  if (!mood) return null

  const moodColors: Record<string, string> = {
    euphoric: '#22c55e', confident: '#22c55e',
    steady: '#94a3b8', neutral: '#94a3b8',
    anxious: '#f59e0b', frustrated: '#f59e0b',
    despairing: '#ef4444',
  }
  const color = moodColors[mood.current_mood.toLowerCase()] ?? '#6b7280'

  return (
    <div className="flex items-center gap-2 mt-1">
      <span className="text-xs font-mono font-semibold uppercase" style={{ color }}>
        {mood.current_mood}
      </span>
      {mood.form && (
        <div className="flex gap-0.5">
          {mood.form.split('').slice(0, 5).map((r, i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full"
              style={{
                backgroundColor: r === 'W' ? '#22c55e' : r === 'D' ? '#eab308' : r === 'L' ? '#ef4444' : '#6b7280',
                opacity: 0.8,
              }}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Club selection grid ──────────────────────────────────────────────────────

interface ClubGridProps {
  onSelectClub: (clubId: string) => void
}

function ClubGrid({ onSelectClub }: ClubGridProps) {
  const [hovered, setHovered] = useState<string | null>(null)

  return (
    <div
      className="min-h-screen flex flex-col items-center p-6 pt-10"
      style={{ backgroundColor: theme.colors.background.default }}
    >
      {/* Header */}
      <div className="max-w-4xl w-full text-center mb-10">
        {/* League badge */}
        <div
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border mb-6 animate-fade-up"
          style={{
            borderColor: theme.colors.border.default,
            backgroundColor: theme.colors.background.elevated,
          }}
        >
          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#E63946' }} />
          <span
            className="text-xs font-display font-bold tracking-widest uppercase"
            style={{ color: theme.colors.text.secondary }}
          >
            La Liga — Spain
          </span>
        </div>

        <h1
          className="font-display text-5xl sm:text-6xl font-extrabold tracking-tight uppercase mb-3 animate-fade-up"
          style={{ color: theme.colors.text.primary, animationDelay: '50ms' }}
        >
          ELIGE TU CLUB
        </h1>
        <p
          className="text-lg italic animate-fade-up"
          style={{ color: theme.colors.text.secondary, animationDelay: '120ms' }}
        >
          "¡Vamos! Pick your side and feel the passion of Spanish football."
        </p>
      </div>

      {/* Club grid — 2 cols mobile, 3 desktop */}
      <div className="w-full max-w-4xl">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {LA_LIGA_CLUBS.map((club, index) => {
            const palette: ClubPalette = CLUB_PALETTES[club.id] || DEFAULT_PALETTE
            const isHovered = hovered === club.id

            return (
              <button
                key={club.id}
                onClick={() => onSelectClub(club.id)}
                onMouseEnter={() => setHovered(club.id)}
                onMouseLeave={() => setHovered(null)}
                className="relative cursor-pointer transition-all duration-300 animate-fade-up text-left"
                style={{ animationDelay: `${160 + index * 60}ms` }}
              >
                <div
                  className="rounded-xl p-5 h-full flex flex-col justify-between border transition-all duration-300 overflow-hidden"
                  style={{
                    background: isHovered ? palette.gradient : theme.colors.background.elevated,
                    borderColor: isHovered ? palette.primary : palette.primary + '30',
                    boxShadow: isHovered
                      ? `0 16px 40px ${palette.primary}40, inset 0 1px 0 ${palette.primary}20`
                      : 'none',
                    transform: isHovered ? 'translateY(-3px) scale(1.02)' : 'translateY(0)',
                    minHeight: '160px',
                  }}
                >
                  {/* Colour accent bar */}
                  <div
                    className="w-10 h-1 rounded-full mb-3"
                    style={{ backgroundColor: palette.primary }}
                  />

                  {/* Club name */}
                  <h3
                    className="font-display text-lg font-extrabold tracking-wide uppercase leading-tight mb-1 transition-colors duration-300"
                    style={{
                      color: isHovered ? palette.textOnPrimary : theme.colors.text.primary,
                    }}
                  >
                    {club.displayName}
                  </h3>

                  {/* Stadium + city */}
                  <p
                    className="text-xs mb-2 transition-colors duration-300"
                    style={{
                      color: isHovered ? palette.textOnPrimary + 'AA' : theme.colors.text.muted,
                    }}
                  >
                    {club.stadium} · {club.city}
                  </p>

                  {/* Tagline */}
                  <p
                    className="text-[11px] italic leading-snug transition-colors duration-300 mb-2"
                    style={{
                      color: isHovered ? palette.textOnPrimary + 'CC' : theme.colors.text.secondary,
                    }}
                  >
                    {club.tagline}
                  </p>

                  {/* Live mood */}
                  <MoodBadge clubId={club.id} />
                </div>
              </button>
            )
          })}
        </div>

        {/* Footer */}
        <div
          className="mt-10 text-center text-xs font-display tracking-widest uppercase"
          style={{ color: theme.colors.text.muted }}
        >
          Pasión. Historia. La Liga.
        </div>
      </div>
    </div>
  )
}

// ─── Main page component ──────────────────────────────────────────────────────

export function LaLigaChat() {
  const [selectedClub, setSelectedClub] = useState<string | null>(null)
  const { setClubId } = useClubTheme()
  const {
    messages,
    conversationId,
    isLoading,
    sendMessage,
    clearChat,
    streamingEnabled,
    toggleStreaming,
  } = useChat(selectedClub || undefined)

  useEffect(() => {
    setClubId(selectedClub)
  }, [selectedClub, setClubId])

  const handleClubSelect = (clubId: string) => {
    // Validate — extra safety: only accept known La Liga clubs
    const valid = LA_LIGA_CLUBS.find(c => c.id === clubId)
    if (!valid) {
      console.error('[LaLigaChat] Unknown club id:', clubId)
      return
    }
    setSelectedClub(clubId)
  }

  const handleChangeClub = () => {
    setSelectedClub(null)
    clearChat()
  }

  if (!selectedClub) {
    return <ClubGrid onSelectClub={handleClubSelect} />
  }

  return (
    <div className="h-[calc(100vh-8rem)]">
      <ChatContainer
        messages={messages}
        onSendMessage={sendMessage}
        isLoading={isLoading}
        conversationId={conversationId}
        onClearChat={handleChangeClub}
        clubId={selectedClub}
        streamingEnabled={streamingEnabled}
        onToggleStreaming={toggleStreaming}
      />
    </div>
  )
}
