/**
 * LiveMatchBanner
 *
 * Checks for live matches involving the selected club.
 * If found, shows a persistent banner with score + link to Companion.
 * Polls every 60 seconds.
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useClubTheme } from '@/config/ClubThemeProvider'
import { API_URL } from '@/config/api'
import { Radio } from 'lucide-react'

interface LiveFixture {
  id: number
  home_team: string
  away_team: string
  status: string
  home_score?: number
  away_score?: number
  minute?: number
}

export function LiveMatchBanner() {
  const { clubId, palette } = useClubTheme()
  const [liveMatch, setLiveMatch] = useState<LiveFixture | null>(null)

  useEffect(() => {
    if (!clubId || clubId === 'analyst') {
      setLiveMatch(null)
      return
    }

    const checkLive = async () => {
      try {
        const resp = await fetch(`${API_URL}/api/v1/live/fixtures`)
        const json = await resp.json()
        const fixtures = json.data || []

        // Find a match that's IN_PLAY involving our club
        const clubLower = clubId.replace(/_/g, ' ').toLowerCase()
        const live = fixtures.find((f: LiveFixture) => {
          const isLive = f.status === 'IN_PLAY' || f.status === 'LIVE' || f.status === 'PAUSED'
          const involves = f.home_team?.toLowerCase().includes(clubLower) ||
                          f.away_team?.toLowerCase().includes(clubLower)
          return isLive && involves
        })

        setLiveMatch(live || null)
      } catch {
        setLiveMatch(null)
      }
    }

    checkLive()
    const interval = setInterval(checkLive, 60000)
    return () => clearInterval(interval)
  }, [clubId])

  if (!liveMatch) return null

  return (
    <Link
      to="/companion"
      className="block w-full py-2 px-4 text-center transition-all hover:brightness-110 animate-mood-pulse"
      style={{
        backgroundColor: palette.primary,
        color: palette.textOnPrimary,
      }}
    >
      <div className="flex items-center justify-center gap-3 text-sm font-display font-bold tracking-wide uppercase">
        <Radio size={14} className="animate-pulse" />
        <span>
          LIVE: {liveMatch.home_team} {liveMatch.home_score ?? '?'}-{liveMatch.away_score ?? '?'} {liveMatch.away_team}
          {liveMatch.minute ? ` (${liveMatch.minute}')` : ''}
        </span>
        <span className="font-normal opacity-80">TAP TO WATCH</span>
      </div>
    </Link>
  )
}
