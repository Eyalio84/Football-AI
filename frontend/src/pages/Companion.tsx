import { useState, useEffect, useRef, useCallback } from 'react'
import { theme } from '@/config/theme'
import { useClubTheme } from '@/config/ClubThemeProvider'
import { CLUB_PALETTES, type ClubPalette } from '@/config/clubThemes'
import { Radio } from 'lucide-react'
import { API_URL } from '@/config/api'

interface MatchEvent {
  type: string
  event_type: string
  minute: string
  description: string
  reaction: string
  score_home: number
  score_away: number
  home_team: string
  away_team: string
  timestamp: string
}

interface SimMatch {
  key: string
  home_team: string
  away_team: string
  home_id: string
  away_id: string
}

interface SessionState {
  session_id: string
  home_team: string
  away_team: string
  club: string
  score_home: number
  score_away: number
  status: string
  finished: boolean
  events: MatchEvent[]
  total_events: number
}

const EVENT_ICONS: Record<string, string> = {
  kickoff: '\u23F1',
  goal: '\u26BD',
  goal_conceded: '\u26BD',
  halftime: '\u23F8',
  second_half: '\u25B6',
  fulltime: '\u{1F3C1}',
}

function getPalette(clubId: string): ClubPalette {
  return CLUB_PALETTES[clubId] || { primary: '#666', secondary: '#999', accent: '#fff', gradient: '#666', glowColor: 'transparent', textOnPrimary: '#fff' }
}

