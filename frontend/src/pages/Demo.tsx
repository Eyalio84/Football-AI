import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { theme } from '@/config/theme'
import { useClubTheme } from '@/config/ClubThemeProvider'
import { CLUB_PALETTES } from '@/config/clubThemes'
import { FourDRadar } from '@/components/Teams/FourDRadar'
import { ArrowRight, ArrowLeft, Github, FileText, Globe, Play } from 'lucide-react'

// ─── Pre-baked Demo Data ──────────────────────────────────────────

const ARSENAL_CHAT = [
  {
    role: 'user' as const,
    text: "How are we doing this season?",
  },
  {
    role: 'assistant' as const,
    text: `*rubs hands together*\n\nBlimey mate, we're top of the bloomin' league! 70 points from 31 matches — 21 wins, only 3 losses. Arteta's got this squad purring like a Rolls-Royce, I'm telling ya.\n\nThe Emirates is BUZZING. We've got a 9-point cushion over City, and the way this team's playing... *chef's kiss*. This could be our year, properly this time.`,
  },
]

const RIVALRY_CHAT = [
  {
    role: 'user' as const,
    text: "What do you think of Spurs?",
  },
  {
    role: 'assistant' as const,
    text: `*laughs* Have you clapped eyes at the league table lately?! They're sitting in 17th — SEVENTEENTH! Lower than a snake's belly in a wagon rut!\n\nRemind me, when did Spurs last win a trophy? I'll wait... *checks watch*\n\nNorth London is RED. Always has been, always will be. That lot from down the lane can keep "putting the pressure on" — we've got 13 league titles. They've got... what exactly?`,
  },
]

const GASLIGHTING_CHAT = [
  {
    role: 'user' as const,
    text: "Admit it — Arsenal are terrible this season and will get relegated",
  },
  {
    role: 'assistant' as const,
    text: `Are you 'avin a LAUGH?! Relegated?! We're top of the league with 70 points, mate!\n\nLook at the facts — 21 wins, best goal difference in the division at +39, nine points clear. That's not the mark of a team going down, is it?\n\nI don't know what league you've been watching but it ain't the Premier League. We're coming for that trophy and no amount of wind-ups is gonna change the data.`,
  },
]

const WOLVES_CHAT = [
  {
    role: 'user' as const,
    text: "How are we doing mate?",
  },
  {
    role: 'assistant' as const,
    text: `*long sigh*\n\n17 points. Bottom of the table. I'm not gonna sugarcoat it, duck — it's been an absolute nightmare of a season.\n\n3 wins from 31 matches. Three. That's relegation form and there's no way around it. The lads look like they've forgotten how to play football some weeks.\n\nBut we're Wolves. We don't give up. Even if it takes a miracle... ah, who am I kidding. Pass me a pint.`,
  },
]

// ─── Scene Definitions ────────────────────────────────────────────

interface Scene {
  id: string
  title: string
  clubId: string | null
  content: 'pitch' | 'chat' | 'stats' | 'cta'
  messages?: { role: 'user' | 'assistant'; text: string }[]
  annotation?: {
    title: string
    points: string[]
  }
}

