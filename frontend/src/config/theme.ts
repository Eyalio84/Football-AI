/**
 * Theme Configuration
 *
 * This is the SINGLE SOURCE OF TRUTH for all visual styling.
 * Change colors, fonts, spacing here to customize the entire app.
 */

export const theme = {
  // Color Palette - Change these to match your brand
  colors: {
    // Primary green accent (used for user messages, highlights)
    primary: '#10B981',
    primaryHover: '#059669',

    // Secondary blue accent
    secondary: '#3B82F6',
    secondaryHover: '#2563EB',

    // Dark theme backgrounds
    background: {
      default: '#0F172A',   // Page background (alias for main)
      main: '#0F172A',      // Darkest - page background
      surface: '#1E293B',   // Cards, chat bubbles
      elevated: '#334155',  // Hover states, elevated elements
    },

    // Border colors
    border: {
      default: '#334155',   // Default borders
      subtle: '#1E293B',    // Subtle borders
      strong: '#475569',    // Strong borders
    },

    // Text colors
    text: {
      primary: '#F8FAFC',   // Main text
      secondary: '#94A3B8', // Muted text, timestamps
      tertiary: '#64748B',  // Even more muted
      muted: '#64748B',     // Placeholders, disabled
    },

    // Message bubble specific
    bubbles: {
      user: '#10B981',      // User message background
      userText: '#FFFFFF',  // User message text
      bot: '#1E293B',       // Bot message background
      botText: '#F8FAFC',   // Bot message text
    },

    // Semantic colors
    success: '#22C55E',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
  },

  // Typography — Matchday Programme
  fonts: {
    display: "var(--font-display)",  // Barlow Condensed — headlines, nav
    body: "var(--font-body)",        // Source Serif 4 — chat, paragraphs
    mono: "var(--font-mono)",        // JetBrains Mono — stats, tables
    // Legacy alias
    sans: "var(--font-body)",
  },

  // Font sizes
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
  },

  // Spacing
  spacing: {
    xs: '0.5rem',  // 8px
    sm: '0.75rem', // 12px
    md: '1rem',    // 16px
    lg: '1.5rem',  // 24px
    xl: '2rem',    // 32px
  },

  // Border radius
  borderRadius: {
    sm: '0.375rem',  // 6px
    md: '0.5rem',    // 8px
    lg: '0.75rem',   // 12px
    xl: '1rem',      // 16px
    full: '9999px',  // Fully rounded
  },

  // Shadows
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1)',
  },

  // Transitions
  transitions: {
    fast: '150ms ease-in-out',
    normal: '250ms ease-in-out',
    slow: '350ms ease-in-out',
  },

  // Layout
  layout: {
    maxChatWidth: '48rem', // Max width of chat container
    headerHeight: '4rem',  // Height of top bar
    inputHeight: '4.5rem', // Height of input area
  },
} as const

// Export type for TypeScript autocomplete
export type Theme = typeof theme
