import { useState } from 'react'
import { theme } from '@/config/theme'
import { useClubTheme } from '@/config/ClubThemeProvider'
import { CLUB_PALETTES, type ClubPalette } from '@/config/clubThemes'
import { Swords } from 'lucide-react'
import { API_URL } from '@/config/api'

interface Exchange {
  club: string
  club_display: string
  text: string
  round: number
}

// All clubs available for debate
const DEBATE_CLUBS = [
  { id: 'arsenal', name: 'Arsenal' },
  { id: 'chelsea', name: 'Chelsea' },
  { id: 'liverpool', name: 'Liverpool' },
  { id: 'manchester_united', name: 'Man United' },
  { id: 'manchester_city', name: 'Man City' },
  { id: 'tottenham', name: 'Tottenham' },
  { id: 'newcastle', name: 'Newcastle' },
  { id: 'west_ham', name: 'West Ham' },
  { id: 'everton', name: 'Everton' },
  { id: 'aston_villa', name: 'Aston Villa' },
  { id: 'brighton', name: 'Brighton' },
  { id: 'wolves', name: 'Wolves' },
  { id: 'crystal_palace', name: 'Crystal Palace' },
  { id: 'fulham', name: 'Fulham' },
  { id: 'nottingham_forest', name: 'Forest' },
  { id: 'brentford', name: 'Brentford' },
  { id: 'bournemouth', name: 'Bournemouth' },
  { id: 'sunderland', name: 'Sunderland' },
  { id: 'leeds', name: 'Leeds' },
  { id: 'burnley', name: 'Burnley' },
]

const SUGGESTED_TOPICS = [
  "Who is the bigger club?",
  "Who has the better history?",
  "Who has the best fans?",
  "Who will finish higher this season?",
  "Who has the better manager?",
  "Who has the greatest legend of all time?",
]

function getPalette(clubId: string): ClubPalette {
  return CLUB_PALETTES[clubId] || { primary: '#666', secondary: '#999', accent: '#fff', gradient: '#666', glowColor: 'transparent', textOnPrimary: '#fff' }
}

