/**
 * Shareable Prediction Card
 *
 * Route: /card/:home/:away
 * Renders a full-screen, visually striking prediction card designed for
 * social sharing. Dark card with split club-colour gradient, probability
 * bars, AI quote, and verbalogix.com branding.
 */

import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { CLUB_PALETTES, DEFAULT_PALETTE, type ClubPalette } from '@/config/clubThemes'
import { theme } from '@/config/theme'
import { API_URL } from '@/config/api'

interface CardData {
  home_team: string
  away_team: string
  home_club_id: string
  away_club_id: string
  prediction: string
  probabilities: { home_win: number; draw: number; away_win: number }
  expected_goals: { home: number; away: number }
  most_likely_score: string
  ai_take: string
  date: string | null
  time: string | null
}

function getPalette(clubId: string): ClubPalette {
  return CLUB_PALETTES[clubId] || DEFAULT_PALETTE
}

function ProbBar({ value, color, label }: { value: number; color: string; label: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="font-display text-xs font-bold tracking-wide uppercase w-12 text-right" style={{ color }}>
        {label}
      </span>
      <div className="flex-1 h-3 rounded-full overflow-hidden" style={{ backgroundColor: 'rgba(255,255,255,0.08)' }}>
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{
            width: `${Math.max(value * 100, 3)}%`,
            backgroundColor: color,
            boxShadow: `0 0 8px ${color}60`,
          }}
        />
      </div>
      <span className="font-mono text-sm font-bold w-12" style={{ color }}>
        {(value * 100).toFixed(0)}%
      </span>
    </div>
  )
}

