/**
 * TypeScript Type Definitions
 *
 * These types match the backend API contract defined in api_design.md
 */

// ============================================================================
// Message Types
// ============================================================================

export type MessageRole = 'user' | 'assistant'

export interface Message {
  id: string
  role: MessageRole
  content: string
  timestamp: Date
  isLoading?: boolean  // Used for showing "typing" indicator
  sources?: Source[]   // For rich message rendering
}

// ============================================================================
// API Request/Response Types (matches backend)
// ============================================================================

export interface ChatRequest {
  message: string
  conversation_id?: string
  club_id?: string  // Fan persona system: manchester-united, arsenal, or chelsea
}

export interface Source {
  type: 'player' | 'team' | 'game' | 'injury' | 'news' | 'transfer'
  id: number
  relevance?: number
}

export interface ChatResponse {
  response: string
  conversation_id: string
  sources: Source[]
  confidence: number
  timestamp?: string
}

export interface ApiError {
  detail: string
  error_code?: string
}

// ============================================================================
// Entity Types (for future features like showing player cards)
// ============================================================================

export interface Player {
  id: number
  name: string
  team: string
  position: string
  nationality: string
}

export interface Team {
  id: number
  name: string
  short_name?: string
  league: string
  country?: string
  stadium?: string | null
  founded?: number | null
  logo_url?: string | null
  manager?: string
  created_at?: string
  updated_at?: string
}

export interface Game {
  id: number
  date: string
  time?: string
  home_team?: {
    id?: number
    name: string
    short?: string
    score?: number | null
  }
  away_team?: {
    id?: number
    name: string
    short?: string
    score?: number | null
  }
  home_team_id?: number
  away_team_id?: number
  home_team_name?: string
  away_team_name?: string
  home_team_short?: string
  away_team_short?: string
  home_score?: number | null
  away_score?: number | null
  status: 'scheduled' | 'in_progress' | 'finished'
  venue?: string
  competition?: string
  attendance?: number | null
  referee?: string | null
}

export interface Injury {
  id: number
  player_name: string
  team_name: string
  injury_type: string
  severity: string
  expected_return?: string
  status: 'active' | 'recovered'
}

// ============================================================================
// Club Personality Types (KG-powered features)
// ============================================================================

export interface Legend {
  id: number
  name: string
  team_id: number
  position?: string
  era?: string
  goals?: number
  appearances?: number
  achievements?: string
}

export interface Rivalry {
  id: number
  team_id: number
  rival_team_id: number
  rival_team_name?: string
  intensity: number  // 1-10
  derby_name?: string
  historical_context?: string
}

export interface Moment {
  id: number
  team_id: number
  title: string
  date?: string
  opponent?: string
  competition?: string
  result?: string
  significance?: string
  emotion?: 'triumph' | 'heartbreak' | 'joy' | 'defiance' | 'vindication' | string
  keywords?: string
}

export interface TeamIdentity {
  id: number
  team_id: number
  chant?: string
  nickname?: string
  values?: string
  playing_style?: string
}

export interface TeamMood {
  current_mood: string
  mood_intensity: number
  last_result?: string
  mood_factors?: string[]
}

export interface TeamPersonality {
  team: Team
  identity?: TeamIdentity
  mood?: TeamMood
  rivalries: Rivalry[]
  moments: Moment[]
  legends: Legend[]
}

// ============================================================================
// Knowledge Graph Types
// ============================================================================

export interface KGNode {
  id: number | string
  label: string
  group: 'team' | 'legend' | 'moment'
  color: string
  shape?: string
  size?: number
  title?: string  // Tooltip
}

export interface KGEdge {
  from: number | string
  to: number | string
  label: string
  color?: string
  arrows?: string
  dashes?: boolean
  width?: number
}

export interface KGGraph {
  nodes: KGNode[]
  edges: KGEdge[]
  stats: {
    total_nodes: number
    total_edges: number
    by_type: Record<string, number>
    by_relationship?: Record<string, number>
  }
}

export interface KGSubgraph extends KGGraph {
  center?: string
  depth?: number
  team?: Team
}

// ============================================================================
// UI State Types
// ============================================================================

export interface ChatState {
  messages: Message[]
  conversationId: string | null
  isLoading: boolean
  error: string | null
}

// ============================================================================
// Trivia Types
// ============================================================================

export interface TriviaQuestion {
  question_id: number
  question: string
  answers: string[]
  category: 'history' | 'players' | 'matches' | 'legends' | 'stadium' | string
  difficulty: 'easy' | 'medium' | 'hard'
}

export interface TriviaResult {
  correct: boolean
  correct_answer: string
  explanation?: string
  stats?: {
    times_asked: number
    times_correct: number
    accuracy: number
  }
}

export interface TriviaStats {
  total_questions: number
  questions_by_category: Record<string, number>
  questions_by_difficulty: Record<string, number>
  average_accuracy: number
}

// ============================================================================
// Prediction Types
// ============================================================================

export interface MatchPrediction {
  match: string
  favorite: string
  underdog: string
  upset_probability: number
  confidence: 'low' | 'medium' | 'high'
  factors: {
    side_a: string[]  // Favorite weaknesses
    side_b: string[]  // Underdog strengths
    patterns: string[]  // Third Knowledge bonuses
  }
  key_insight?: string
}

export interface PredictionPattern {
  id: string
  name: string
  trigger: string[]
  bonus: number
  description: string
}

// ============================================================================
// Utility Types
// ============================================================================

export type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: string }