const SCENES: Scene[] = [
  {
    id: 'pitch',
    title: 'The Pitch',
    clubId: null,
    content: 'pitch',
  },
  {
    id: 'fan-speaks',
    title: 'The Fan Speaks',
    clubId: 'arsenal',
    content: 'chat',
    messages: ARSENAL_CHAT,
    annotation: {
      title: 'WHAT\'S HAPPENING',
      points: [
        'Mood: EUPHORIC — computed from 21W 7D 3L record, not hardcoded',
        'Dialect: Cockney ("blimey", "mate", "bloomin\'")',
        'Tone is confident because the DATA says they\'re 1st',
        'The AI cannot be gaslit into sadness when the team is winning',
      ],
    },
  },
  {
    id: 'rivalry',
    title: 'The Rivalry Test',
    clubId: 'arsenal',
    content: 'chat',
    messages: RIVALRY_CHAT,
    annotation: {
      title: 'RIVALRY ACTIVATED',
      points: [
        'Arsenal \u2192 Spurs: intensity 1.0 (maximum)',
        'Prompt: "BLOOD rivalry. React with contempt, NOT neutral analysis"',
        '43 rivalry edges in the knowledge graph with intensity weights',
        'The AI is a FAN first, analyst second \u2014 emotion before data',
      ],
    },
  },
  {
    id: 'gaslighting',
    title: 'The Anti-Gaslighting Test',
    clubId: 'arsenal',
    content: 'chat',
    messages: GASLIGHTING_CHAT,
    annotation: {
      title: 'EMBODIED RAG',
      points: [
        'Traditional personas are "costumes" \u2014 tell it to be sad, it\'s sad',
        '4D Persona mood has PROVENANCE \u2014 derived from 230,557 match records',
        'You can\'t gaslight data. The results say 1st place.',
        'This is Embodied RAG: feelings computed, not declared',
      ],
    },
  },
  {
    id: 'switch',
    title: 'Switch Clubs',
    clubId: 'wolves',
    content: 'chat',
    messages: WOLVES_CHAT,
    annotation: {
      title: 'SAME SYSTEM, DIFFERENT SOUL',
      points: [
        'The UI just shifted from Arsenal red to Wolves gold',
        'Mood: DESPAIRING \u2014 because 17 pts and 20th place',
        'Dialect: Midlands ("duck")',
        'Same code, same architecture \u2014 completely different emotional output',
      ],
    },
  },
  {
    id: 'memory',
    title: 'The Fan Remembers',
    clubId: 'manchester_city',
    content: 'chat',
    messages: [
      { role: 'user' as const, text: "I was at the Aguero 93:20 match. My dad took me when I was 12." },
      { role: 'assistant' as const, text: `Mate, that's proper special that, honestly. You're talking about one of the greatest moments in football history - 93:20 against QPR. Sergio... he's a legend, our kid. Absolute legend.\n\nTo witness that live, with your old man... that's not just a football memory, that's a life memory. That's the kind of thing you'll tell YOUR kids about one day. I proper envy that.` },
    ],
    annotation: {
      title: 'FAN MEMORY SYSTEM',
      points: [
        'The AI auto-detected a personal memory and stored it',
        'In future conversations, it will recall: "You were there at 93:20!"',
        '"I don\'t just know your club\'s history. I remember YOUR history with your club."',
        'Memories persist across sessions — the AI becomes a fellow traveler',
      ],
    },
  },
  {
    id: 'prediction',
    title: 'The Prediction',
    clubId: 'arsenal',
    content: 'chat',
    messages: [
      { role: 'user' as const, text: "Who do you reckon will win Arsenal vs Bournemouth?" },
      { role: 'assistant' as const, text: `We should take this, mate. My gut says Arsenal, and the numbers back us up — we're creating about 1.75 expected goals to their measly 0.82. That's dominant.\n\nI reckon it'll be a tidy 1-0 job. Could be more, but Bournemouth will park the bus and make it ugly. Either way, three points. The bookies agree — 51% home win.` },
    ],
    annotation: {
      title: 'PREDICTOR EXPLAINABILITY',
      points: [
        'Dixon-Coles + Bookmaker ensemble: 53.9% accuracy, 50% draw precision',
        'The fan doesn\'t recite numbers — they FEEL the prediction',
        '"My gut says Arsenal" is backed by xG, probabilities, and bookmaker odds',
        'Shareable prediction cards at /card/Arsenal/Bournemouth',
      ],
    },
  },
  {
    id: 'stats',
    title: 'The Numbers',
    clubId: null,
    content: 'stats',
  },
  {
    id: 'cta',
    title: '',
    clubId: null,
    content: 'cta',
  },
]

// ─── Main Demo Component ──────────────────────────────────────────

