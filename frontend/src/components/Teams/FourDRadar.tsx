/**
 * 4D Coordinate Visualizer
 *
 * Diamond-shaped SVG radar showing the AI's current position
 * in the 4D Persona space: X=Emotional, Y=Relational, Z=Linguistic, T=Temporal.
 *
 * Compact (chat header) and expanded (team profile) modes.
 */

import { useEffect, useState } from 'react'
import { theme } from '@/config/theme'
import { useClubTheme } from '@/config/ClubThemeProvider'
import { API_URL } from '@/config/api'

interface FourDState {
  x: number  // Emotional intensity (0-1)
  y: number  // Relational activation (0-1)
  z: number  // Linguistic distinctiveness (0-1)
  t: number  // Temporal momentum (0-1, mapped from -1..1)
}

interface FourDRadarProps {
  clubId: string
  size?: number    // SVG viewport size
  compact?: boolean
}

const AXES = [
  { key: 'x', label: 'EMOTIONAL', shortLabel: 'X', angle: -90, color: '#ef4444' },
  { key: 'y', label: 'RELATIONAL', shortLabel: 'Y', angle: 0, color: '#f59e0b' },
  { key: 'z', label: 'LINGUISTIC', shortLabel: 'Z', angle: 90, color: '#3b82f6' },
  { key: 't', label: 'TEMPORAL', shortLabel: 'T', angle: 180, color: '#8b5cf6' },
] as const

function polarToXY(angleDeg: number, radius: number, cx: number, cy: number): [number, number] {
  const rad = (angleDeg * Math.PI) / 180
  return [cx + radius * Math.cos(rad), cy + radius * Math.sin(rad)]
}

export function FourDRadar({ clubId, size = 160, compact = false }: FourDRadarProps) {
  const [state, setState] = useState<FourDState>({ x: 0, y: 0, z: 0, t: 0.5 })
  const [loading, setLoading] = useState(true)
  const { palette } = useClubTheme()

  useEffect(() => {
    if (!clubId) return
    setLoading(true)
    fetch(`${API_URL}/api/v1/fan/${clubId}/4d-state`)
      .then(r => r.json())
      .then(d => {
        const p = d?.position_4d
        if (p) {
          setState({
            x: p.x?.intensity ?? 0.5,
            y: p.y?.activated ? (p.y?.intensity ?? 0.8) : 0.1,
            z: p.z?.distinctiveness ?? 0.5,
            t: Math.max(0, Math.min(1, 0.5 + (p.t?.momentum?.x ?? 0) * 0.5)),
          })
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [clubId])

  const cx = size / 2
  const cy = size / 2
  const maxR = size * 0.38
  const ringRadii = compact ? [maxR] : [maxR * 0.33, maxR * 0.66, maxR]

  // Build the data polygon
  const dataPoints = AXES.map(axis => {
    const val = state[axis.key as keyof FourDState]
    const r = val * maxR
    return polarToXY(axis.angle, r, cx, cy)
  })
  const polygonPath = dataPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ') + ' Z'

  // Build the max polygon (for reference outline)
  const maxPoints = AXES.map(axis => polarToXY(axis.angle, maxR, cx, cy))
  const maxPath = maxPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ') + ' Z'

  if (loading) {
    return (
      <div
        className="flex items-center justify-center"
        style={{ width: size, height: size }}
      >
        <div className="typing-dot" />
      </div>
    )
  }

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full">
        <defs>
          <filter id="radarGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Ring guides */}
        {ringRadii.map((r, i) => (
          <circle
            key={i}
            cx={cx} cy={cy} r={r}
            fill="none"
            stroke={theme.colors.border.default}
            strokeWidth="0.5"
            opacity="0.3"
          />
        ))}

        {/* Axis lines */}
        {AXES.map(axis => {
          const [ex, ey] = polarToXY(axis.angle, maxR, cx, cy)
          return (
            <line
              key={axis.key}
              x1={cx} y1={cy} x2={ex} y2={ey}
              stroke={theme.colors.border.default}
              strokeWidth="0.5"
              opacity="0.3"
            />
          )
        })}

        {/* Max outline */}
        <path
          d={maxPath}
          fill="none"
          stroke={theme.colors.border.default}
          strokeWidth="0.5"
          opacity="0.2"
        />

        {/* Data polygon (filled) */}
        <path
          d={polygonPath}
          fill={palette.primary}
          fillOpacity="0.15"
          stroke={palette.primary}
          strokeWidth="1.5"
          filter="url(#radarGlow)"
          style={{ transition: 'all 0.6s ease-out' }}
        />

        {/* Data points */}
        {dataPoints.map(([px, py], i) => (
          <circle
            key={i}
            cx={px} cy={py}
            r={compact ? 2.5 : 3.5}
            fill={AXES[i].color}
            stroke={theme.colors.background.surface}
            strokeWidth="1.5"
            style={{ transition: 'all 0.6s ease-out' }}
          />
        ))}

        {/* Axis labels (expanded only) */}
        {!compact && AXES.map(axis => {
          const [lx, ly] = polarToXY(axis.angle, maxR + 16, cx, cy)
          return (
            <text
              key={axis.key}
              x={lx} y={ly}
              textAnchor="middle"
              dominantBaseline="middle"
              fill={axis.color}
              fontSize="8"
              fontFamily="var(--font-display)"
              fontWeight="700"
              letterSpacing="0.08em"
            >
              {axis.shortLabel}
            </text>
          )
        })}
      </svg>

      {/* Labels below (expanded only) */}
      {!compact && (
        <div className="flex justify-center gap-3 mt-1">
          {AXES.map(axis => (
            <div key={axis.key} className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: axis.color }} />
              <span
                className="font-display text-[8px] font-bold tracking-widest uppercase"
                style={{ color: theme.colors.text.muted }}
              >
                {axis.label}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