export function Debate() {
  const [clubA, setClubA] = useState<string>('')
  const [clubB, setClubB] = useState<string>('')
  const [topic, setTopic] = useState('')
  const [exchanges, setExchanges] = useState<Exchange[]>([])
  const [loading, setLoading] = useState(false)
  const [visibleCount, setVisibleCount] = useState(0)
  const { setClubId } = useClubTheme()

  const paletteA = getPalette(clubA)
  const paletteB = getPalette(clubB)

  const canStart = clubA && clubB && clubA !== clubB && topic.trim()

  const startDebate = async () => {
    if (!canStart) return
    setLoading(true)
    setExchanges([])
    setVisibleCount(0)
    setClubId(null) // Neutral for debate view

    try {
      const resp = await fetch(`${API_URL}/api/v1/debate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          club_a: clubA,
          club_b: clubB,
          topic: topic,
          rounds: 3,
        }),
      })
      const json = await resp.json()

      if (json.success && json.data?.exchanges) {
        setExchanges(json.data.exchanges)
        // Reveal messages one by one
        revealMessages(json.data.exchanges.length)
      }
    } catch (err) {
      console.error('Debate failed:', err)
    } finally {
      setLoading(false)
    }
  }

  const revealMessages = (total: number) => {
    let count = 0
    const interval = setInterval(() => {
      count++
      setVisibleCount(count)
      if (count >= total) clearInterval(interval)
    }, 800)
  }

  const hasStarted = exchanges.length > 0 || loading

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h1
          className="font-display text-3xl sm:text-4xl font-extrabold tracking-wide uppercase mb-2"
          style={{ color: theme.colors.text.primary }}
        >
          FAN DEBATE
        </h1>
        <p
          className="text-sm italic"
          style={{ color: theme.colors.text.muted }}
        >
          Two scarves. One question. No mercy.
        </p>
      </div>

      {/* Setup panel */}
      {!hasStarted && (
        <div
          className="rounded-xl border p-6 mb-6 animate-fade-up"
          style={{
            backgroundColor: theme.colors.background.surface,
            borderColor: theme.colors.border.default,
          }}
        >
          {/* Club selectors */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
            {/* Club A */}
            <div>
              <label
                className="font-display text-xs font-bold tracking-widest uppercase block mb-2"
                style={{ color: theme.colors.text.secondary }}
              >
                FIRST CORNER
              </label>
              <div className="grid grid-cols-4 gap-1.5">
                {DEBATE_CLUBS.map((c) => {
                  const p = getPalette(c.id)
                  const selected = clubA === c.id
                  const disabled = clubB === c.id
                  return (
                    <button
                      key={c.id}
                      onClick={() => setClubA(c.id)}
                      disabled={disabled}
                      className="px-2 py-1.5 rounded-lg text-xs font-display font-bold tracking-wide truncate transition-all disabled:opacity-20"
                      style={{
                        backgroundColor: selected ? p.primary : theme.colors.background.elevated,
                        color: selected ? p.textOnPrimary : theme.colors.text.secondary,
                        border: `1px solid ${selected ? p.primary : 'transparent'}`,
                      }}
                    >
                      {c.name}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Club B */}
            <div>
              <label
                className="font-display text-xs font-bold tracking-widest uppercase block mb-2"
                style={{ color: theme.colors.text.secondary }}
              >
                SECOND CORNER
              </label>
              <div className="grid grid-cols-4 gap-1.5">
                {DEBATE_CLUBS.map((c) => {
                  const p = getPalette(c.id)
                  const selected = clubB === c.id
                  const disabled = clubA === c.id
                  return (
                    <button
                      key={c.id}
                      onClick={() => setClubB(c.id)}
                      disabled={disabled}
                      className="px-2 py-1.5 rounded-lg text-xs font-display font-bold tracking-wide truncate transition-all disabled:opacity-20"
                      style={{
                        backgroundColor: selected ? p.primary : theme.colors.background.elevated,
                        color: selected ? p.textOnPrimary : theme.colors.text.secondary,
                        border: `1px solid ${selected ? p.primary : 'transparent'}`,
                      }}
                    >
                      {c.name}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {/* VS display */}
          {clubA && clubB && (
            <div className="flex items-center justify-center gap-4 mb-6 animate-fade-up">
              <span className="font-display text-lg font-bold" style={{ color: paletteA.primary }}>
                {DEBATE_CLUBS.find(c => c.id === clubA)?.name}
              </span>
              <Swords size={24} style={{ color: theme.colors.text.muted }} />
              <span className="font-display text-lg font-bold" style={{ color: paletteB.primary }}>
                {DEBATE_CLUBS.find(c => c.id === clubB)?.name}
              </span>
            </div>
          )}

          {/* Topic */}
          <div className="mb-4">
            <label
              className="font-display text-xs font-bold tracking-widest uppercase block mb-2"
              style={{ color: theme.colors.text.secondary }}
            >
              THE QUESTION
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., Who is the bigger club?"
              className="w-full px-4 py-3 rounded-xl focus:outline-none focus:ring-2 text-sm"
              style={{
                backgroundColor: theme.colors.background.elevated,
                color: theme.colors.text.primary,
                '--tw-ring-color': theme.colors.text.muted,
              } as React.CSSProperties}
            />
          </div>

          {/* Topic suggestions */}
          <div className="flex flex-wrap gap-2 mb-6">
            {SUGGESTED_TOPICS.map((t) => (
              <button
                key={t}
                onClick={() => setTopic(t)}
                className="px-3 py-1 rounded-full text-xs transition-all hover:scale-105 border"
                style={{
                  backgroundColor: topic === t ? theme.colors.background.elevated : 'transparent',
                  color: theme.colors.text.secondary,
                  borderColor: theme.colors.border.default,
                }}
              >
                {t}
              </button>
            ))}
          </div>

          {/* Start button */}
          <button
            onClick={startDebate}
            disabled={!canStart}
            className="w-full py-3 rounded-xl font-display font-bold tracking-wide uppercase text-sm transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-30"
            style={{
              background: clubA && clubB
                ? `linear-gradient(135deg, ${paletteA.primary} 0%, ${paletteB.primary} 100%)`
                : theme.colors.background.elevated,
              color: '#fff',
            }}
          >
            START DEBATE
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && exchanges.length === 0 && (
        <div className="text-center py-12 animate-fade-up">
          <div className="flex items-center justify-center gap-4 mb-4">
            <div className="w-4 h-4 rounded-full animate-mood-pulse" style={{ backgroundColor: paletteA.primary }} />
            <Swords size={20} style={{ color: theme.colors.text.muted }} className="animate-pulse" />
            <div className="w-4 h-4 rounded-full animate-mood-pulse" style={{ backgroundColor: paletteB.primary }} />
          </div>
          <p className="font-display text-sm tracking-wide uppercase" style={{ color: theme.colors.text.secondary }}>
            The fans are warming up...
          </p>
        </div>
      )}

      {/* Debate exchanges */}
      {exchanges.length > 0 && (
        <div className="space-y-4">
          {/* Topic banner */}
          <div
            className="rounded-xl p-4 text-center border mb-6"
            style={{
              background: `linear-gradient(135deg, ${paletteA.primary}15 0%, ${paletteB.primary}15 100%)`,
              borderColor: theme.colors.border.default,
            }}
          >
            <p className="font-display text-xs font-bold tracking-widest uppercase mb-1" style={{ color: theme.colors.text.muted }}>
              THE DEBATE
            </p>
            <p className="text-base italic" style={{ color: theme.colors.text.primary }}>
              "{exchanges.length > 0 ? topic : ''}"
            </p>
          </div>

          {exchanges.slice(0, visibleCount).map((ex, idx) => {
            const isClubA = ex.club === clubA
            const palette = isClubA ? paletteA : paletteB

            return (
              <div
                key={idx}
                className={`flex ${isClubA ? 'justify-start' : 'justify-end'} animate-message-in`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-5 py-4 ${isClubA ? 'rounded-bl-sm' : 'rounded-br-sm'}`}
                  style={{
                    backgroundColor: theme.colors.background.surface,
                    borderLeft: isClubA ? `4px solid ${palette.primary}` : undefined,
                    borderRight: !isClubA ? `4px solid ${palette.primary}` : undefined,
                    boxShadow: `0 2px 8px ${palette.primary}15`,
                  }}
                >
                  {/* Speaker label */}
                  <div className="flex items-center gap-2 mb-2">
                    <div
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: palette.primary }}
                    />
                    <span
                      className="font-display text-xs font-bold tracking-wide uppercase"
                      style={{ color: palette.primary }}
                    >
                      {ex.club_display} FAN
                    </span>
                    <span
                      className="font-mono text-xs"
                      style={{ color: theme.colors.text.muted }}
                    >
                      R{ex.round}
                    </span>
                  </div>

                  {/* Message text */}
                  <p
                    className="text-sm leading-relaxed whitespace-pre-line"
                    style={{ color: theme.colors.text.primary }}
                  >
                    {ex.text}
                  </p>
                </div>
              </div>
            )
          })}

          {/* New debate button */}
          {visibleCount >= exchanges.length && (
            <div className="text-center pt-6 animate-fade-up">
              <button
                onClick={() => { setExchanges([]); setVisibleCount(0) }}
                className="px-6 py-2 rounded-xl font-display font-bold tracking-wide uppercase text-xs transition-all hover:scale-105 border"
                style={{
                  borderColor: theme.colors.border.strong,
                  color: theme.colors.text.secondary,
                }}
              >
                NEW DEBATE
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