export function Companion() {
  const [matches, setMatches] = useState<SimMatch[]>([])
  const [selectedMatch, setSelectedMatch] = useState<string>('')
  const [selectedClub, setSelectedClub] = useState<string>('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [state, setState] = useState<SessionState | null>(null)
  const [loading, setLoading] = useState(false)
  const { setClubId } = useClubTheme()
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const eventsEndRef = useRef<HTMLDivElement>(null)

  // Fetch available simulated matches
  useEffect(() => {
    fetch(`${API_URL}/api/v1/live/companion/matches`)
      .then(r => r.json())
      .then(d => setMatches(d.data || []))
      .catch(() => {})
  }, [])

  // Auto-scroll
  useEffect(() => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state?.events?.length])

  // Set club theme
  useEffect(() => {
    setClubId(selectedClub || null)
  }, [selectedClub, setClubId])

  const startSimulation = useCallback(async () => {
    if (!selectedMatch || !selectedClub) return
    setLoading(true)

    try {
      const resp = await fetch(`${API_URL}/api/v1/live/companion/simulate/${selectedMatch}/${selectedClub}`, {
        method: 'POST',
      })
      const json = await resp.json()
      if (json.success) {
        const sid = json.data.session_id
        setSessionId(sid)
        setState({
          session_id: sid,
          home_team: json.data.home_team,
          away_team: json.data.away_team,
          club: selectedClub,
          score_home: 0,
          score_away: 0,
          status: 'TIMED',
          finished: false,
          events: [],
          total_events: 0,
        })

        // Start polling
        let eventsSeen = 0
        pollRef.current = setInterval(async () => {
          try {
            const pollResp = await fetch(`${API_URL}/api/v1/live/companion/events/${sid}?after=${eventsSeen}`)
            const pollJson = await pollResp.json()
            const data = pollJson.data as SessionState

            if (data.events.length > 0) {
              eventsSeen = data.total_events
              setState(prev => prev ? {
                ...prev,
                score_home: data.score_home,
                score_away: data.score_away,
                status: data.status,
                finished: data.finished,
                events: [...prev.events, ...data.events],
                total_events: data.total_events,
              } : null)
            } else if (data.finished) {
              setState(prev => prev ? { ...prev, finished: true } : null)
            }

            if (data.finished && pollRef.current) {
              clearInterval(pollRef.current)
              pollRef.current = null
            }
          } catch {}
        }, 3000)
      }
    } catch (err) {
      console.error('Failed to start simulation:', err)
    } finally {
      setLoading(false)
    }
  }, [selectedMatch, selectedClub])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const reset = () => {
    if (pollRef.current) clearInterval(pollRef.current)
    setSessionId(null)
    setState(null)
    setSelectedMatch('')
    setSelectedClub('')
  }

  const match = matches.find(m => m.key === selectedMatch)
  const homePalette = match ? getPalette(match.home_id) : null
  const awayPalette = match ? getPalette(match.away_id) : null
  const clubPalette = selectedClub ? getPalette(selectedClub) : null

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Radio
          size={20}
          className={state && !state.finished ? 'animate-mood-pulse' : ''}
          style={{ color: state && !state.finished ? '#ef4444' : theme.colors.text.muted }}
        />
        <h1
          className="font-display text-3xl font-extrabold tracking-wide uppercase"
          style={{ color: theme.colors.text.primary }}
        >
          MATCH DAY COMPANION
        </h1>
      </div>

      {/* Setup (before simulation starts) */}
      {!sessionId && (
        <div
          className="rounded-xl border p-6 animate-fade-up"
          style={{
            backgroundColor: theme.colors.background.surface,
            borderColor: theme.colors.border.default,
          }}
        >
          <p className="text-sm italic mb-6" style={{ color: theme.colors.text.secondary }}>
            Watch a simulated match unfold with live fan reactions in your club's voice.
          </p>

          {/* Match picker */}
          <label className="font-display text-xs font-bold tracking-widest uppercase block mb-2" style={{ color: theme.colors.text.secondary }}>
            SELECT MATCH
          </label>
          <div className="grid grid-cols-1 gap-2 mb-6">
            {matches.map(m => {
              const hp = getPalette(m.home_id)
              const ap = getPalette(m.away_id)
              const selected = selectedMatch === m.key
              return (
                <button
                  key={m.key}
                  onClick={() => {
                    setSelectedMatch(m.key)
                    if (!selectedClub) setSelectedClub(m.home_id)
                  }}
                  className="flex items-center justify-between px-4 py-3 rounded-lg border transition-all"
                  style={{
                    backgroundColor: selected ? theme.colors.background.elevated : 'transparent',
                    borderColor: selected ? hp.primary + '60' : theme.colors.border.default,
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: hp.primary }} />
                    <span className="font-display text-sm font-bold" style={{ color: theme.colors.text.primary }}>
                      {m.home_team}
                    </span>
                    <span className="font-display text-xs" style={{ color: theme.colors.text.muted }}>vs</span>
                    <span className="font-display text-sm font-bold" style={{ color: theme.colors.text.primary }}>
                      {m.away_team}
                    </span>
                    <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: ap.primary }} />
                  </div>
                </button>
              )
            })}
          </div>

          {/* Club picker (which side are you supporting?) */}
          {match && (
            <>
              <label className="font-display text-xs font-bold tracking-widest uppercase block mb-2" style={{ color: theme.colors.text.secondary }}>
                YOUR SIDE
              </label>
              <div className="flex gap-3 mb-6">
                {[{ id: match.home_id, name: match.home_team }, { id: match.away_id, name: match.away_team }].map(team => {
                  const p = getPalette(team.id)
                  const sel = selectedClub === team.id
                  return (
                    <button
                      key={team.id}
                      onClick={() => setSelectedClub(team.id)}
                      className="flex-1 py-3 rounded-lg font-display font-bold text-sm tracking-wide uppercase transition-all"
                      style={{
                        backgroundColor: sel ? p.primary : theme.colors.background.elevated,
                        color: sel ? p.textOnPrimary : theme.colors.text.secondary,
                        border: `2px solid ${sel ? p.primary : 'transparent'}`,
                      }}
                    >
                      {team.name}
                    </button>
                  )
                })}
              </div>
            </>
          )}

          <button
            onClick={startSimulation}
            disabled={!selectedMatch || !selectedClub || loading}
            className="w-full py-3 rounded-xl font-display font-bold tracking-wide uppercase text-sm transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-30"
            style={{
              backgroundColor: clubPalette?.primary || theme.colors.primary,
              color: clubPalette?.textOnPrimary || '#fff',
            }}
          >
            {loading ? 'STARTING...' : 'KICK OFF'}
          </button>
        </div>
      )}

      {/* Live match view */}
      {state && (
        <div className="space-y-4">
          {/* Scoreboard */}
          <div
            className="rounded-xl p-6 text-center border relative overflow-hidden"
            style={{
              backgroundColor: theme.colors.background.surface,
              borderColor: theme.colors.border.default,
            }}
          >
            {/* Background gradient of both teams */}
            {homePalette && awayPalette && (
              <div
                className="absolute inset-0 opacity-10"
                style={{
                  background: `linear-gradient(135deg, ${homePalette.primary} 0%, transparent 50%, ${awayPalette.primary} 100%)`,
                }}
              />
            )}

            <div className="relative z-10">
              {/* Live indicator */}
              {!state.finished && (
                <div className="flex items-center justify-center gap-2 mb-3">
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-mood-pulse" />
                  <span className="font-display text-xs font-bold tracking-widest uppercase text-red-400">
                    LIVE
                  </span>
                </div>
              )}

              <div className="flex items-center justify-center gap-6">
                <div className="text-right flex-1">
                  <span
                    className="font-display text-lg sm:text-xl font-bold tracking-wide uppercase"
                    style={{ color: homePalette?.primary || theme.colors.text.primary }}
                  >
                    {state.home_team}
                  </span>
                </div>

                <div
                  className="font-mono text-4xl sm:text-5xl font-bold px-4"
                  style={{ color: theme.colors.text.primary }}
                >
                  {state.score_home} - {state.score_away}
                </div>

                <div className="text-left flex-1">
                  <span
                    className="font-display text-lg sm:text-xl font-bold tracking-wide uppercase"
                    style={{ color: awayPalette?.primary || theme.colors.text.primary }}
                  >
                    {state.away_team}
                  </span>
                </div>
              </div>

              {state.finished && (
                <div className="mt-3 font-display text-sm font-bold tracking-widest uppercase" style={{ color: theme.colors.text.muted }}>
                  FULL TIME
                </div>
              )}
            </div>
          </div>

          {/* Events feed */}
          <div className="space-y-3">
            {state.events.map((ev, idx) => {
              const isGoalForUs = ev.event_type === 'goal'
              const isGoalAgainst = ev.event_type === 'goal_conceded'

              return (
                <div
                  key={idx}
                  className="rounded-xl p-4 border animate-message-in"
                  style={{
                    backgroundColor: theme.colors.background.surface,
                    borderColor: isGoalForUs
                      ? (clubPalette?.primary || '#22c55e') + '40'
                      : isGoalAgainst
                        ? '#ef444440'
                        : theme.colors.border.default,
                    borderLeftWidth: '4px',
                    borderLeftColor: isGoalForUs
                      ? (clubPalette?.primary || '#22c55e')
                      : isGoalAgainst
                        ? '#ef4444'
                        : ev.event_type === 'fulltime'
                          ? '#eab308'
                          : theme.colors.border.default,
                  }}
                >
                  {/* Event header */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">{EVENT_ICONS[ev.event_type] || '\u26A1'}</span>
                    <span className="font-mono text-xs font-bold" style={{ color: theme.colors.text.muted }}>
                      {ev.minute}
                    </span>
                    <span className="font-display text-xs font-bold tracking-wide uppercase" style={{ color: theme.colors.text.secondary }}>
                      {ev.description}
                    </span>
                  </div>

                  {/* Fan reaction */}
                  <p
                    className="text-sm leading-relaxed italic"
                    style={{ color: theme.colors.text.primary }}
                  >
                    "{ev.reaction}"
                  </p>
                </div>
              )
            })}

            {/* Waiting indicator */}
            {!state.finished && state.events.length > 0 && (
              <div className="flex items-center justify-center gap-2 py-4">
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="font-display text-xs tracking-wide uppercase ml-2" style={{ color: theme.colors.text.muted }}>
                  Watching...
                </span>
              </div>
            )}

            <div ref={eventsEndRef} />
          </div>

          {/* Reset button */}
          {state.finished && (
            <div className="text-center pt-4 animate-fade-up">
              <button
                onClick={reset}
                className="px-6 py-2 rounded-xl font-display font-bold tracking-wide uppercase text-xs transition-all hover:scale-105 border"
                style={{
                  borderColor: theme.colors.border.strong,
                  color: theme.colors.text.secondary,
                }}
              >
                WATCH ANOTHER MATCH
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
