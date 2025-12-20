# Soccer-AI API Contracts

**Last Updated**: 2026-04-10
**Backend**: FastAPI (port 8000)
**Total Endpoints**: 91

---

## Response Wrapper (All Endpoints)

```typescript
interface ApiResponse<T> {
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
```

---

## 1. CHAT (Primary Interface) ⭐

### POST /api/v1/chat

**Request:**
```typescript
interface ChatRequest {
  message: string;           // 1-1000 chars
  conversation_id?: string;  // Optional, creates new if omitted
  club?: string;             // Fan persona: "arsenal", "chelsea", etc.
}
```

**Response:**
```typescript
interface ChatResponse {
  response: string;
  conversation_id: string;
  sources: Array<{
    type: string;
    id?: number;
  }>;
  confidence: number;        // 0-1
  usage?: {
    input_tokens: number;
    output_tokens: number;
  };
}
```

**Valid Clubs:**
```
arsenal, chelsea, manchester_united, liverpool, manchester_city,
tottenham, newcastle, west_ham, everton, brighton, aston_villa,
wolves, crystal_palace, fulham, nottingham_forest, brentford,
bournemouth, ipswich, southampton, analyst (neutral)
```

**Club Aliases (auto-resolved):**
```
man_united, man_utd, united -> manchester_united
man_city, city              -> manchester_city
spurs                       -> tottenham
villa                       -> aston_villa
palace                      -> crystal_palace
forest                      -> nottingham_forest
hammers                     -> west_ham
toon                        -> newcastle
wolves                      -> wolverhampton
```

---

## 2. CLUBS & PERSONAS ⭐

### GET /api/v1/clubs

**Response:**
```typescript
interface Club {
  id: string;      // "arsenal"
  name: string;    // "Arsenal"
}
// Returns: ApiResponse<Club[]>
```

### GET /api/v1/personas

**Response:**
```typescript
interface Persona {
  club_key: string;
  team_id: number;
  display_name: string;
  identity: {
    nickname?: string;
    founded?: number;
    stadium?: string;
    colors?: string;
    philosophy?: string;
  };
  mood: {
    current_mood: string;      // "optimistic", "anxious", etc.
    intensity: number;         // 0-1
    last_updated: string;
  };
}
// Returns: ApiResponse<{ personas: Persona[], total: number }>
```

---

## 3. TEAMS

### GET /api/v1/teams

**Query Params:** `league?`, `limit?` (1-100), `offset?`

**Response:**
```typescript
interface Team {
  id: number;
  name: string;
  short_name?: string;
  league: string;
  country: string;
  stadium?: string;
  founded?: number;
  logo_url?: string;
}
// Returns: ApiResponse<Team[]>
```

### GET /api/v1/teams/{team_id}

Returns single `Team` with same shape.

### GET /api/v1/teams/{team_id}/personality

**Response (Full Club Context):**
```typescript
{
  team: Team;
  identity: {
    nickname?: string;
    founded?: number;
    stadium?: string;
    manager?: string;
    philosophy?: string;
  };
  mood: {
    current_mood: string;
    intensity: number;
  };
  rivalries: Array<{
    rival_team_id: number;
    rival_name: string;
    rivalry_name: string;
    intensity: number;        // 1-10
  }>;
  moments: Array<{
    id: number;
    title: string;
    date: string;
    emotion: string;
    description: string;
  }>;
  legends: Array<{
    id: number;
    name: string;
    position: string;
    years_active: string;
  }>;
}
```

---

## 4. FIXTURES & GAMES ⭐

### GET /api/v1/games/today

**Response:**
```typescript
interface Game {
  id: number;
  date: string;              // "YYYY-MM-DD"
  time?: string;             // "HH:MM"
  status: string;            // "scheduled", "live", "finished"
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
// Returns: ApiResponse<Game[]>
```

### GET /api/v1/games/upcoming

Same response shape as above.

### GET /api/v1/games/live

Same response shape (filtered to live matches).

---

## 5. STANDINGS ⭐

### GET /api/v1/standings/{league}

**Query Params:** `season?` (default: "2025-26")

**Response:**
```typescript
interface StandingEntry {
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
// Returns: ApiResponse<StandingEntry[]>
```

---

## 6. PREDICTIONS ⭐

### POST /api/v1/predict

**Query Params:**
- `home_team` (string)
- `away_team` (string)
- `favorite` (string)
- `underdog` (string)
- `match_date?` (string)

**Response:**
```typescript
interface Prediction {
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
  confidence_level: string;  // "low", "medium", "high"
  key_insight: string;
}
```

### GET /api/v1/predict/patterns