export function PredictionCard() {
  const { home, away } = useParams<{ home: string; away: string }>()
  const [data, setData] = useState<CardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!home || !away) return
    fetch(`${API_URL}/api/v1/predict/v2/${home}/${away}/card`)
      .then(r => r.json())
      .then(d => { if (d.success) setData(d.data) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [home, away])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#0a0e17' }}>
        <div className="flex gap-1.5">
          <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#0a0e17' }}>
        <p className="font-display text-lg" style={{ color: theme.colors.text.muted }}>Match not found</p>
      </div>
    )
  }

  const homePalette = getPalette(data.home_club_id)
  const awayPalette = getPalette(data.away_club_id)

  const handleShare = async () => {
    const url = window.location.href
    const text = `${data.home_team} vs ${data.away_team} — ${data.prediction} (${(Math.max(data.probabilities.home_win, data.probabilities.draw, data.probabilities.away_win) * 100).toFixed(0)}%)\n\n"${data.ai_take}"\n\nPowered by Football-AI`
    if (navigator.share) {
      await navigator.share({ title: `${data.home_team} vs ${data.away_team}`, text, url })
    } else {
      await navigator.clipboard.writeText(`${text}\n${url}`)
    }
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-4"
      style={{ backgroundColor: '#0a0e17' }}
    >
      {/* The Card */}
      <div
        className="w-full max-w-lg rounded-2xl overflow-hidden border animate-fade-up"
        style={{
          background: `linear-gradient(135deg, ${homePalette.primary}12 0%, #0f1520 40%, #0f1520 60%, ${awayPalette.primary}12 100%)`,
          borderColor: 'rgba(255,255,255,0.08)',
          boxShadow: `0 0 60px ${homePalette.primary}10, 0 0 60px ${awayPalette.primary}10`,
        }}
      >
        {/* Top gradient bar */}
        <div
          className="h-1"
          style={{
            background: `linear-gradient(90deg, ${homePalette.primary} 0%, transparent 40%, transparent 60%, ${awayPalette.primary} 100%)`,
          }}
        />

        {/* Header: date + model */}
        <div className="px-6 pt-5 pb-2 flex items-center justify-between">
          <span className="font-mono text-xs" style={{ color: theme.colors.text.muted }}>
            {data.date || 'Upcoming'}
          </span>
          <span className="font-display text-[10px] font-bold tracking-widest uppercase" style={{ color: theme.colors.text.muted }}>
            FOOTBALL-AI PREDICTION
          </span>
        </div>

        {/* Teams */}
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="text-center flex-1">
            <div className="w-4 h-4 rounded-sm mx-auto mb-2" style={{ backgroundColor: homePalette.primary }} />
            <h2 className="font-display text-xl font-extrabold tracking-wide uppercase" style={{ color: homePalette.primary }}>
              {data.home_team}
            </h2>
            <span className="font-mono text-xs" style={{ color: theme.colors.text.muted }}>HOME</span>
          </div>

          <div className="px-4 text-center">
            <div className="font-mono text-3xl font-bold" style={{ color: theme.colors.text.primary }}>
              {data.most_likely_score}
            </div>
            <span className="font-display text-[10px] font-bold tracking-widest uppercase" style={{ color: theme.colors.text.muted }}>
              LIKELY SCORE
            </span>
          </div>

          <div className="text-center flex-1">
            <div className="w-4 h-4 rounded-sm mx-auto mb-2" style={{ backgroundColor: awayPalette.primary }} />
            <h2 className="font-display text-xl font-extrabold tracking-wide uppercase" style={{ color: awayPalette.primary }}>
              {data.away_team}
            </h2>
            <span className="font-mono text-xs" style={{ color: theme.colors.text.muted }}>AWAY</span>
          </div>
        </div>

        {/* Probability bars */}
        <div className="px-6 py-4 space-y-2.5">
          <ProbBar value={data.probabilities.home_win} color={homePalette.primary} label="HOME" />
          <ProbBar value={data.probabilities.draw} color="#94a3b8" label="DRAW" />
          <ProbBar value={data.probabilities.away_win} color={awayPalette.primary} label="AWAY" />
        </div>

        {/* xG */}
        <div className="px-6 py-2 flex items-center justify-center gap-6">
          <span className="font-mono text-sm" style={{ color: homePalette.primary }}>
            xG {data.expected_goals.home}
          </span>
          <span className="font-display text-xs font-bold tracking-widest uppercase" style={{ color: theme.colors.text.muted }}>
            EXPECTED GOALS
          </span>
          <span className="font-mono text-sm" style={{ color: awayPalette.primary }}>
            xG {data.expected_goals.away}
          </span>
        </div>

        {/* Prediction + AI Take */}
        <div
          className="mx-6 my-4 rounded-xl px-5 py-4"
          style={{
            backgroundColor: 'rgba(255,255,255,0.03)',
            borderLeft: `3px solid ${data.prediction.includes(data.home_team) ? homePalette.primary : data.prediction === 'Draw' ? '#94a3b8' : awayPalette.primary}`,
          }}
        >
          <div className="font-display text-sm font-bold tracking-wide uppercase mb-1" style={{ color: theme.colors.text.primary }}>
            {data.prediction}
          </div>
          <p className="text-sm italic" style={{ color: theme.colors.text.secondary }}>
            "{data.ai_take}"
          </p>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 flex items-center justify-between border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <span className="font-display text-xs font-bold tracking-wide uppercase" style={{ color: theme.colors.text.muted }}>
            football-ai
          </span>
          <span className="font-mono text-[10px]" style={{ color: theme.colors.text.muted }}>
            verbalogix.com
          </span>
        </div>
      </div>

      {/* Share button */}
      <button
        onClick={handleShare}
        className="mt-6 px-6 py-2.5 rounded-xl font-display font-bold tracking-wide uppercase text-sm transition-all hover:scale-105 animate-fade-up"
        style={{
          animationDelay: '300ms',
          background: `linear-gradient(135deg, ${homePalette.primary} 0%, ${awayPalette.primary} 100%)`,
          color: '#fff',
        }}
      >
        SHARE PREDICTION
      </button>

      {/* Back link */}
      <a
        href="/"
        className="mt-3 font-display text-xs tracking-wide uppercase animate-fade-up"
        style={{ animationDelay: '400ms', color: theme.colors.text.muted }}
      >
        BACK TO FOOTBALL-AI
      </a>
    </div>
  )
}
