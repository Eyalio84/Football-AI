import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { theme } from '@/config/theme'
import { API_URL } from '@/config/api'
import { useClubTheme } from '@/config/ClubThemeProvider'
import { CLUB_PALETTES, DEFAULT_PALETTE, type ClubPalette } from '@/config/clubThemes'
import { Share2, ExternalLink } from 'lucide-react'

interface Prediction {
  date: string
  home_team: string
  away_team: string
  prediction: string
  probabilities: { home_win: number; draw: number; away_win: number }
  expected_goals: { home: number; away: number }
  most_likely_score: string
}

function getPalette(teamName: string): ClubPalette {
  // Try to match team name to a club palette
  const key = teamName.toLowerCase().replace(/ /g, '_').replace('wolverhampton', 'wolves').replace("nott'm forest", 'nottingham_forest')
  return CLUB_PALETTES[key] || DEFAULT_PALETTE
}

function ProbBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-1.5 flex-1 rounded-full overflow-hidden" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }}>
      <div
        className="h-full rounded-full transition-all duration-700"
        style={{ width: `${Math.max(value * 100, 2)}%`, backgroundColor: color }}
      />
    </div>
  )
}

export function Predictions() {
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<number | null>(null)
  const [clubFilter, setClubFilter] = useState<string>('')
  const { clubId } = useClubTheme()

  useEffect(() => {
    fetch(`${API_URL}/api/v1/predict/v2/upcoming`)
      .then(r => r.json())
      .then(d => {
        if (d.success) setPredictions(d.data.predictions || [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // Auto-set club filter if a club is selected in the theme
  useEffect(() => {
    if (clubId && clubId !== 'analyst') {
      // Map club ID to display name patterns
      const displayName = clubId.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
      setClubFilter(displayName)
    }
  }, [clubId])

  const filtered = clubFilter
    ? predictions.filter(p =>
        p.home_team.toLowerCase().includes(clubFilter.toLowerCase()) ||
        p.away_team.toLowerCase().includes(clubFilter.toLowerCase())
      )
    : predictions

  // Group by date
  const grouped: Record<string, Prediction[]> = {}
  for (const p of filtered) {
    const date = p.date || 'Unknown'
    if (!grouped[date]) grouped[date] = []
    grouped[date].push(p)
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1
            className="font-display text-3xl font-extrabold tracking-wide uppercase"
            style={{ color: theme.colors.text.primary }}
          >
            PREDICTIONS
          </h1>
          <p className="text-sm mt-1" style={{ color: theme.colors.text.muted }}>
            Dixon-Coles + Bookmaker ensemble — 53.9% accuracy, 50% draw precision
          </p>
        </div>
      </div>

      {/* Club filter */}
      <div className="flex items-center gap-2 mb-6">
        <button
          onClick={() => setClubFilter('')}
          className="px-3 py-1 rounded-lg text-xs font-display font-bold tracking-wide uppercase transition-all"
          style={{
            backgroundColor: !clubFilter ? 'var(--club-primary, #10B981)20' : theme.colors.background.elevated,
            color: !clubFilter ? 'var(--club-primary, #10B981)' : theme.colors.text.secondary,
          }}
        >
          ALL MATCHES
        </button>
        {clubId && clubId !== 'analyst' && (
          <button
            onClick={() => {
              const name = clubId.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
              setClubFilter(clubFilter === name ? '' : name)
            }}
            className="px-3 py-1 rounded-lg text-xs font-display font-bold tracking-wide uppercase transition-all"
            style={{
              backgroundColor: clubFilter ? 'var(--club-primary)20' : theme.colors.background.elevated,
              color: clubFilter ? 'var(--club-primary)' : theme.colors.text.secondary,
            }}
          >
            MY CLUB ONLY
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="typing-dot" /><div className="typing-dot ml-1.5" /><div className="typing-dot ml-1.5" />
        </div>
      ) : filtered.length === 0 ? (
        <div
          className="text-center py-12 rounded-xl border"
          style={{ backgroundColor: theme.colors.background.surface, borderColor: theme.colors.border.default }}
        >
          <p className="text-lg" style={{ color: theme.colors.text.secondary }}>No upcoming fixtures found</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([date, matches]) => (
            <div key={date}>
              {/* Date header */}
              <div className="flex items-center gap-3 mb-3">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: 'var(--club-primary)' }} />
                <span className="font-display text-sm font-bold tracking-widest uppercase" style={{ color: theme.colors.text.muted }}>
                  {formatDate(date)}
                </span>
              </div>

              {/* Matches for this date */}
              <div className="space-y-2">
                {matches.map((pred, idx) => {
                  const globalIdx = predictions.indexOf(pred)
                  const isExpanded = expanded === globalIdx
                  const hp = getPalette(pred.home_team)
                  const ap = getPalette(pred.away_team)

                  return (
                    <div
                      key={idx}
                      className="rounded-xl border overflow-hidden transition-all duration-200"
                      style={{
                        backgroundColor: theme.colors.background.surface,
                        borderColor: isExpanded ? 'var(--club-primary, #334155)40' : theme.colors.border.default,
                      }}
                    >
                      {/* Match row — clickable */}
                      <button
                        onClick={() => setExpanded(isExpanded ? null : globalIdx)}
                        className="w-full px-4 py-3 flex items-center gap-3 text-left transition-colors hover:bg-white/[0.02]"
                      >
                        {/* Home team */}
                        <div className="flex items-center gap-2 flex-1 justify-end">
                          <span className="font-display text-sm font-bold tracking-wide text-right truncate" style={{ color: theme.colors.text.primary }}>
                            {pred.home_team}
                          </span>
                          <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ backgroundColor: hp.primary }} />
                        </div>

                        {/* Score prediction */}
                        <div className="px-3 text-center flex-shrink-0">
                          <span className="font-mono text-lg font-bold" style={{ color: theme.colors.text.primary }}>
                            {pred.most_likely_score}
                          </span>
                        </div>

                        {/* Away team */}
                        <div className="flex items-center gap-2 flex-1">
                          <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ backgroundColor: ap.primary }} />
                          <span className="font-display text-sm font-bold tracking-wide truncate" style={{ color: theme.colors.text.primary }}>
                            {pred.away_team}
                          </span>
                        </div>

                        {/* Prediction badge */}
                        <div
                          className="px-2 py-0.5 rounded text-xs font-mono font-bold flex-shrink-0"
                          style={{
                            backgroundColor: pred.prediction.includes('Draw') ? '#94a3b820' : 'var(--club-primary, #10B981)10',
                            color: pred.prediction.includes('Draw') ? '#94a3b8' : theme.colors.text.secondary,
                          }}
                        >
                          {pred.prediction.includes('Draw') ? 'DRAW' : pred.probabilities.home_win >= pred.probabilities.away_win ? 'H' : 'A'}
                        </div>
                      </button>

                      {/* Expanded details */}
                      {isExpanded && (
                        <div className="px-4 pb-4 pt-1 border-t animate-message-in" style={{ borderColor: theme.colors.border.default }}>
                          {/* Probability bars */}
                          <div className="space-y-2 mb-3">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs w-10 text-right" style={{ color: hp.primary }}>
                                {(pred.probabilities.home_win * 100).toFixed(0)}%
                              </span>
                              <ProbBar value={pred.probabilities.home_win} color={hp.primary} />
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs w-10 text-right" style={{ color: '#94a3b8' }}>
                                {(pred.probabilities.draw * 100).toFixed(0)}%
                              </span>
                              <ProbBar value={pred.probabilities.draw} color="#94a3b8" />
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs w-10 text-right" style={{ color: ap.primary }}>
                                {(pred.probabilities.away_win * 100).toFixed(0)}%
                              </span>
                              <ProbBar value={pred.probabilities.away_win} color={ap.primary} />
                            </div>
                          </div>

                          {/* xG + actions */}
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs" style={{ color: theme.colors.text.muted }}>
                              xG: {pred.expected_goals.home} — {pred.expected_goals.away}
                            </span>
                            <Link
                              to={`/card/${pred.home_team}/${pred.away_team}`}
                              className="flex items-center gap-1 text-xs font-display font-bold tracking-wide uppercase transition-all hover:scale-105"
                              style={{ color: 'var(--club-primary, #10B981)' }}
                            >
                              <Share2 size={12} />
                              SHARE CARD
                              <ExternalLink size={10} />
                            </Link>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr + 'T12:00:00')
    const today = new Date()
    const tomorrow = new Date(today)
    tomorrow.setDate(tomorrow.getDate() + 1)

    if (d.toDateString() === today.toDateString()) return 'TODAY'
    if (d.toDateString() === tomorrow.toDateString()) return 'TOMORROW'

    return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
  } catch {
    return dateStr
  }
}
