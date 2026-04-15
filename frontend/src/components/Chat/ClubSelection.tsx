import { useState, useEffect } from 'react'
import { theme } from '@/config/theme'
import { API_URL } from '@/config/api'
import { getClubs } from '@/services/api'
import { CLUB_PALETTES, ANALYST_PALETTE, DEFAULT_PALETTE, type ClubPalette } from '@/config/clubThemes'
import { BarChart3 } from 'lucide-react'
import { useLeague } from '@/config/LeagueProvider'

interface Club {
  id: string
  name: string
}

interface MoodData {
  current_mood: string
  mood_reason: string
  form: string
}

interface ClubSelectionProps {
  onSelectClub: (clubId: string) => void
}

const CLUB_STADIUMS: Record<string, string> = {
  // Premier League
  arsenal: 'Emirates Stadium',
  chelsea: 'Stamford Bridge',
  liverpool: 'Anfield',
  manchester_united: 'Old Trafford',
  manchester_city: 'Etihad Stadium',
  tottenham: 'Tottenham Hotspur Stadium',
  newcastle: "St James' Park",
  west_ham: 'London Stadium',
  everton: 'Goodison Park',
  aston_villa: 'Villa Park',
  brighton: 'Amex Stadium',
  wolves: 'Molineux',
  crystal_palace: 'Selhurst Park',
  fulham: 'Craven Cottage',
  nottingham_forest: 'City Ground',
  brentford: 'Gtech Community Stadium',
  bournemouth: 'Vitality Stadium',
  sunderland: 'Stadium of Light',
  leeds: 'Elland Road',
  burnley: 'Turf Moor',
  ipswich: 'Portman Road',
  southampton: "St Mary's Stadium",
  leicester: 'King Power Stadium',
  // La Liga
  real_madrid: 'Santiago Bernabéu',
  barcelona: 'Spotify Camp Nou',
  atletico_madrid: 'Cívitas Metropolitano',
  sevilla: 'Ramón Sánchez-Pizjuán',
  athletic_bilbao: 'San Mamés',
  valencia: 'Mestalla',
  real_betis: 'Benito Villamarín',
  real_sociedad: 'Reale Arena',
  villarreal: 'Estadio de la Cerámica',
  osasuna: 'El Sadar',
  celta_vigo: 'Estadio de Balaídos',
  getafe: 'Coliseum Alfonso Pérez',
  cadiz: 'Estadio Nuevo Mirandilla',
  almeria: 'Power Horse Stadium',
  rayo_vallecano: 'Campo de Fútbol de Vallecas',
  mallorca: 'Visit Mallorca Estadi',
  granada: 'Estadio Nuevo Los Cármenes',
  girona: 'Estadio Municipal de Montilivi',
  las_palmas: 'Estadio Gran Canaria',
  leganes: 'Estadio Municipal de Butarque',
}

const MOOD_EMOJI: Record<string, string> = {
  euphoric: '\u2191\u2191',
  confident: '\u2191',
  steady: '\u2192',
  anxious: '\u2193',
  despairing: '\u2193\u2193',
  frustrated: '\u2193',
  neutral: '\u2192',
}

/** League tab bar — prominent selector above the club grid */
function LeagueTabBar() {
  const { competition, setCompetition, leagues } = useLeague()

  // Always show at least a PL placeholder while leagues are loading
  const tabs = leagues.length > 0 ? leagues : [
    { competition_code: 'PL', display_name: 'Premier League', country: 'England' }
  ]

  return (
    <div className="flex gap-2 mb-8 animate-fade-up" style={{ animationDelay: '150ms' }}>
      {tabs.map(league => {
        const active = league.competition_code === competition
        return (
          <button
            key={league.competition_code}
            onClick={() => setCompetition(league.competition_code)}
            className="px-5 py-2 rounded-full border transition-all duration-200 font-display text-xs font-bold tracking-widest uppercase"
            style={{
              backgroundColor: active ? theme.colors.text.primary : 'transparent',
              borderColor: active ? theme.colors.text.primary : theme.colors.border.default,
              color: active ? theme.colors.background.default : theme.colors.text.secondary,
              transform: active ? 'scale(1.05)' : 'scale(1)',
            }}
          >
            {league.display_name}
          </button>
        )
      })}
    </div>
  )
}

/** Featured clubs per league shown slightly larger */
const FEATURED_CLUBS: Record<string, Set<string>> = {
  PL: new Set(['arsenal', 'chelsea', 'liverpool', 'manchester_united', 'manchester_city', 'tottenham']),
  PD: new Set(['real_madrid', 'barcelona', 'atletico_madrid']),
}

