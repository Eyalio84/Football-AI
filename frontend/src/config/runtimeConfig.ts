/**
 * Runtime Configuration
 *
 * Allows certain settings to be changed at runtime (no rebuild needed).
 * Values are persisted to localStorage so they survive page refresh.
 *
 * Priority: localStorage override > VITE env var > hardcoded default
 */

const KEYS = {
  API_URL: 'soccer_ai_api_url',
  DEBUG_4D: 'soccer_ai_debug_4d',
} as const

const DEFAULT_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function readLocal(key: string): string | null {
  try { return localStorage.getItem(key) } catch { return null }
}

function writeLocal(key: string, value: string | null) {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch { /* ignore */ }
}

/** Mutable singleton — updated by ConfigDrawer, read by api.ts */
export const runtimeConfig = {
  get apiUrl(): string {
    return readLocal(KEYS.API_URL) || DEFAULT_API_URL
  },
  setApiUrl(url: string | null) {
    writeLocal(KEYS.API_URL, url)
  },

  get debug4d(): boolean {
    return readLocal(KEYS.DEBUG_4D) === 'true'
  },
  setDebug4d(on: boolean) {
    writeLocal(KEYS.DEBUG_4D, on ? 'true' : null)
  },

  /** Hard reset: wipe all soccer_ai_* keys and reload */
  hardReset() {
    try {
      Object.values(KEYS).forEach(k => localStorage.removeItem(k))
      localStorage.removeItem('soccer_ai_league')
      // Clear any other app keys
      const toRemove: string[] = []
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i)
        if (k?.startsWith('soccer_ai_')) toRemove.push(k)
      }
      toRemove.forEach(k => localStorage.removeItem(k))
    } catch { /* ignore */ }
    window.location.href = '/'
  },

  /** Soft reset: clear conversation state only (no reload) */
  clearConversation(): void {
    // Conversation IDs are in-memory — a page reload clears them
    // We just navigate to home which resets the chat component tree
    window.location.href = '/chat'
  },
}