**Response:**
```typescript
interface Pattern {
  name: string;
  description: string;
  factor_a: string;
  factor_b: string;
  interaction_type: string;
  multiplier: number;
  confidence: number;
}
// Returns: ApiResponse<{ patterns: Pattern[], total: number }>
```

### GET /api/v1/match/preview/{home_team_id}/{away_team_id}

**Response (Bridge Endpoint):**
```typescript
{
  match: {
    home_team: Team;
    away_team: Team;
    is_derby: boolean;
    derby_info?: object;
  };
  fan_context: {
    home: { identity: object; mood: object };
    away: { identity: object; mood: object };
  };
  predictor_context: {
    home_insights: object[];
    away_insights: object[];
    prediction: Prediction;
  };
  talking_points: string[];
}
```

---

## 7. LEGENDS

### GET /api/v1/legends

**Query Params:** `team_id?`, `limit?`

**Response:**
```typescript
interface Legend {
  id: number;
  name: string;
  team_id?: number;
  position?: string;
  years_active?: string;
  achievements?: string;
  defining_moment?: string;
  legacy_description?: string;
}
// Returns: ApiResponse<Legend[]>
```

### POST /api/v1/legends/{legend_id}/tell-story

**Query Params:** `angle` ("career" | "moment" | "legacy")

**Response:**
```typescript
{
  legend: Legend;
  story: string;             // AI-generated narrative
  angle: string;
  team: Team;
}
```

---

## 8. FAN PERSONA & 4D STATE

### GET /api/v1/fan/{club}/mood

**Response:**
```typescript
{
  club: string;
  mood: {
    current_mood: string;       // "euphoric", "confident", "steady", "anxious", "despairing"
    mood_intensity: number;     // 0-1
    mood_reason: string;
    form: string;               // "WWDLD"
    goals_for: number;
    goals_against: number;
    goal_difference: number;
  };
  dialect: string | null;
  timestamp: string;
}
```

### GET /api/v1/fan/{club}/full

Returns mood + rivalry (if message provided) + dialect combined.

### GET /api/v1/fan/{club}/4d-state

**Response:**
```typescript
{
  club: string;
  position_4d: {
    x: { mood: string; intensity: number; reason: string };
    y: { rivalry_active: boolean; rival?: string; intensity?: number };
    z: { dialect: string; region: string; phrases: string[] };
    t: { trajectory: string; momentum: number };
  };
  timestamp: string;
}
```

### POST /api/v1/fan/{club}/check-rivalry

**Body:** `message` (string)

**Response:**
```typescript
{
  club: string;
  message: string;
  rivalry_detected: boolean;
  rivalry: {
    rival: string;
    rival_display: string;
    intensity: number;          // 0.6-1.0
    derby_name: string;
    banter: string[];
  } | null;
}
```

---

## 8A. LIVE DATA (football-data.org)

Auto-refreshed every 6 hours. 5-minute cache TTL.

### GET /api/v1/live/standings

**Response:** Live Premier League table with position, played, won, drawn, lost, GF, GA, GD, points.

### GET /api/v1/live/fixtures

**Response:** Upcoming fixtures (next 14 days) with date, time, teams, matchday.

### GET /api/v1/live/results

**Response:** Recent results (last 14 days) with scores and status.

### GET /api/v1/live/team/{name}

**Response:** Team context from live API (form, position, upcoming fixtures).

---

## 9. TRIVIA (136 questions, 6 categories)

### GET /api/v1/trivia

**Query Params:** `team_id?`, `category?`, `difficulty?`

**Categories:** `records`, `head2head`, `history`, `stats`, `rivalries`, `legends`
**Difficulties:** `easy` (20), `medium` (57), `hard` (59)

**Response:**
```typescript
interface TriviaQuestion {
  id: number;
  question: string;
  correct_answer: string;
  wrong_answers: string[];     // 3 distractors
  difficulty: string;          // "easy", "medium", "hard"
  category: string;
  team_id?: number;
  explanation: string;
  times_asked: number;
  times_correct: number;
}
// Returns: ApiResponse<TriviaQuestion>
```

### POST /api/v1/trivia/check

**Query Params:** `question_id`, `answer`

**Response:**
```typescript
{
  correct: boolean;
  correct_answer: string;
  explanation: string;
  your_answer: string;
}
```

### GET /api/v1/trivia/stats

**Response:**
```typescript
{
  total_questions: number;      // 136
  by_category: Record<string, number>;
  by_difficulty: Record<string, number>;
}
```

---

## 9A. FAN DEBATE

### POST /api/v1/debate

Two fan personas debate a topic, taking turns. Each sees the other's previous response.