export function ClubSelection({ onSelectClub }: ClubSelectionProps) {
  const { competition, clubsForLeague } = useLeague()
  const [clubs, setClubs] = useState<Club[]>([])
  const [moods, setMoods] = useState<Record<string, MoodData>>({})
  const [hoveredClub, setHoveredClub] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Re-fetch whenever the league changes
  useEffect(() => {
    setLoading(true)
    setMoods({})

    const fetchData = async () => {
      try {
        let data: Club[]
        if (clubsForLeague.length > 0) {
          // Use clubs from the league context (loaded via /api/v1/leagues)
          data = clubsForLeague.map(c => ({ id: c.id, name: c.display_name }))
        } else {
          // Fallback: fetch PL clubs from legacy endpoint
          data = await getClubs()
        }
        setClubs(data)

        // Fetch moods in parallel for all clubs
        const moodPromises = data.map(async (club: Club) => {
          try {
            const resp = await fetch(`${API_URL}/api/v1/fan/${club.id}/mood`)
            const json = await resp.json()
            return { id: club.id, mood: json.mood as MoodData }
          } catch {
            return { id: club.id, mood: null }
          }
        })

        const results = await Promise.all(moodPromises)
        const moodMap: Record<string, MoodData> = {}
        for (const r of results) {
          if (r.mood) moodMap[r.id] = r.mood
        }
        setMoods(moodMap)
      } catch (error) {
        console.error('Failed to fetch clubs:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [competition, clubsForLeague])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div
            className="w-10 h-10 border-2 border-t-transparent rounded-full animate-spin mx-auto mb-4"
            style={{ borderColor: theme.colors.text.muted, borderTopColor: 'transparent' }}
          />
          <p className="font-display text-sm tracking-wide uppercase" style={{ color: theme.colors.text.secondary }}>
            Loading clubs...
          </p>
        </div>
      </div>
    )
  }

  const featuredSet = FEATURED_CLUBS[competition] ?? FEATURED_CLUBS['PL']

  // Sort: featured clubs first, then alphabetical
  const sorted = [...clubs].sort((a, b) => {
    const aIsBig = featuredSet.has(a.id) ? 0 : 1
    const bIsBig = featuredSet.has(b.id) ? 0 : 1
    if (aIsBig !== bIsBig) return aIsBig - bIsBig
    return a.name.localeCompare(b.name)
  })

  return (
    <div
      className="min-h-screen flex flex-col items-center p-6 pt-12"
      style={{ backgroundColor: theme.colors.background.default }}
    >
      {/* Header */}
      <div className="max-w-4xl w-full text-center mb-6">
        <h1
          className="font-display text-5xl sm:text-6xl font-extrabold tracking-tight uppercase mb-3 animate-fade-up"
          style={{ color: theme.colors.text.primary }}
        >
          PICK YOUR SIDE
        </h1>
        <p
          className="text-lg italic animate-fade-up"
          style={{ color: theme.colors.text.secondary, animationDelay: '100ms' }}
        >
          "The young lad on the tip of his toes, holding his breath..."
        </p>
      </div>

      {/* League Selector */}
      <LeagueTabBar />



      {/* Club Grid */}
      <div className="w-full max-w-6xl">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {sorted.map((club, index) => {
            const palette: ClubPalette = CLUB_PALETTES[club.id] || DEFAULT_PALETTE
            const mood = moods[club.id]
            const isHovered = hoveredClub === club.id
            const isBig6 = featuredSet.has(club.id)
            const stadium = CLUB_STADIUMS[club.id]

            return (
              <button
                key={club.id}
                onClick={() => onSelectClub(club.id)}
                onMouseEnter={() => setHoveredClub(club.id)}
                onMouseLeave={() => setHoveredClub(null)}
                className={`relative cursor-pointer transition-all duration-300 animate-fade-up ${
                  isBig6 ? 'sm:col-span-1' : ''
                }`}
                style={{ animationDelay: `${index * 40}ms` }}
              >
                <div
                  className="rounded-xl p-5 h-full flex flex-col justify-between border transition-all duration-300 overflow-hidden"
                  style={{
                    background: isHovered
                      ? palette.gradient
                      : theme.colors.background.elevated,
                    borderColor: isHovered
                      ? palette.primary
                      : palette.primary + '20',
                    boxShadow: isHovered
                      ? `0 12px 32px ${palette.primary}35, inset 0 1px 0 ${palette.primary}20`
                      : 'none',
                    transform: isHovered ? 'translateY(-2px)' : 'translateY(0)',
                    minHeight: isBig6 ? '140px' : '120px',
                  }}
                >
                  {/* Top row: colour bar + name */}
                  <div>
                    <div className="flex items-center gap-2.5 mb-2">
                      <div
                        className="w-3 h-3 rounded-sm flex-shrink-0"
                        style={{ backgroundColor: palette.primary }}
                      />
                      <h3
                        className="font-display text-base font-bold tracking-wide uppercase truncate transition-colors duration-300"
                        style={{
                          color: isHovered ? palette.textOnPrimary : theme.colors.text.primary,
                        }}
                      >
                        {club.name}
                      </h3>
                    </div>

                    {/* Stadium */}
                    {stadium && (
                      <p
                        className="text-xs mb-2 truncate transition-colors duration-300"
                        style={{
                          color: isHovered ? palette.textOnPrimary + 'AA' : theme.colors.text.muted,
                        }}
                      >
                        {stadium}
                      </p>
                    )}
                  </div>

                  {/* Mood badge */}
                  {mood && (
                    <div
                      className="flex items-center gap-1.5 mt-auto"
                    >
                      <span
                        className="font-mono text-xs font-semibold uppercase transition-colors duration-300"
                        style={{
                          color: isHovered ? palette.textOnPrimary + 'CC' : getMoodColor(mood.current_mood),
                        }}
                      >
                        {MOOD_EMOJI[mood.current_mood] || ''} {mood.current_mood}
                      </span>
                      {mood.form && (
                        <div className="flex gap-0.5 ml-auto">
                          {mood.form.split('').slice(0, 5).map((r, i) => (
                            <div
                              key={i}
                              className="w-2 h-2 rounded-full"
                              style={{
                                backgroundColor: r === 'W' ? '#22c55e'
                                  : r === 'D' ? '#eab308'
                                  : r === 'L' ? '#ef4444'
                                  : '#6b7280',
                                opacity: isHovered ? 0.9 : 0.7,
                              }}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </button>
            )
          })}
        </div>

        {/* Neutral Analyst Option */}
        <div className="mt-6 flex justify-center">
          <button
            onClick={() => onSelectClub('analyst')}
            onMouseEnter={() => setHoveredClub('analyst')}
            onMouseLeave={() => setHoveredClub(null)}
            className="transition-all duration-300 animate-fade-up"
            style={{ animationDelay: `${sorted.length * 40 + 100}ms` }}
          >
            <div
              className="rounded-xl px-8 py-4 flex items-center gap-3 border transition-all duration-300"
              style={{
                background: hoveredClub === 'analyst'
                  ? ANALYST_PALETTE.gradient
                  : theme.colors.background.surface,
                borderColor: hoveredClub === 'analyst'
                  ? theme.colors.text.secondary
                  : theme.colors.border.default,
                transform: hoveredClub === 'analyst' ? 'translateY(-2px)' : 'translateY(0)',
              }}
            >
              <BarChart3
                size={20}
                style={{ color: hoveredClub === 'analyst' ? '#fff' : theme.colors.text.secondary }}
              />
              <div className="text-left">
                <span
                  className="font-display text-sm font-bold tracking-wide uppercase block transition-colors duration-300"
                  style={{
                    color: hoveredClub === 'analyst' ? '#fff' : theme.colors.text.primary,
                  }}
                >
                  NEUTRAL ANALYST
                </span>
                <span
                  className="text-xs transition-colors duration-300"
                  style={{
                    color: hoveredClub === 'analyst' ? '#ffffffAA' : theme.colors.text.muted,
                  }}
                >
                  No allegiances. Pure data.
                </span>
              </div>
            </div>
          </button>
        </div>

        {/* Footer */}
        <div
          className="mt-8 text-center text-xs font-display tracking-widest uppercase"
          style={{ color: theme.colors.text.muted }}
        >
          Fan at heart. Analyst in nature.
        </div>
      </div>
    </div>
  )
}

function getMoodColor(mood: string): string {
  const m = mood.toLowerCase()
  if (m === 'euphoric' || m === 'confident') return '#22c55e'
  if (m === 'steady' || m === 'neutral') return '#94a3b8'
  if (m === 'anxious' || m === 'frustrated') return '#f59e0b'
  if (m === 'despairing') return '#ef4444'
  return '#6b7280'
}
