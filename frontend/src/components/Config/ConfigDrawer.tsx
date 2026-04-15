/**
 * ConfigDrawer
 *
 * A persistent left-edge settings drawer available on every page.
 * When closed, only a small handle tab is visible.
 * Tap the handle (or anywhere on it) to open.
 *
 * Contents:
 * - API health indicator
 * - Hard reset
 * - Clear conversation
 * - League switcher
 * - Backend URL override
 * - Session info (active club, mood, league)
 * - Debug 4D toggle
 */

import { useState, useEffect, useRef } from 'react'
import { runtimeConfig } from '@/config/runtimeConfig'
import { useLeague } from '@/config/LeagueProvider'
import { useClubTheme } from '@/config/ClubThemeProvider'
import { theme } from '@/config/theme'

// ─── API Health ───────────────────────────────────────────────────────────────

type HealthStatus = 'checking' | 'ok' | 'error'

function useApiHealth(apiUrl: string): HealthStatus {
  const [status, setStatus] = useState<HealthStatus>('checking')

  useEffect(() => {
    setStatus('checking')
    fetch(`${apiUrl}/api/v1/leagues`, { signal: AbortSignal.timeout(4000) })
      .then(r => setStatus(r.ok ? 'ok' : 'error'))
      .catch(() => setStatus('error'))
  }, [apiUrl])

  return status
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function HealthDot({ status }: { status: HealthStatus }) {
  const color = status === 'ok' ? '#22c55e' : status === 'error' ? '#ef4444' : '#f59e0b'
  const label = status === 'ok' ? 'Backend online' : status === 'error' ? 'Backend unreachable' : 'Checking…'
  return (
    <div className="flex items-center gap-2">
      <div
        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
        style={{
          backgroundColor: color,
          boxShadow: status === 'ok' ? `0 0 6px ${color}` : 'none',
        }}
      />
      <span className="text-xs" style={{ color: theme.colors.text.secondary }}>{label}</span>
    </div>
  )
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-display font-bold tracking-widest uppercase mb-2"
      style={{ color: theme.colors.text.muted }}>
      {children}
    </p>
  )
}

function Divider() {
  return <div className="my-4 h-px" style={{ backgroundColor: theme.colors.border.subtle }} />
}

// ─── Main Drawer ──────────────────────────────────────────────────────────────

