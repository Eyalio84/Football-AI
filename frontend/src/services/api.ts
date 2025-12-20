/**
 * API Service
 *
 * Handles all communication with the FastAPI backend.
 * Uses native fetch API for HTTP requests.
 */

import type {
  ChatRequest, ChatResponse, Player, Team, Game, Injury,
  Legend, Rivalry, Moment, TeamMood, TeamPersonality,
  KGGraph, KGSubgraph
} from '../types'

// ============================================================================
// Configuration
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_PREFIX = '/api/v1'

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${API_PREFIX}${endpoint}`

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }))
      throw new Error(errorData.detail || 'An error occurred')
    }

    return await response.json()
  } catch (error) {
    if (error instanceof Error) {
      throw error
    }
    throw new Error('Network error occurred')
  }
}

// ============================================================================
// Chat API
// ============================================================================

/**
 * Send a message to the AI chatbot
 *
 * @param message - User's question/message
 * @param conversationId - Optional conversation ID to continue a conversation
 * @returns AI response with sources and confidence
 */
export async function sendChatMessage(
  message: string,
  conversationId?: string,
  clubId?: string
): Promise<ChatResponse> {
  const request: ChatRequest = {
    message,
    ...(conversationId && { conversation_id: conversationId }),
    ...(clubId && { club_id: clubId }),
  }

  return fetchAPI<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

/**
 * Send a message with streaming response (SSE)
 *
 * @param message - User's question/message
 * @param conversationId - Optional conversation ID
 * @param clubId - Optional club persona
 * @param onChunk - Callback for each text chunk
 * @param onDone - Callback when stream completes
 * @param onError - Callback on error
 */
export async function sendChatMessageStream(
  message: string,
  conversationId: string | undefined,
  clubId: string | undefined,
  onChunk: (text: string) => void,
  onDone: (conversationId: string) => void,
  onError: (error: string) => void
): Promise<void> {
  const url = `${API_BASE_URL}${API_PREFIX}/chat/stream`

  const request: ChatRequest = {
    message,
    ...(conversationId && { conversation_id: conversationId }),
    ...(clubId && { club_id: clubId }),
  }

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let buffer = ''
    let newConversationId = conversationId || ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Process complete SSE events
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)

          if (data === '[DONE]') {
            onDone(newConversationId)
            return
          }

          try {
            const parsed = JSON.parse(data)
            if (parsed.text) {
              onChunk(parsed.text)
            }
            if (parsed.conversation_id) {
              newConversationId = parsed.conversation_id
            }
            if (parsed.error) {
              onError(parsed.error)
              return
            }
          } catch {
            // Not JSON, treat as plain text chunk
            if (data.trim()) {
              onChunk(data)
            }
          }
        }
      }
    }

    onDone(newConversationId)
  } catch (error) {
    onError(error instanceof Error ? error.message : 'Stream failed')
  }
}

/**
 * Get available club personas
 */
export async function getClubs(): Promise<Array<{ id: string; name: string }>> {
  const response = await fetchAPI<{ data: Array<{ id: string; name: string }> }>('/clubs')
  return response.data
}

// ============================================================================
// Entity APIs (for future features)
// ============================================================================

/**
 * Get list of players
 */
export async function getPlayers(limit = 50): Promise<Player[]> {
  return fetchAPI<Player[]>(`/players?limit=${limit}`)
}

/**
 * Get list of teams
 */
export async function getTeams(limit = 50): Promise<Team[]> {
  const response = await fetchAPI<{ data: Team[] }>(`/teams?limit=${limit}`)
  return response.data
}

/**
 * Get a specific team
 */
export async function getTeam(id: number): Promise<Team> {
  const response = await fetchAPI<{ data: Team }>(`/teams/${id}`)
  return response.data
}

/**
 * Get team's upcoming fixtures
 */
export async function getTeamFixtures(id: number): Promise<Game[]> {
  const response = await fetchAPI<{ data: Game[] }>(`/teams/${id}/fixtures`)
  return response.data
}

/**
 * Get team's recent results
 */
export async function getTeamResults(id: number): Promise<Game[]> {
  const response = await fetchAPI<{ data: Game[] }>(`/teams/${id}/results`)
  return response.data
}

/**
 * Transform backend game response to include nested team objects
 */
function transformGame(game: any): Game {
  return {
    ...game,
    home_team: {
      id: game.home_team_id,
      name: game.home_team_name || game.home_team || '',
      short: game.home_team_short,
      score: game.home_score,
    },
    away_team: {
      id: game.away_team_id,
      name: game.away_team_name || game.away_team || '',
      short: game.away_team_short,
      score: game.away_score,
    },
  }
}

/**
 * Get list of games
 */
export async function getGames(limit = 50): Promise<Game[]> {
  const response = await fetchAPI<{ data: any[] }>(`/games?limit=${limit}`)
  return response.data.map(transformGame)
}

/**
 * Get today's games
 */
export async function getGamesToday(): Promise<Game[]> {
  const today = new Date().toISOString().split('T')[0]
  const response = await fetchAPI<{ data: any[] }>(`/games?date_from=${today}&date_to=${today}`)
  return response.data.map(transformGame)
}

/**
 * Get upcoming games (scheduled status)
 */
export async function getGamesUpcoming(limit = 20): Promise<Game[]> {
  const response = await fetchAPI<{ data: any[] }>(`/games?status=scheduled&limit=${limit}`)
  return response.data.map(transformGame)
}

/**
 * Get live games (in_progress status)
 */
export async function getGamesLive(): Promise<Game[]> {
  const response = await fetchAPI<{ data: any[] }>('/games?status=in_progress')
  return response.data.map(transformGame)
}

/**
 * Get a specific game
 */
export async function getGame(id: number): Promise<Game> {
  const response = await fetchAPI<{ data: any }>(`/games/${id}`)
  return transformGame(response.data)
}

/**
 * Get active injuries
 */
export async function getActiveInjuries(): Promise<Injury[]> {
  return fetchAPI<Injury[]>('/injuries/active')
}

/**
 * Search across all data
 */
export async function searchAll(query: string): Promise<any> {
  return fetchAPI<any>(`/search?q=${encodeURIComponent(query)}`)
}

/**
 * Get league standings
 */
export async function getStandings(league: string = 'Premier League'): Promise<any[]> {
  const response = await fetchAPI<{ data: any[] }>(`/standings/${encodeURIComponent(league)}`)
  return response.data
}

/**
 * Health check
 */
export async function checkHealth(): Promise<{ status: string }> {
  const url = `${API_BASE_URL}/health`
  const response = await fetch(url)
  return response.json()
}

// ============================================================================
// Club Personality APIs (KG-powered)
// ============================================================================

/**
 * Get all legends
 */
export async function getLegends(teamId?: number): Promise<Legend[]> {
  const params = teamId ? `?team_id=${teamId}` : ''
  const response = await fetchAPI<{ data: Legend[] }>(`/legends${params}`)
  return response.data
}

/**
 * Get legends for a specific team
 */
export async function getTeamLegends(teamId: number): Promise<{ team: Team; legends: Legend[] }> {
  const response = await fetchAPI<{ data: { team: Team; legends: Legend[] } }>(`/teams/${teamId}/legends`)
  return response.data
}

/**
 * Get team rivalries
 */
export async function getTeamRivalries(teamId: number): Promise<{ team: Team; rivalries: Rivalry[] }> {
  const response = await fetchAPI<{ data: { team: Team; rivalries: Rivalry[] } }>(`/teams/${teamId}/rivalries`)
  return response.data
}

/**
 * Get team moments
 */
export async function getTeamMoments(teamId: number): Promise<{ team: Team; moments: Moment[] }> {
  const response = await fetchAPI<{ data: { team: Team; moments: Moment[] } }>(`/teams/${teamId}/moments`)
  return response.data
}

/**
 * Get team mood
 */
export async function getTeamMood(teamId: number): Promise<{ team: Team; mood: TeamMood | null }> {
  const response = await fetchAPI<{ data: { team: Team; mood: TeamMood | null } }>(`/teams/${teamId}/mood`)
  return response.data
}

/**
 * Get full team personality (identity, mood, rivalries, moments, legends)
 */
export async function getTeamPersonality(teamId: number): Promise<TeamPersonality> {
  const response = await fetchAPI<{ data: TeamPersonality }>(`/teams/${teamId}/personality`)
  return response.data
}

// ============================================================================
// Knowledge Graph APIs
// ============================================================================

/**
 * Get full Knowledge Graph in vis.js format
 */
export async function getKGGraph(): Promise<KGGraph> {
  const response = await fetchAPI<{ data: KGGraph }>('/graph')
  return response.data
}

/**
 * Get subgraph centered on a node
 */
export async function getKGSubgraph(nodeId: string | number, depth: number = 1): Promise<KGSubgraph> {
  const response = await fetchAPI<{ data: KGSubgraph }>(`/graph/subgraph/${nodeId}?depth=${depth}`)
  return response.data
}

/**
 * Get KG subgraph for a team
 */
export async function getTeamKGGraph(teamId: number, depth: number = 2): Promise<KGSubgraph> {
  const response = await fetchAPI<{ data: KGSubgraph }>(`/graph/team/${teamId}?depth=${depth}`)
  return response.data
}

/**
 * Get KG Viewer URL
 */
export function getKGViewerUrl(): string {
  return `${API_BASE_URL}/kg-viewer`
}

// ============================================================================
// Trivia APIs
// ============================================================================

export interface TriviaQuestion {
  question_id: number
  question: string
  answers: string[]
  category: string
  difficulty: string
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

/**
 * Get a trivia question
 */
export async function getTriviaQuestion(
  teamId?: number,
  category?: string,
  difficulty?: string
): Promise<TriviaQuestion | null> {
  const params = new URLSearchParams()
  if (teamId) params.append('team_id', String(teamId))
  if (category) params.append('category', category)
  if (difficulty) params.append('difficulty', difficulty)

  const queryString = params.toString() ? `?${params.toString()}` : ''
  const response = await fetchAPI<{ data: TriviaQuestion | null }>(`/trivia${queryString}`)
  return response.data
}

/**
 * Check a trivia answer
 */
export async function checkTriviaAnswer(
  questionId: number,
  answer: string
): Promise<TriviaResult> {
  const response = await fetchAPI<{ data: TriviaResult }>(
    `/trivia/check?question_id=${questionId}&answer=${encodeURIComponent(answer)}`,
    { method: 'POST' }
  )
  return response.data
}

/**
 * Get trivia statistics
 */
export async function getTriviaStats(teamId?: number): Promise<any> {
  const queryString = teamId ? `?team_id=${teamId}` : ''
  const response = await fetchAPI<{ data: any }>(`/trivia/stats${queryString}`)
  return response.data
}

// ============================================================================
// Prediction APIs
// ============================================================================

export interface MatchPrediction {
  match: string
  favorite: string
  underdog: string
  upset_probability: number
  confidence: string
  factors: {
    side_a: string[]
    side_b: string[]
    patterns: string[]
  }
  key_insight?: string
}

/**
 * Get match prediction (manual data)
 */
export async function getMatchPrediction(
  homeTeam: string,
  awayTeam: string,
  homeData: object = {},
  awayData: object = {}
): Promise<MatchPrediction> {
  const response = await fetchAPI<{ data: MatchPrediction }>('/predict', {
    method: 'POST',
    body: JSON.stringify({
      home_team: homeTeam,
      away_team: awayTeam,
      home_data: homeData,
      away_data: awayData,
    }),
  })
  return response.data
}

/**
 * Get live match prediction (using external APIs)
 */
export async function getMatchPredictionLive(
  homeTeam: string,
  awayTeam: string
): Promise<MatchPrediction> {
  const response = await fetchAPI<{ data: MatchPrediction }>('/predict/live', {
    method: 'POST',
    body: JSON.stringify({
      home_team: homeTeam,
      away_team: awayTeam,
    }),
  })
  return response.data
}

/**
 * Get prediction patterns
 */
export async function getPredictionPatterns(): Promise<any[]> {
  const response = await fetchAPI<{ data: any[] }>('/predict/patterns')
  return response.data
}

/**
 * Get match preview with prediction
 */
export async function getMatchPreview(
  homeTeamId: number,
  awayTeamId: number
): Promise<any> {
  const response = await fetchAPI<{ data: any }>(`/match/preview/${homeTeamId}/${awayTeamId}`)
  return response.data
}