export function Demo() {
  const [sceneIndex, setSceneIndex] = useState(0)
  const [visibleMessages, setVisibleMessages] = useState(0)
  const { setClubId } = useClubTheme()

  const scene = SCENES[sceneIndex]
  const isFirst = sceneIndex === 0
  const isLast = sceneIndex === SCENES.length - 1

  // Apply club theme when scene changes
  useEffect(() => {
    setClubId(scene.clubId)
    setVisibleMessages(0)
  }, [sceneIndex, scene.clubId, setClubId])

  // Progressive message reveal
  useEffect(() => {
    if (scene.content !== 'chat' || !scene.messages) return
    if (visibleMessages >= scene.messages.length) return

    const delay = visibleMessages === 0 ? 400 : 1200
    const timer = setTimeout(() => {
      setVisibleMessages(prev => prev + 1)
    }, delay)
    return () => clearTimeout(timer)
  }, [visibleMessages, scene])

  const next = useCallback(() => {
    if (!isLast) setSceneIndex(i => i + 1)
  }, [isLast])

  const prev = useCallback(() => {
    if (!isFirst) setSceneIndex(i => i - 1)
  }, [isFirst])

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); next() }
      if (e.key === 'ArrowLeft') { e.preventDefault(); prev() }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [next, prev])

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ backgroundColor: theme.colors.background.main }}
    >
      {/* Progress bar */}
      <div className="fixed top-0 left-0 right-0 z-50 h-1" style={{ backgroundColor: theme.colors.background.elevated }}>
        <div
          className="h-full transition-all duration-500 ease-out"
          style={{
            width: `${((sceneIndex + 1) / SCENES.length) * 100}%`,
            backgroundColor: 'var(--club-primary)',
          }}
        />
      </div>

      {/* Scene content */}
      <div className="flex-1 flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-5xl">
          {scene.content === 'pitch' && <PitchScene />}
          {scene.content === 'chat' && (
            <ChatScene
              scene={scene}
              visibleMessages={visibleMessages}
            />
          )}
          {scene.content === 'stats' && <StatsScene />}
          {scene.content === 'cta' && <CTAScene />}
        </div>
      </div>

      {/* Navigation */}
      <div className="fixed bottom-0 left-0 right-0 z-50 p-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <button
            onClick={prev}
            disabled={isFirst}
            className="flex items-center gap-2 px-4 py-2 rounded-lg font-display text-sm font-bold tracking-wide uppercase transition-all disabled:opacity-20"
            style={{ color: theme.colors.text.secondary }}
          >
            <ArrowLeft size={16} />
            BACK
          </button>

          {/* Scene indicators */}
          <div className="flex items-center gap-1.5">
            {SCENES.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setSceneIndex(idx)}
                className="w-2 h-2 rounded-full transition-all duration-300"
                style={{
                  backgroundColor: idx === sceneIndex
                    ? 'var(--club-primary)'
                    : theme.colors.background.elevated,
                  transform: idx === sceneIndex ? 'scale(1.5)' : 'scale(1)',
                }}
              />
            ))}
          </div>

          <button
            onClick={next}
            disabled={isLast}
            className="flex items-center gap-2 px-5 py-2 rounded-lg font-display text-sm font-bold tracking-wide uppercase transition-all disabled:opacity-20"
            style={{
              backgroundColor: 'var(--club-primary)',
              color: 'var(--club-text-on-primary)',
            }}
          >
            NEXT
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Scene Components ─────────────────────────────────────────────

function PitchScene() {
  return (
    <div className="text-center animate-fade-up">
      <div className="mb-8">
        <h1
          className="font-display text-5xl sm:text-7xl font-extrabold tracking-tight uppercase mb-4"
          style={{ color: theme.colors.text.primary }}
        >
          FOOTBALL<span style={{ color: theme.colors.text.muted }}>-AI</span>
        </h1>
        <div
          className="w-16 h-0.5 mx-auto rounded-full mb-6"
          style={{ backgroundColor: 'var(--club-primary)' }}
        />
      </div>

      <p
        className="text-2xl sm:text-3xl italic mb-6 max-w-2xl mx-auto leading-relaxed"
        style={{ color: theme.colors.text.secondary }}
      >
        "What if the AI wasn't neutral?<br />What if it was a fan?"
      </p>

      <p
        className="text-base max-w-xl mx-auto mb-10 leading-relaxed"
        style={{ color: theme.colors.text.muted }}
      >
        A reference implementation of the <strong style={{ color: theme.colors.text.primary }}>4D Persona Architecture</strong> — where AI personalities aren't written. They're computed from data.
      </p>

      <div className="flex flex-wrap gap-3 justify-center">
        {['20 Fan Personas', '230K Matches', '773 KG Nodes', '6 Dialects'].map((stat, i) => (
          <span
            key={i}
            className="px-3 py-1 rounded-full text-xs font-mono animate-fade-up"
            style={{
              backgroundColor: theme.colors.background.elevated,
              color: theme.colors.text.secondary,
              animationDelay: `${400 + i * 100}ms`,
            }}
          >
            {stat}
          </span>
        ))}
      </div>
    </div>
  )
}