export function ConfigDrawer() {
  const [open, setOpen] = useState(false)
  const [apiUrl, setApiUrl] = useState(runtimeConfig.apiUrl)
  const [apiUrlDraft, setApiUrlDraft] = useState(runtimeConfig.apiUrl)
  const [debug4d, setDebug4d] = useState(runtimeConfig.debug4d)
  const [resetConfirm, setResetConfirm] = useState(false)
  const resetTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const { competition, setCompetition, leagues } = useLeague()
  const { clubId, mood } = useClubTheme()
  const health = useApiHealth(apiUrl)

  // Cancel reset confirmation after 4 seconds
  useEffect(() => {
    if (resetConfirm) {
      resetTimer.current = setTimeout(() => setResetConfirm(false), 4000)
    }
    return () => { if (resetTimer.current) clearTimeout(resetTimer.current) }
  }, [resetConfirm])

  // Close drawer on outside click
  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (!target.closest('[data-config-drawer]')) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  function applyApiUrl() {
    const trimmed = apiUrlDraft.trim().replace(/\/$/, '')
    runtimeConfig.setApiUrl(trimmed === (import.meta.env.VITE_API_URL || 'http://localhost:8000') ? null : trimmed)
    setApiUrl(trimmed)
  }

  function toggleDebug4d() {
    const next = !debug4d
    runtimeConfig.setDebug4d(next)
    setDebug4d(next)
  }

  const drawerWidth = 300

  return (
    <>
      {/* ── Overlay (mobile tap-outside) ── */}
      {open && (
        <div
          className="fixed inset-0 z-40 sm:hidden"
          style={{ backgroundColor: 'rgba(0,0,0,0.4)' }}
          onClick={() => setOpen(false)}
        />
      )}

      {/* ── Drawer + Handle ── */}
      <div
        data-config-drawer
        className="fixed top-0 left-0 h-full z-50 flex"
        style={{
          transform: open ? 'translateX(0)' : `translateX(-${drawerWidth}px)`,
          transition: 'transform 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      >
        {/* Panel */}
        <div
          className="flex flex-col h-full overflow-y-auto"
          style={{
            width: drawerWidth,
            backgroundColor: theme.colors.background.elevated,
            borderRight: `1px solid ${theme.colors.border.subtle}`,
          }}
        >
          {/* Header */}
          <div
            className="flex items-center justify-between px-5 py-4 border-b flex-shrink-0"
            style={{ borderColor: theme.colors.border.subtle }}
          >
            <span className="font-display text-sm font-bold tracking-widest uppercase"
              style={{ color: theme.colors.text.primary }}>
              Settings
            </span>
            <button
              onClick={() => setOpen(false)}
              className="text-lg leading-none"
              style={{ color: theme.colors.text.muted }}
              aria-label="Close settings"
            >
              ×
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 px-5 py-5 space-y-0 overflow-y-auto">

            {/* ── Status ── */}
            <SectionLabel>Status</SectionLabel>
            <HealthDot status={health} />
            {clubId && (
              <div className="mt-2 text-xs" style={{ color: theme.colors.text.secondary }}>
                Club: <span style={{ color: theme.colors.text.primary }}>{clubId}</span>
                &nbsp;·&nbsp;Mood: <span style={{ color: theme.colors.text.primary }}>{mood}</span>
              </div>
            )}
            {competition && (
              <div className="mt-1 text-xs" style={{ color: theme.colors.text.secondary }}>
                League: <span style={{ color: theme.colors.text.primary }}>
                  {leagues.find(l => l.competition_code === competition)?.display_name ?? competition}
                </span>
              </div>
            )}

            <Divider />

            {/* ── League ── */}
            <SectionLabel>League</SectionLabel>
            <div className="flex gap-2 flex-wrap">
              {(leagues.length > 0 ? leagues : [{ competition_code: 'PL', display_name: 'Premier League' }]).map(league => {
                const active = league.competition_code === competition
                return (
                  <button
                    key={league.competition_code}
                    onClick={() => setCompetition(league.competition_code)}
                    className="px-3 py-1.5 rounded-lg border text-xs font-display font-bold tracking-wide uppercase transition-all"
                    style={{
                      backgroundColor: active ? theme.colors.text.primary : 'transparent',
                      borderColor: active ? theme.colors.text.primary : theme.colors.border.default,
                      color: active ? theme.colors.background.default : theme.colors.text.secondary,
                    }}
                  >
                    {league.display_name}
                  </button>
                )
              })}
            </div>

            <Divider />

            {/* ── Reset ── */}
            <SectionLabel>Reset</SectionLabel>
            <div className="space-y-2">
              {/* Hard Reset */}
              {!resetConfirm ? (
                <button
                  onClick={() => setResetConfirm(true)}
                  className="w-full py-2.5 px-4 rounded-lg border text-xs font-display font-bold tracking-wide uppercase transition-all"
                  style={{
                    borderColor: '#ef4444',
                    color: '#ef4444',
                    backgroundColor: 'transparent',
                  }}
                >
                  Hard Reset
                </button>
              ) : (
                <button
                  onClick={() => runtimeConfig.hardReset()}
                  className="w-full py-2.5 px-4 rounded-lg text-xs font-display font-bold tracking-wide uppercase animate-pulse"
                  style={{
                    backgroundColor: '#ef4444',
                    color: '#ffffff',
                  }}
                >
                  Tap again to confirm
                </button>
              )}

              {/* Clear Conversation */}
              <button
                onClick={() => { runtimeConfig.clearConversation(); setOpen(false) }}
                className="w-full py-2 px-4 rounded-lg border text-xs font-display font-bold tracking-wide uppercase transition-all"
                style={{
                  borderColor: theme.colors.border.default,
                  color: theme.colors.text.secondary,
                  backgroundColor: 'transparent',
                }}
              >
                Clear Conversation
              </button>
            </div>

            <Divider />

            {/* ── Backend URL ── */}
            <SectionLabel>Backend URL</SectionLabel>
            <div className="space-y-2">
              <input
                type="text"
                value={apiUrlDraft}
                onChange={e => setApiUrlDraft(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && applyApiUrl()}
                className="w-full px-3 py-2 rounded-lg text-xs font-mono"
                style={{
                  backgroundColor: theme.colors.background.surface,
                  border: `1px solid ${theme.colors.border.default}`,
                  color: theme.colors.text.primary,
                  outline: 'none',
                }}
                placeholder="http://localhost:8000"
                spellCheck={false}
              />
              <button
                onClick={applyApiUrl}
                className="w-full py-2 px-4 rounded-lg text-xs font-display font-bold tracking-wide uppercase transition-all"
                style={{
                  backgroundColor: theme.colors.background.surface,
                  border: `1px solid ${theme.colors.border.default}`,
                  color: theme.colors.text.secondary,
                }}
              >
                Apply URL
              </button>
              <p className="text-[10px]" style={{ color: theme.colors.text.muted }}>
                Switch between local and Hetzner without a rebuild.
              </p>
            </div>

            <Divider />

            {/* ── Debug ── */}
            <SectionLabel>Debug</SectionLabel>
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-xs" style={{ color: theme.colors.text.secondary }}>
                Show 4D persona state
              </span>
              <div
                className="relative w-10 h-5 rounded-full transition-colors duration-200"
                style={{ backgroundColor: debug4d ? '#22c55e' : theme.colors.border.default }}
                onClick={toggleDebug4d}
              >
                <div
                  className="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform duration-200"
                  style={{ transform: debug4d ? 'translateX(22px)' : 'translateX(2px)' }}
                />
              </div>
            </label>
            {debug4d && (
              <p className="text-[10px] mt-1" style={{ color: theme.colors.text.muted }}>
                4D state will appear in the browser console on each chat message.
              </p>
            )}

          </div>

          {/* Footer */}
          <div
            className="px-5 py-3 border-t flex-shrink-0"
            style={{ borderColor: theme.colors.border.subtle }}
          >
            <p className="text-[10px] font-display tracking-widest uppercase text-center"
              style={{ color: theme.colors.text.muted }}>
              Football AI · Config
            </p>
          </div>
        </div>

        {/* Handle tab — always visible, sticks out to the right of the panel */}
        <button
          onClick={() => setOpen(o => !o)}
          aria-label="Open settings"
          className="flex-shrink-0 flex items-center justify-center"
          style={{
            width: 20,
            alignSelf: 'center',
            height: 64,
            backgroundColor: theme.colors.background.elevated,
            border: `1px solid ${theme.colors.border.subtle}`,
            borderLeft: 'none',
            borderRadius: '0 8px 8px 0',
            cursor: 'pointer',
            // Health status stripe on handle
            borderTop: `3px solid ${
              health === 'ok' ? '#22c55e' : health === 'error' ? '#ef4444' : '#f59e0b'
            }`,
          }}
        >
          {/* Three tiny dots like a drag handle */}
          <div className="flex flex-col gap-1">
            {[0,1,2].map(i => (
              <div key={i} className="w-1 h-1 rounded-full"
                style={{ backgroundColor: theme.colors.text.muted }} />
            ))}
          </div>
        </button>
      </div>
    </>
  )
}