**Request:**
```typescript
{
  club_a: string;       // e.g., "arsenal" (aliases work)
  club_b: string;       // e.g., "tottenham"
  topic: string;        // e.g., "Who is the bigger club?"
  rounds?: number;      // 1-5, default 3
}
```

**Response:**
```typescript
{
  success: true;
  data: {
    club_a: string;
    club_b: string;
    topic: string;
    rounds: number;
    exchanges: Array<{
      club: string;           // Club ID
      club_display: string;   // "Arsenal"
      text: string;           // The persona's argument
      round: number;          // Which round (1-based)
    }>;
  };
}
```

**Notes:**
- Each persona has mood, rivalry, and dialect injected
- Responses reference real club history, legends, and achievements
- Rivalry intensity fires for both sides if they're rivals
- 3 rounds = 6 exchanges (club A speaks, club B responds, repeat)

---

## 9B. V2 PREDICTIONS (Dixon-Coles + Bookmaker)

Upgraded prediction system: 53.9% accuracy, 50% draw precision.

### GET /api/v1/predict/v2/{home_team}/{away_team}

**Response:**
```typescript
{
  success: true;
  data: {
    home_team: string;
    away_team: string;
    prediction: string;        // "Arsenal Win" | "Draw" | "Bournemouth Win"
    confidence: number;        // 0-1
    probabilities: {
      home_win: number;
      draw: number;
      away_win: number;
    };
    expected_goals: {
      home: number;            // e.g., 1.75
      away: number;            // e.g., 0.82
    };
    most_likely_score: string; // "1-0"
    dixon_coles: {
      home_win: number;
      draw: number;
      away_win: number;
      rho: number;             // Correlation parameter
    };
    bookmaker: {
      available: boolean;
      home_win: number | null;
      draw: number | null;
      away_win: number | null;
      raw_odds: { home: number; draw: number; away: number } | null;
    };
    model: string;
  };
}
```

### GET /api/v1/predict/v2/upcoming

Returns V2 predictions for all upcoming fixtures.

### GET /api/v1/predict/v2/backtest

Returns accuracy metrics: accuracy, draw precision, Brier score for Dixon-Coles, Bookmaker, and ensemble.

---

## 9C. LIVE MATCH COMPANION

### GET /api/v1/live/companion/matches

Lists available simulated matches for demo/testing.

### POST /api/v1/live/companion/simulate/{match_key}/{club}

Start a simulated match. Returns `session_id` for polling.

### GET /api/v1/live/companion/events/{session_id}?after=N

Poll for new events (incremental). Returns:
```typescript
{
  success: true;
  data: {
    session_id: string;
    home_team: string;
    away_team: string;
    score_home: number;
    score_away: number;
    status: string;
    finished: boolean;
    events: Array<{
      type: "event";
      event_type: string;      // "kickoff" | "goal" | "goal_conceded" | "halftime" | "fulltime"
      minute: string;          // "23'" | "HT" | "FT"
      description: string;
      reaction: string;        // Fan persona reaction (generated by Haiku)
      score_home: number;
      score_away: number;
    }>;
    total_events: number;
  };
}
```

---

## 9D. SEASON MOOD TIMELINE

### GET /api/v1/fan/{club}/mood-timeline?season=2024

Returns per-match mood trajectory for a full season (38 data points).

```typescript
{
  success: true;
  data: {
    club: string;
    club_display: string;
    season: string;            // "2024-25"
    total_matches: number;
    points: Array<{
      matchweek: number;
      date: string;
      opponent: string;
      is_home: boolean;
      score: string;           // "Arsenal 2-0 Wolves"
      result: "W" | "D" | "L";
      mood_value: number;      // 0-1
      mood_label: string;      // "euphoric" | "confident" | "steady" | "anxious" | "despairing"
      form: string;            // "WWDLD"
    }>;
  };
}
```

---

## 9E. SHAREABLE PREDICTION CARDS

### GET /api/v1/predict/v2/{home_team}/{away_team}/card

Returns all data needed to render a visual prediction card for social sharing.

```typescript
{
  success: true;
  data: {
    home_team: string;
    away_team: string;
    home_club_id: string;          // For colour palette lookup
    away_club_id: string;
    prediction: string;            // "Arsenal Win" | "Draw"
    probabilities: { home_win: number; draw: number; away_win: number };
    expected_goals: { home: number; away: number };
    most_likely_score: string;     // "1-0"
    ai_take: string;               // One-liner AI quote
    date: string | null;           // Fixture date
    model: string;
  };
}
```

Frontend route: `/card/:home/:away` (standalone, no nav — optimized for sharing)

---

## 9F. USER FAN MEMORIES

### GET /api/v1/fan/memories/{session_id}?club=arsenal

Returns stored personal fan memories for a session.

