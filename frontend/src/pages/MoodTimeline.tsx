import { useState, useEffect, useCallback } from 'react'
import { theme } from '@/config/theme'
import { useClubTheme } from '@/config/ClubThemeProvider'
import { CLUB_PALETTES } from '@/config/clubThemes'
import { API_URL } from '@/config/api'

interface MoodPoint {
  matchweek: number
  date: string
  opponent: string
  is_home: boolean
  score: string
  result: 'W' | 'D' | 'L'
  mood_value: number
  mood_label: string
  form: string
}

interface TimelineData {
  club: string
  club_display: string
  season: string
  total_matches: number
  points: MoodPoint[]
}

// ─── SVG Chart Constants ──────────────────────────────────────────

const CHART = {
  width: 900,
  height: 340,
  padLeft: 50,
  padRight: 20,
  padTop: 20,
  padBottom: 40,
}

const PLOT = {
  x: CHART.padLeft,
  y: CHART.padTop,
  w: CHART.width - CHART.padLeft - CHART.padRight,
  h: CHART.height - CHART.padTop - CHART.padBottom,
}

const MOOD_ZONES = [
  { label: 'EUPHORIC', min: 0.8, max: 1.0, color: 'rgba(34, 197, 94, 0.06)' },
  { label: 'CONFIDENT', min: 0.6, max: 0.8, color: 'rgba(59, 130, 246, 0.04)' },
  { label: 'STEADY', min: 0.4, max: 0.6, color: 'rgba(148, 163, 184, 0.03)' },
  { label: 'ANXIOUS', min: 0.2, max: 0.4, color: 'rgba(245, 158, 11, 0.04)' },
  { label: 'DESPAIRING', min: 0.0, max: 0.2, color: 'rgba(239, 68, 68, 0.06)' },
]

const RESULT_COLORS = { W: '#22c55e', D: '#eab308', L: '#ef4444' }

// ─── Club Selection ──────────────────────────────────────────────

const CLUBS = [
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

// ─── Helpers ──────────────────────────────────────────────────────

function toX(matchweek: number, total: number): number {
  return PLOT.x + ((matchweek - 1) / Math.max(total - 1, 1)) * PLOT.w
}

function toY(mood: number): number {
  return PLOT.y + PLOT.h - mood * PLOT.h
}

function buildPath(points: MoodPoint[]): string {
  if (points.length === 0) return ''
  const total = points.length
  return points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${toX(p.matchweek, total).toFixed(1)} ${toY(p.mood_value).toFixed(1)}`)
    .join(' ')
}

function buildAreaPath(points: MoodPoint[]): string {
  if (points.length === 0) return ''
  const total = points.length
  const line = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${toX(p.matchweek, total).toFixed(1)} ${toY(p.mood_value).toFixed(1)}`)
    .join(' ')
  const bottomRight = `L ${toX(points[points.length - 1].matchweek, total).toFixed(1)} ${toY(0).toFixed(1)}`
  const bottomLeft = `L ${toX(1, total).toFixed(1)} ${toY(0).toFixed(1)} Z`
  return `${line} ${bottomRight} ${bottomLeft}`
}

// ─── Main Component ───────────────────────────────────────────────