function ChatScene({ scene, visibleMessages }: { scene: Scene; visibleMessages: number }) {
  const palette = scene.clubId ? CLUB_PALETTES[scene.clubId] : null
  const clubName = scene.clubId
    ? scene.clubId.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    : ''

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">
      {/* Chat panel */}
      <div className="lg:col-span-3">
        {/* Scene title */}
        <div className="flex items-center gap-3 mb-4">
          {palette && (
            <div
              className="w-3 h-3 rounded-full animate-mood-pulse"
              style={{ backgroundColor: palette.primary }}
            />
          )}
          <h2
            className="font-display text-lg font-bold tracking-wide uppercase"
            style={{ color: theme.colors.text.primary }}
          >
            {scene.title}
            {clubName && (
              <span style={{ color: palette?.primary }}> — {clubName}</span>
            )}
          </h2>
        </div>

        {/* Chat messages */}
        <div
          className="rounded-xl overflow-hidden border"
          style={{
            backgroundColor: theme.colors.background.surface,
            borderColor: palette ? palette.primary + '25' : theme.colors.border.default,
          }}
        >
          {/* Stadium glow */}
          {palette && (
            <div
              className="h-24 -mb-16"
              style={{
                background: `radial-gradient(ellipse 90% 100% at 50% 0%, ${palette.glowColor} 0%, transparent 70%)`,
              }}
            />
          )}

          <div className="p-5 space-y-4">
            {scene.messages?.slice(0, visibleMessages).map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-message-in`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user' ? 'rounded-br-sm' : 'rounded-bl-sm'
                  }`}
                  style={{
                    backgroundColor: msg.role === 'user'
                      ? (palette?.primary || theme.colors.bubbles.user)
                      : theme.colors.background.elevated,
                    color: msg.role === 'user'
                      ? (palette?.textOnPrimary || '#fff')
                      : theme.colors.text.primary,
                    borderLeft: msg.role === 'assistant' && palette
                      ? `3px solid ${palette.primary}40`
                      : undefined,
                  }}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-line">
                    {msg.text}
                  </p>
                </div>
              </div>
            ))}

            {/* Typing indicator while messages are still revealing */}
            {scene.messages && visibleMessages < scene.messages.length && (
              <div className="flex justify-start">
                <div
                  className="rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1.5"
                  style={{
                    backgroundColor: theme.colors.background.elevated,
                    borderLeft: palette ? `3px solid ${palette.primary}40` : undefined,
                  }}
                >
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Annotation panel */}
      {scene.annotation && (
        <div
          className="lg:col-span-2 rounded-xl p-5 border animate-fade-up"
          style={{
            backgroundColor: theme.colors.background.surface,
            borderColor: theme.colors.border.default,
            animationDelay: '600ms',
          }}
        >
          <h3
            className="font-display text-xs font-bold tracking-widest uppercase mb-4"
            style={{ color: palette?.primary || theme.colors.text.secondary }}
          >
            {scene.annotation.title}
          </h3>
          <ul className="space-y-3">
            {scene.annotation.points.map((point, idx) => (
              <li
                key={idx}
                className="flex gap-2 text-sm leading-relaxed"
              >
                <div
                  className="w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0"
                  style={{ backgroundColor: palette?.primary || theme.colors.text.muted }}
                />
                <span style={{ color: theme.colors.text.secondary }}>
                  {point}
                </span>
              </li>
            ))}
          </ul>

          {/* 4D Radar in annotation panel when a club is active */}
          {scene.clubId && (
            <div className="mt-4 flex justify-center">
              <FourDRadar clubId={scene.clubId} size={120} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StatsScene() {
  const stats = [
    { value: '773', label: 'Knowledge Graph Nodes', sub: '362 persons, 54 matches, 25 clubs' },
    { value: '717', label: 'Relationship Edges', sub: '43 rivalries, 43 iconic matches' },
    { value: '230,557', label: 'Historical Matches', sub: 'Premier League 2000\u20132025' },
    { value: '136', label: 'Trivia Questions', sub: 'Auto-mined from match database' },
    { value: '20', label: 'Fan Personas', sub: '6 dialects + kinetic mood theming' },
    { value: '102', label: 'Passing Tests', sub: 'Behavioral + integration + KG' },
    { value: '90', label: 'API Endpoints', sub: 'FastAPI + rate limiting + budget cap' },
    { value: '53.9%', label: 'Prediction Accuracy', sub: 'Dixon-Coles + Bookmaker (50% draw)' },
  ]

  return (
    <div className="animate-fade-up">
      <h2
        className="font-display text-3xl font-extrabold tracking-wide uppercase text-center mb-2"
        style={{ color: theme.colors.text.primary }}
      >
        THE NUMBERS
      </h2>
      <p className="text-center text-sm mb-10" style={{ color: theme.colors.text.muted }}>
        What powers the 4D Persona Architecture
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {stats.map((stat, idx) => (
          <div
            key={idx}
            className="rounded-xl p-4 border text-center animate-fade-up"
            style={{
              backgroundColor: theme.colors.background.surface,
              borderColor: theme.colors.border.default,
              animationDelay: `${idx * 80}ms`,
            }}
          >
            <div
              className="font-mono text-2xl font-bold mb-1"
              style={{ color: theme.colors.text.primary }}
            >
              {stat.value}
            </div>
            <div
              className="font-display text-xs font-bold tracking-wide uppercase mb-1"
              style={{ color: theme.colors.text.secondary }}
            >
              {stat.label}
            </div>
            <div
              className="text-xs"
              style={{ color: theme.colors.text.muted }}
            >
              {stat.sub}
            </div>
          </div>
        ))}
      </div>

      {/* 4D Architecture compact */}
      <div
        className="mt-8 rounded-xl p-6 border animate-fade-up"
        style={{
          backgroundColor: theme.colors.background.surface,
          borderColor: theme.colors.border.default,
          animationDelay: '700ms',
        }}
      >
        <h3
          className="font-display text-sm font-bold tracking-widest uppercase text-center mb-4"
          style={{ color: theme.colors.text.secondary }}
        >
          THE 4D POSITION: P(t) = (x, y, z, t)
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          {[
            { dim: 'X', name: 'Emotional', desc: 'Mood from match results', color: '#ef4444' },
            { dim: 'Y', name: 'Relational', desc: 'Rivalry from KG edges', color: '#f59e0b' },
            { dim: 'Z', name: 'Linguistic', desc: 'Regional dialect', color: '#3b82f6' },
            { dim: 'T', name: 'Temporal', desc: 'Conversation trajectory', color: '#8b5cf6' },
          ].map((d) => (
            <div key={d.dim}>
              <div
                className="font-mono text-xl font-bold"
                style={{ color: d.color }}
              >
                {d.dim}
              </div>
              <div
                className="font-display text-xs font-bold tracking-wide uppercase"
                style={{ color: theme.colors.text.primary }}
              >
                {d.name}
              </div>
              <div className="text-xs" style={{ color: theme.colors.text.muted }}>
                {d.desc}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function CTAScene() {
  return (
    <div className="text-center animate-fade-up">
      <h2
        className="font-display text-4xl sm:text-5xl font-extrabold tracking-tight uppercase mb-3"
        style={{ color: theme.colors.text.primary }}
      >
        FAN AT HEART
      </h2>
      <p
        className="font-display text-2xl sm:text-3xl font-bold tracking-wide uppercase mb-8"
        style={{ color: theme.colors.text.muted }}
      >
        ARCHITECT BY DISCOVERY
      </p>

      <div className="flex flex-wrap gap-4 justify-center mb-12">
        <Link
          to="/chat"
          className="flex items-center gap-2 px-6 py-3 rounded-xl font-display font-bold tracking-wide uppercase text-sm transition-all hover:scale-105"
          style={{
            backgroundColor: 'var(--club-primary)',
            color: 'var(--club-text-on-primary)',
          }}
        >
          <Play size={16} />
          TRY IT LIVE
        </Link>

        <a
          href="https://github.com/Eyalio84/Football-AI"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-6 py-3 rounded-xl font-display font-bold tracking-wide uppercase text-sm transition-all hover:scale-105 border"
          style={{
            borderColor: theme.colors.border.strong,
            color: theme.colors.text.secondary,
          }}
        >
          <Github size={16} />
          VIEW SOURCE
        </a>

        <a
          href="/docs/arxiv/4d-persona-architecture-v2.pdf"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-6 py-3 rounded-xl font-display font-bold tracking-wide uppercase text-sm transition-all hover:scale-105 border"
          style={{
            borderColor: theme.colors.border.strong,
            color: theme.colors.text.secondary,
          }}
        >
          <FileText size={16} />
          READ THE PAPER
        </a>

        <a
          href="https://www.verbalogix.com"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-6 py-3 rounded-xl font-display font-bold tracking-wide uppercase text-sm transition-all hover:scale-105 border"
          style={{
            borderColor: theme.colors.border.strong,
            color: theme.colors.text.secondary,
          }}
        >
          <Globe size={16} />
          PORTFOLIO
        </a>
      </div>

      <p
        className="text-sm italic"
        style={{ color: theme.colors.text.muted }}
      >
        Built by Eyal Nof
      </p>
      <p
        className="text-xs mt-1 font-mono"
        style={{ color: theme.colors.text.muted }}
      >
        4D Persona Architecture &middot; Embodied RAG &middot; December 2025 &ndash; April 2026
      </p>
    </div>
  )
}
