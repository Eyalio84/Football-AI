// API Response Wrapper
export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  meta?: {
    limit?: number;
    offset?: number;
    timestamp?: string;
    [key: string]: any;
  };
  error?: {
    code: string;
    message: string;
  };
}

// Club for persona selection
export interface Club {
  id: string;      // "arsenal", "chelsea", etc.
  name: string;    // "Arsenal", "Chelsea", etc.
}

// Chat
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  club?: string;   // Persona used for this message
  confidence?: number;
}

export interface ChatRequest {
  message: string;           // 1-1000 chars
  conversation_id?: string;  // Optional, creates new if omitted
  club?: string;             // Fan persona: "arsenal", "chelsea", etc.
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  sources: Array<{ type: string; id?: number; }>;
  confidence: number;        // 0-1
  usage?: { input_tokens: number; output_tokens: number; };
}

// Team
export interface Team {
  id: number;
  name: string;
  short_name?: string;
  league: string;
  country: string;
  stadium?: string;
  founded?: number;
  logo_url?: string;
}

// Game/Fixture
export interface Game {
  id: number;
  date: string;              // "YYYY-MM-DD"
  time?: string;             // "HH:MM"
  status: 'scheduled' | 'live' | 'finished';
  home_team_id: number;
  home_team_name: string;
  home_team_short?: string;
  away_team_id: number;
  away_team_name: string;
  away_team_short?: string;
  home_score?: number;
  away_score?: number;
  competition?: string;
  venue?: string;
}

// Standing
export interface Standing {
  position: number;
  team_id: number;
  team_name: string;
  short_name?: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  form?: string;             // "WWDLW" - last 5 results
}

// Prediction
export interface Prediction {
  home_team: string;
  away_team: string;
  favorite: string;
  underdog: string;
  side_a_score: number;      // Favorite weakness (0-100)
  side_b_score: number;      // Underdog strength (0-100)
  base_upset_prob: number;   // 0-1
  pattern_multiplier: number;
  final_upset_prob: number;  // 0-1
  patterns_triggered: Array<{
    name: string;
    multiplier: number;
    confidence: number;
  }>;
  confidence_level: 'low' | 'medium' | 'high';
  key_insight: string;
}

export interface ClubColors {
  primary: string;
  secondary: string;
}