export function MoodTimeline() {
  const [selectedClub, setSelectedClub] = useState('arsenal')
  const [data, setData] = useState<TimelineData | null>(null)
  const [loading, setLoading] = useState(false)
  const [hovered, setHovered] = useState<number | null>(null)
  const { setClubId, palette } = useClubTheme()

  const fetchTimeline = useCallback(async (club: string) => {
    setLoading(true)
    setHovered(null)
    try {
      const resp = await fetch(`${API_URL}/api/v1/fan/${club}/mood-timeline?season=2024`)
      const json = await resp.json()
      if (json.success) setData(json.data)
    } catch (err) {
      console.error('Failed to fetch timeline:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    setClubId(selectedClub)
    fetchTimeline(selectedClub)
  }, [selectedClub, setClubId, fetchTimeline])

  const hoveredPoint = hovered !== null && data ? data.points[hovered] : null

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1
          className="font-display text-3xl font-extrabold tracking-wide uppercase"
          style={{ color: theme.colors.text.primary }}
        >
          THE EMOTIONAL SEASON
        </h1>
        <p className="text-sm mt-1" style={{ color: theme.colors.text.muted }}>
          How it felt to be a fan — every match, every mood shift, computed from real results.
        </p>
      </div>

      {/* Club selector */}
      <div className="flex flex-wrap gap-1.5 mb-6">
        {CLUBS.map(c => {
          const cp = CLUB_PALETTES[c.id]
          const sel = selectedClub === c.id
          return (
            <button
              key={c.id}
              onClick={() => setSelectedClub(c.id)}
              className="px-2.5 py-1 rounded-lg text-xs font-display font-bold tracking-wide uppercase transition-all"
              style={{
                backgroundColor: sel ? (cp?.primary || '#666') : theme.colors.background.elevated,
                color: sel ? (cp?.textOnPrimary || '#fff') : theme.colors.text.secondary,
              }}
            >
              {c.name}
            </button>
          )
        })}
      </div>

      {/* Season label */}
      {data && (
        <div className="flex items-center gap-3 mb-4 animate-fade-up">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: palette.primary }} />
          <span className="font-display text-lg font-bold tracking-wide uppercase" style={{ color: palette.primary }}>
            {data.club_display}
          </span>
          <span className="font-mono text-sm" style={{ color: theme.colors.text.muted }}>
            {data.season} &middot; {data.total_matches} matches
          </span>
        </div>
      )}

      {/* Chart */}
      {loading ? (
        <div className="flex items-center justify-center h-80">
          <div className="typing-dot" /><div className="typing-dot ml-1.5" /><div className="typing-dot ml-1.5" />
        </div>
      ) : data && data.points.length > 0 ? (
        <div
          className="rounded-xl border overflow-hidden relative animate-fade-up"
          style={{
            backgroundColor: theme.colors.background.surface,
            borderColor: theme.colors.border.default,
          }}
        >
          {/* Stadium glow behind chart */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              background: `radial-gradient(ellipse 70% 50% at 50% 20%, ${palette.glowColor} 0%, transparent 70%)`,
            }}
          />

          <svg
            viewBox={`0 0 ${CHART.width} ${CHART.height}`}
            className="w-full h-auto relative z-10"
            style={{ minHeight: 280 }}
            onMouseLeave={() => setHovered(null)}
          >
            <defs>
              {/* Glow filter for the mood line */}
              <filter id="lineGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>

              {/* Gradient fill under the line */}
              <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={palette.primary} stopOpacity="0.15" />
                <stop offset="100%" stopColor={palette.primary} stopOpacity="0" />
              </linearGradient>
            </defs>

            {/* Mood zone bands */}
            {MOOD_ZONES.map(zone => (
              <g key={zone.label}>
                <rect
                  x={PLOT.x}
                  y={toY(zone.max)}
                  width={PLOT.w}
                  height={toY(zone.min) - toY(zone.max)}
                  fill={zone.color}
                />
                <text
                  x={PLOT.x + 6}
                  y={toY((zone.min + zone.max) / 2) + 3}
                  fill={theme.colors.text.muted}
                  fontSize="8"
                  fontFamily="var(--font-display)"
                  letterSpacing="0.1em"
                  opacity="0.5"
                >
                  {zone.label}
                </text>
              </g>
            ))}

            {/* Horizontal gridlines */}
            {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map(v => (
              <line
                key={v}
                x1={PLOT.x}
                y1={toY(v)}
                x2={PLOT.x + PLOT.w}
                y2={toY(v)}
                stroke={theme.colors.border.default}
                strokeWidth="0.5"
                strokeDasharray={v === 0.5 ? '4,4' : undefined}
                opacity="0.4"
              />
            ))}

            {/* Area fill under line */}
            <path
              d={buildAreaPath(data.points)}
              fill="url(#areaFill)"
            />

            {/* Mood line (glowing) */}
            <path
              d={buildPath(data.points)}
              fill="none"
              stroke={palette.primary}
              strokeWidth="2.5"
              strokeLinejoin="round"
              strokeLinecap="round"
              filter="url(#lineGlow)"
              opacity="0.9"
            />

            {/* Mood line (crisp) */}
            <path
              d={buildPath(data.points)}
              fill="none"
              stroke={palette.primary}
              strokeWidth="1.5"
              strokeLinejoin="round"
              strokeLinecap="round"
            />

            {/* Result dots */}
            {data.points.map((p, i) => {
              const cx = toX(p.matchweek, data.points.length)
              const cy = toY(p.mood_value)
              const isHovered = hovered === i
              return (
                <g key={i}>
                  {/* Invisible larger hit area */}
                  <circle
                    cx={cx}
                    cy={cy}
                    r={12}
                    fill="transparent"
                    onMouseEnter={() => setHovered(i)}
                    style={{ cursor: 'pointer' }}
                  />
                  {/* Glow ring on hover */}
                  {isHovered && (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={10}
                      fill={RESULT_COLORS[p.result]}
                      opacity={0.15}
                    />
                  )}
                  {/* Result dot */}
                  <circle
                    cx={cx}
                    cy={cy}
                    r={isHovered ? 5 : 3.5}
                    fill={RESULT_COLORS[p.result]}
                    stroke={theme.colors.background.surface}
                    strokeWidth={isHovered ? 2 : 1}
                    style={{ transition: 'r 0.15s ease' }}
                  />
                </g>
              )
            })}

            {/* X-axis labels (every 5 matchweeks) */}
            {data.points.filter((_, i) => i % 5 === 0 || i === data.points.length - 1).map(p => (
              <text
                key={p.matchweek}
                x={toX(p.matchweek, data.points.length)}
                y={CHART.height - 8}
                textAnchor="middle"
                fill={theme.colors.text.muted}
                fontSize="9"
                fontFamily="var(--font-mono)"
              >
                {p.matchweek}
              </text>
            ))}

            {/* X-axis title */}
            <text
              x={PLOT.x + PLOT.w / 2}
              y={CHART.height}
              textAnchor="middle"
              fill={theme.colors.text.muted}
              fontSize="9"
              fontFamily="var(--font-display)"
              letterSpacing="0.08em"
            >
              MATCHWEEK
            </text>

            {/* Hover vertical line */}
            {hoveredPoint && (
              <line
                x1={toX(hoveredPoint.matchweek, data.points.length)}
                y1={PLOT.y}
                x2={toX(hoveredPoint.matchweek, data.points.length)}
                y2={PLOT.y + PLOT.h}
                stroke={palette.primary}
                strokeWidth="1"
                strokeDasharray="3,3"
                opacity="0.4"
              />
            )}
          </svg>

          {/* Hover tooltip */}
          {hoveredPoint && (
            <div
              className="absolute z-20 pointer-events-none animate-message-in"
              style={{
                left: `${(toX(hoveredPoint.matchweek, data.points.length) / CHART.width) * 100}%`,
                top: 16,
                transform: hoveredPoint.matchweek > data.points.length * 0.7 ? 'translateX(-100%)' : 'translateX(-50%)',
              }}
            >
              <div
                className="rounded-lg px-4 py-3 border shadow-xl"
                style={{
                  backgroundColor: theme.colors.background.elevated + 'F5',
                  borderColor: RESULT_COLORS[hoveredPoint.result] + '40',
                  backdropFilter: 'blur(8px)',
                  minWidth: 200,
                }}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <span
                    className="font-display text-xs font-bold tracking-widest uppercase"
                    style={{ color: theme.colors.text.muted }}
                  >
                    MW{hoveredPoint.matchweek}
                  </span>
                  <span className="font-mono text-xs" style={{ color: theme.colors.text.muted }}>
                    {hoveredPoint.date}
                  </span>
                </div>
                <div className="font-display text-sm font-bold mb-1" style={{ color: theme.colors.text.primary }}>
                  {hoveredPoint.score}
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: RESULT_COLORS[hoveredPoint.result] }}
                  />
                  <span
                    className="font-mono text-xs font-bold uppercase"
                    style={{ color: RESULT_COLORS[hoveredPoint.result] }}
                  >
                    {hoveredPoint.result === 'W' ? 'WIN' : hoveredPoint.result === 'D' ? 'DRAW' : 'LOSS'}
                  </span>
                  <span className="text-xs" style={{ color: theme.colors.text.muted }}>
                    &rarr;
                  </span>
                  <span
                    className="font-display text-xs font-bold uppercase"
                    style={{ color: theme.colors.text.secondary }}
                  >
                    {hoveredPoint.mood_label}
                  </span>
                </div>
                <div className="flex gap-0.5 mt-1.5">
                  {hoveredPoint.form.split('').map((r, j) => (
                    <div
                      key={j}
                      className="w-3 h-3 rounded-full text-center"
                      style={{
                        backgroundColor: RESULT_COLORS[r as 'W' | 'D' | 'L'] || '#666',
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Legend */}
          <div className="flex items-center justify-center gap-6 py-3 border-t" style={{ borderColor: theme.colors.border.default }}>
            {[
              { label: 'WIN', color: '#22c55e' },
              { label: 'DRAW', color: '#eab308' },
              { label: 'LOSS', color: '#ef4444' },
            ].map(l => (
              <div key={l.label} className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: l.color }} />
                <span className="font-display text-xs font-bold tracking-wide uppercase" style={{ color: theme.colors.text.muted }}>
                  {l.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Season summary stats */}
      {data && data.points.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 animate-fade-up" style={{ animationDelay: '200ms' }}>
          {(() => {
            const wins = data.points.filter(p => p.result === 'W').length
            const draws = data.points.filter(p => p.result === 'D').length
            const losses = data.points.filter(p => p.result === 'L').length
            const peakMood = data.points.reduce((max, p) => p.mood_value > max.mood_value ? p : max)
            const lowMood = data.points.reduce((min, p) => p.mood_value < min.mood_value ? p : min)
            const avgMood = data.points.reduce((sum, p) => sum + p.mood_value, 0) / data.points.length

            return [
              { label: 'RECORD', value: `${wins}W ${draws}D ${losses}L`, sub: `${data.total_matches} played` },
              { label: 'PEAK MOOD', value: peakMood.mood_label.toUpperCase(), sub: `MW${peakMood.matchweek} (${peakMood.mood_value.toFixed(2)})` },
              { label: 'LOW POINT', value: lowMood.mood_label.toUpperCase(), sub: `MW${lowMood.matchweek} (${lowMood.mood_value.toFixed(2)})` },
              { label: 'AVG MOOD', value: (avgMood >= 0.6 ? 'CONFIDENT' : avgMood >= 0.4 ? 'STEADY' : 'ANXIOUS'), sub: `Score: ${avgMood.toFixed(2)}` },
            ].map((stat, i) => (
              <div
                key={i}
                className="rounded-xl p-4 border text-center"
                style={{
                  backgroundColor: theme.colors.background.surface,
                  borderColor: theme.colors.border.default,
                }}
              >
                <div className="font-display text-xs font-bold tracking-widest uppercase mb-1" style={{ color: theme.colors.text.muted }}>
                  {stat.label}
                </div>
                <div className="font-mono text-lg font-bold" style={{ color: theme.colors.text.primary }}>
                  {stat.value}
                </div>
                <div className="text-xs mt-0.5" style={{ color: theme.colors.text.muted }}>
                  {stat.sub}
                </div>
              </div>
            ))
          })()}
        </div>
      )}
    </div>
  )
}
