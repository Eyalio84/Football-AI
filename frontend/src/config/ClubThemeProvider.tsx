/**
 * ClubThemeProvider
 *
 * React context that applies club-specific CSS custom properties to <body>.
 * When the selected club changes, the entire UI shifts colour world.
 */

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { getClubPalette, type ClubPalette } from './clubThemes'

import { API_URL } from './api'

export type MoodState = 'euphoric' | 'confident' | 'steady' | 'anxious' | 'despairing' | 'neutral'

interface ClubThemeContextValue {
  clubId: string | null
  palette: ClubPalette
  mood: MoodState
  setClubId: (id: string | null) => void
}

const ClubThemeContext = createContext<ClubThemeContextValue | null>(null)

export function ClubThemeProvider({ children }: { children: ReactNode }) {
  const [clubId, setClubId] = useState<string | null>(null)
  const [mood, setMood] = useState<MoodState>('neutral')
  const palette = getClubPalette(clubId)

  // Apply CSS custom properties + mood class whenever club changes
  useEffect(() => {
    const root = document.documentElement

    root.style.setProperty('--club-primary', palette.primary)
    root.style.setProperty('--club-secondary', palette.secondary)
    root.style.setProperty('--club-accent', palette.accent)
    root.style.setProperty('--club-gradient', palette.gradient)
    root.style.setProperty('--club-glow', palette.glowColor)
    root.style.setProperty('--club-text-on-primary', palette.textOnPrimary)
    root.style.setProperty('--club-primary-rgb', hexToRgb(palette.primary))
    root.style.setProperty('--club-secondary-rgb', hexToRgb(palette.secondary))
  }, [palette])

  // Fetch mood when club changes
  useEffect(() => {
    if (!clubId || clubId === 'analyst') {
      setMood('neutral')
      return
    }
    fetch(`${API_URL}/api/v1/fan/${clubId}/mood`)
      .then(r => r.json())
      .then(d => {
        const m = d?.mood?.current_mood?.toLowerCase() || 'neutral'
        setMood(m as MoodState)
      })
      .catch(() => setMood('neutral'))
  }, [clubId])

  // Apply mood class to <body> for kinetic theming
  useEffect(() => {
    const body = document.body
    // Remove all mood classes
    body.classList.remove('mood-euphoric', 'mood-confident', 'mood-steady', 'mood-anxious', 'mood-despairing', 'mood-neutral')
    body.classList.add(`mood-${mood}`)
  }, [mood])

  return (
    <ClubThemeContext.Provider value={{ clubId, palette, mood, setClubId }}>
      {children}
    </ClubThemeContext.Provider>
  )
}

export function useClubTheme() {
  const ctx = useContext(ClubThemeContext)
  if (!ctx) throw new Error('useClubTheme must be used within ClubThemeProvider')
  return ctx
}

/** Convert hex (#RRGGBB) to "R, G, B" for rgba() usage */
function hexToRgb(hex: string): string {
  const h = hex.replace('#', '')
  const r = parseInt(h.substring(0, 2), 16)
  const g = parseInt(h.substring(2, 4), 16)
  const b = parseInt(h.substring(4, 6), 16)
  return `${r}, ${g}, ${b}`
}