### POST /api/v1/fan/memories

Store a fan memory manually. Body: `session_id`, `club`, `memory`, `memory_type`.

### DELETE /api/v1/fan/memories/{session_id}

Clear all memories for a session.

**Auto-detection**: Memories are also auto-detected in chat messages ("I was at Istanbul 2005", "my dad took me when I was 12") and stored automatically. Recalled in future conversations via context injection.

---

## 10. SEARCH

### GET /api/v1/search

**Query Params:** `q` (required), `type?` ("all"|"players"|"teams"|"news"), `limit?`

**Response:**
```typescript
{
  query: string;
  results: {
    players?: Player[];
    teams?: Team[];
    news?: NewsArticle[];
  };
  total: number;
}
```

---

## 10. BANTER & DERBIES

### GET /api/v1/banter/{team1}/{team2}

**Response:**
```typescript
{
  team1: string;
  team2: string;
  banter: {
    [team1]_says: string;
    [team2]_says: string;
    neutral: string;
  };
  is_historic_rivalry: boolean;
}
```

### GET /api/v1/derby/{city}

**Cities:** london, manchester, merseyside, tyne-wear

**Response:**
```typescript
{
  city: string;
  derby: {
    name: string;
    teams: string[];
    key_matches: Array<{
      name: string;
      teams: string[];
      intensity: number;
    }>;
    description: string;
  };
  teams: Array<{
    team: Team;
    mood: object;
  }>;
}
```

---

## 11. KNOWLEDGE GRAPH

### GET /api/v1/graph

**Response (vis.js format):**
```typescript
{
  nodes: Array<{
    id: string;
    label: string;
    type: string;            // "team", "legend", "moment"
    color: string;
  }>;
  edges: Array<{
    from: string;
    to: string;
    label: string;           // "legendary_at", "rival_of", etc.
  }>;
  stats: {
    node_count: number;
    edge_count: number;
  };
}
```

---

## 12. ANALYTICS & ADMIN

### GET /api/v1/admin/stats

**Response:**
```typescript
{
  teams: number;
  players: number;
  games: number;
  player_stats: number;
  injuries: number;
  transfers: number;
  standings: number;
  news: number;
  game_events: number;
}
```

### GET /api/v1/metrics

**Response:**
```typescript
{
  analytics: object;
  database: DbStats;
  security: object;
  timestamp: string;
}
```

---

## 13. RATE LIMITING & BUDGET

### GET /api/v1/budget

```typescript
{
  success: true;
  data: {
    daily_cap: number;     // Default $5
    spent_today: number;   // Current spend
    remaining: number;     // Budget left
    currency: "USD";
  };
}
```

**Rate limits** (per IP):
- Chat: 30 requests/minute
- Debate: 5 requests/hour
- Companion simulation: 3 per hour
- Non-AI endpoints: 60/minute

When budget exceeded, AI endpoints return 429 with a friendly message. Non-AI endpoints (trivia, predictions, standings, mood timeline) continue working.

---

## 14. HEALTH

### GET /health

**Response:**
```typescript
{
  status: "healthy";
  timestamp: string;
}
```

---

## Error Responses

All errors follow this format:
```typescript
{
  success: false;
  data: null;
  meta: null;
  error: {
    code: string;            // "HTTP_404", "INTERNAL_ERROR", etc.
    message: string;
  };
}
```

---

## Key Frontend Pages & Required Endpoints

| Page | Primary Endpoints |
|------|-------------------|
| **Chat** | POST /api/v1/chat, GET /api/v1/clubs |
| **Fixtures** | GET /api/v1/live/fixtures, GET /api/v1/live/results |
| **Standings** | GET /api/v1/live/standings |
| **Predictions** | GET /api/v1/predict/v2/{h}/{a}, GET /api/v1/predict/v2/upcoming |
| **Team Profile** | GET /api/v1/teams/{id}/personality, GET /api/v1/fan/{club}/4d-state |
| **Trivia** | GET /api/v1/trivia, POST /api/v1/trivia/check, GET /api/v1/trivia/stats |
| **Debate** | POST /api/v1/debate |
| **Companion** | POST /api/v1/live/companion/simulate, GET /api/v1/live/companion/events |
| **Mood Timeline** | GET /api/v1/fan/{club}/mood-timeline |
| **Prediction Card** | GET /api/v1/predict/v2/{h}/{a}/card (route: /card/:h/:a) |
| **Fan Mood** | GET /api/v1/fan/{club}/mood, GET /api/v1/fan/{club}/full |
| **Fan Memories** | GET/POST/DELETE /api/v1/fan/memories (auto-detected in chat) |
| **Demo** | None (pre-baked data, zero API calls) |
