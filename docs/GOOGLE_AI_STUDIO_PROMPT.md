

# REACT FRONTEND GENERATION REQUEST

## App Overview

**App Name**: Soccer-AI
**Framework**: React 18 + TypeScript + Vite + TailwindCSS
**Description**: An emotionally intelligent Premier League football companion that feels the game with you. NOT a stats bot - a fan companion that supports your club, speaks proper UK football language, knows rivalries, and predicts matches with 62.9% accuracy.

**Core Philosophy**: "Fan at heart. Analyst in nature."

**Key Differentiator**: The AI adopts the persona of YOUR club's supporter. Ask an Arsenal fan about Spurs and watch the rivalry come alive.

---

## Design System

### Visual Identity
- **Primary Colors**: Dark slate (#0f172a) background, emerald (#10b981) accents
- **Club Colors**: Dynamic - switch based on selected team persona
- **Typography**: Inter for UI, system monospace for stats
- **Style**: Professional football broadcast aesthetic, not corporate dashboard
- **Feel**: Match day atmosphere - excitement, tension, passion

### Club Color Palette (for dynamic theming)
```typescript
const CLUB_COLORS: Record<string, { primary: string; secondary: string }> = {
  arsenal: { primary: '#EF0107', secondary: '#063672' },
  chelsea: { primary: '#034694', secondary: '#DBA111' },
  liverpool: { primary: '#C8102E', secondary: '#00B2A9' },
  manchester_united: { primary: '#DA291C', secondary: '#FBE122' },
  manchester_city: { primary: '#6CABDD', secondary: '#1C2C5B' },
  tottenham: { primary: '#132257', secondary: '#FFFFFF' },
  newcastle: { primary: '#241F20', secondary: '#FFFFFF' },
  west_ham: { primary: '#7A263A', secondary: '#1BB1E7' },
  everton: { primary: '#003399', secondary: '#FFFFFF' },
  brighton: { primary: '#0057B8', secondary: '#FFCD00' },
  aston_villa: { primary: '#95BFE5', secondary: '#670E36' },
  wolves: { primary: '#FDB913', secondary: '#231F20' },
  crystal_palace: { primary: '#1B458F', secondary: '#C4122E' },
  fulham: { primary: '#000000', secondary: '#CC0000' },
  nottingham_forest: { primary: '#DD0000', secondary: '#FFFFFF' },
  brentford: { primary: '#E30613', secondary: '#FBB800' },
  bournemouth: { primary: '#DA291C', secondary: '#000000' },
  leicester: { primary: '#003090', secondary: '#FDBE11' },
  ipswich: { primary: '#3A64A3', secondary: '#FFFFFF' },
  southampton: { primary: '#D71920', secondary: '#130C0E' },
  analyst: { primary: '#10b981', secondary: '#0f172a' }
};
```

### Component Styling
- Cards: Rounded corners (xl), subtle shadows, glassmorphism on dark backgrounds
- Buttons: Pill-shaped for actions, squared for navigation
- Form inputs: Dark backgrounds (#1e293b), light text, emerald focus rings
- Tables: Alternating rows, sticky headers, zone highlighting (CL blue, Europa orange, Relegation red)

---

## Data Models (TypeScript Interfaces)

```typescript
// API Response Wrapper - ALL endpoints return this shape
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

// Club for persona selection
interface Club {
  id: string;      // "arsenal", "chelsea", etc.
  name: string;    // "Arsenal", "Chelsea", etc.
}

// Chat
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  club?: string;   // Persona used for this message
}

interface ChatRequest {
  message: string;           // 1-1000 chars
  conversation_id?: string;  // Optional, creates new if omitted
  club?: string;             // Fan persona: "arsenal", "chelsea", etc.
}

interface ChatResponse {
  response: string;
  conversation_id: string;
  sources: Array<{ type: string; id?: number; }>;
  confidence: number;        // 0-1
  usage?: { input_tokens: number; output_tokens: number; };
}

// Team
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

// Game/Fixture
interface Game {
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
interface Standing {
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
  confidence_level: 'low' | 'medium' | 'high';
  key_insight: string;
}

// Persona
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
```

---

## Mock Data (for USE_MOCK_DATA = true)

```typescript
const MOCK_CLUBS: Club[] = [
  { id: 'arsenal', name: 'Arsenal' },
  { id: 'chelsea', name: 'Chelsea' },
  { id: 'liverpool', name: 'Liverpool' },
  { id: 'manchester_united', name: 'Manchester United' },
  { id: 'manchester_city', name: 'Manchester City' },
  { id: 'tottenham', name: 'Tottenham' },
  { id: 'newcastle', name: 'Newcastle United' },
  { id: 'west_ham', name: 'West Ham United' },
  { id: 'everton', name: 'Everton' },
  { id: 'brighton', name: 'Brighton & Hove Albion' },
  { id: 'aston_villa', name: 'Aston Villa' },
  { id: 'wolves', name: 'Wolverhampton Wanderers' },
  { id: 'crystal_palace', name: 'Crystal Palace' },
  { id: 'fulham', name: 'Fulham' },
  { id: 'nottingham_forest', name: 'Nottingham Forest' },
  { id: 'brentford', name: 'Brentford' },
  { id: 'bournemouth', name: 'AFC Bournemouth' },
  { id: 'leicester', name: 'Leicester City' },
  { id: 'ipswich', name: 'Ipswich Town' },
  { id: 'southampton', name: 'Southampton' },
  { id: 'analyst', name: 'Neutral Analyst' }
];

const MOCK_STANDINGS: Standing[] = [
  { position: 1, team_id: 4, team_name: 'Liverpool', short_name: 'LIV', played: 17, won: 14, drawn: 2, lost: 1, goals_for: 45, goals_against: 15, goal_difference: 30, points: 44, form: 'WWDWW' },
  { position: 2, team_id: 5, team_name: 'Chelsea', short_name: 'CHE', played: 17, won: 10, drawn: 4, lost: 3, goals_for: 38, goals_against: 20, goal_difference: 18, points: 34, form: 'DWWLW' },
  { position: 3, team_id: 1, team_name: 'Arsenal', short_name: 'ARS', played: 17, won: 9, drawn: 5, lost: 3, goals_for: 32, goals_against: 18, goal_difference: 14, points: 32, form: 'WDWDW' },
  { position: 4, team_id: 3, team_name: 'Nottingham Forest', short_name: 'NFO', played: 17, won: 9, drawn: 4, lost: 4, goals_for: 25, goals_against: 19, goal_difference: 6, points: 31, form: 'LWWDW' },
  { position: 5, team_id: 6, team_name: 'Manchester City', short_name: 'MCI', played: 17, won: 8, drawn: 4, lost: 5, goals_for: 32, goals_against: 24, goal_difference: 8, points: 28, form: 'LLWDL' },
  // ... more teams
  { position: 18, team_id: 18, team_name: 'Leicester City', short_name: 'LEI', played: 17, won: 4, drawn: 4, lost: 9, goals_for: 22, goals_against: 37, goal_difference: -15, points: 16, form: 'LLLDW' },
  { position: 19, team_id: 19, team_name: 'Ipswich Town', short_name: 'IPS', played: 17, won: 2, drawn: 7, lost: 8, goals_for: 16, goals_against: 31, goal_difference: -15, points: 13, form: 'DLLDD' },
  { position: 20, team_id: 20, team_name: 'Southampton', short_name: 'SOU', played: 17, won: 1, drawn: 3, lost: 13, goals_for: 11, goals_against: 37, goal_difference: -26, points: 6, form: 'LLLLD' }
];

const MOCK_FIXTURES: Game[] = [
  { id: 1, date: '2024-12-21', time: '15:00', status: 'scheduled', home_team_id: 1, home_team_name: 'Arsenal', home_team_short: 'ARS', away_team_id: 5, away_team_name: 'Chelsea', away_team_short: 'CHE', competition: 'Premier League', venue: 'Emirates Stadium' },
  { id: 2, date: '2024-12-21', time: '17:30', status: 'scheduled', home_team_id: 4, home_team_name: 'Liverpool', home_team_short: 'LIV', away_team_id: 6, away_team_name: 'Manchester City', away_team_short: 'MCI', competition: 'Premier League', venue: 'Anfield' },
  { id: 3, date: '2024-12-22', time: '14:00', status: 'scheduled', home_team_id: 2, home_team_name: 'Manchester United', home_team_short: 'MUN', away_team_id: 7, away_team_name: 'Tottenham', away_team_short: 'TOT', competition: 'Premier League', venue: 'Old Trafford' }
];

const MOCK_CHAT_RESPONSES: Record<string, string> = {
  arsenal: "Ah mate, what a time to be a Gooner! Saka's been absolutely brilliant lately. Remember when people doubted Arteta? Look at us now - the process is real! COYG!",
  chelsea: "Blues through and through! The gaffer's got us playing some proper football again. That youth academy is churning out gems - Cobham's finest!",
  liverpool: "You'll Never Walk Alone, mate! The Kop's been bouncing this season. Remember Istanbul? That's the spirit that runs through this club!",
  analyst: "Looking at the tactical setup, the pressing patterns have been particularly effective this season. The expected goals model suggests some regression to the mean is likely."
};
```

---

## API Configuration

```typescript
const API_BASE = 'http://localhost:8000/api/v1';
const USE_MOCK_DATA = true; // Toggle to false when backend is running

// API Client
export const api = {
  // Chat with club persona
  chat: async (message: string, club?: string, conversationId?: string): Promise<ApiResponse<ChatResponse>> => {
    if (USE_MOCK_DATA) {
      return {
        success: true,
        data: {
          response: MOCK_CHAT_RESPONSES[club || 'analyst'] || MOCK_CHAT_RESPONSES.analyst,
          conversation_id: conversationId || crypto.randomUUID(),
          sources: [{ type: 'persona' }],
          confidence: 0.85
        }
      };
    }
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, club, conversation_id: conversationId })
    });
    return res.json();
  },

  // Get all clubs for persona selection
  getClubs: async (): Promise<ApiResponse<Club[]>> => {
    if (USE_MOCK_DATA) {
      return { success: true, data: MOCK_CLUBS };
    }
    const res = await fetch(`${API_BASE}/clubs`);
    return res.json();
  },

  // Get today's fixtures
  getFixturesToday: async (): Promise<ApiResponse<Game[]>> => {
    if (USE_MOCK_DATA) {
      return { success: true, data: MOCK_FIXTURES };
    }
    const res = await fetch(`${API_BASE}/games/today`);
    return res.json();
  },

  // Get upcoming fixtures
  getFixturesUpcoming: async (): Promise<ApiResponse<Game[]>> => {
    if (USE_MOCK_DATA) {
      return { success: true, data: MOCK_FIXTURES };
    }
    const res = await fetch(`${API_BASE}/games/upcoming`);
    return res.json();
  },

  // Get standings
  getStandings: async (league: string = 'premier-league'): Promise<ApiResponse<Standing[]>> => {
    if (USE_MOCK_DATA) {
      return { success: true, data: MOCK_STANDINGS };
    }
    const res = await fetch(`${API_BASE}/standings/${league}`);
    return res.json();
  },

  // Get match prediction
  getPrediction: async (homeTeam: string, awayTeam: string): Promise<ApiResponse<Prediction>> => {
    if (USE_MOCK_DATA) {
      return {
        success: true,
        data: {
          home_team: homeTeam,
          away_team: awayTeam,
          favorite: homeTeam,
          underdog: awayTeam,
          side_a_score: 65,
          side_b_score: 45,
          base_upset_prob: 0.28,
          pattern_multiplier: 1.15,
          final_upset_prob: 0.32,
          patterns_triggered: [
            { name: 'derby_caution', multiplier: 1.15, confidence: 0.8 }
          ],
          confidence_level: 'medium',
          key_insight: 'Historic rivalry adds unpredictability'
        }
      };
    }
    const res = await fetch(`${API_BASE}/predict?home_team=${homeTeam}&away_team=${awayTeam}`, {
      method: 'POST'
    });
    return res.json();
  },

  // Get match preview (combines prediction + fan context)
  getMatchPreview: async (homeTeamId: number, awayTeamId: number): Promise<ApiResponse<any>> => {
    if (USE_MOCK_DATA) {
      return { success: true, data: null };
    }
    const res = await fetch(`${API_BASE}/match/preview/${homeTeamId}/${awayTeamId}`);
    return res.json();
  }
};
```

---

## Page Structure & Requirements

### 1. Chat Page (PRIMARY - Most Important)

**Route**: `/` or `/chat`

**Purpose**: Main interaction - talk to an AI that supports YOUR club

**Components Needed**:
- `ClubSelector` - Dropdown to select club persona (20 clubs + neutral analyst)
- `ChatInput` - Message input with send button
- `ChatHistory` - Scrollable message list with styled bubbles
- `MessageBubble` - Individual message with persona indicator

**Behavior**:
- On club change, show greeting from that persona
- User messages on right (dark bg), AI on left (club-colored accent)
- Show typing indicator while waiting for response
- Display confidence score subtly on AI messages
- Remember conversation_id for context

**Key UX**:
- Club crest/color should be visible in header
- Persona name shown with AI messages (e.g., "Arsenal Fan")
- Mobile-first with fixed input at bottom

### 2. Standings Page

**Route**: `/standings`

**Purpose**: Live Premier League table with form indicators

**Components Needed**:
- `StandingsTable` - Full league table
- `FormBadge` - W/D/L colored badges
- `ZoneIndicator` - Highlights for CL/Europa/Relegation

**Zone Highlighting**:
- Positions 1-4: Champions League (blue left border)
- Positions 5-6: Europa League (orange left border)
- Position 7: Europa Conference (green left border)
- Positions 18-20: Relegation (red left border)

**Form Badge Colors**:
- Win: Green (#22c55e)
- Draw: Amber (#f59e0b)
- Loss: Red (#ef4444)

### 3. Fixtures Page

**Route**: `/fixtures`

**Purpose**: Today's matches and upcoming fixtures

**Components Needed**:
- `FixtureCard` - Individual match card
- `FixtureList` - List of fixtures grouped by date
- `LiveIndicator` - Pulsing dot for live matches

**Display**:
- Show home vs away with crests
- Time and venue
- If finished, show score
- If live, show live indicator and score

### 4. Predictions Page

**Route**: `/predictions`

**Purpose**: Match predictions with Third Knowledge patterns

**Components Needed**:
- `PredictionCard` - Single match prediction
- `PatternBadge` - Shows triggered patterns (derby_caution, close_matchup, etc.)
- `ConfidenceBar` - Visual confidence indicator
- `InsightBox` - Key insight explanation

**Display**:
- Power rating comparison (side_a vs side_b scores)
- Upset probability meter
- Patterns that triggered with descriptions
- AI-generated key insight

---

## Killer Features to Highlight

### 1. Club Persona Chat (Star Feature)
The AI becomes a supporter of YOUR club. Ask about rivals and watch the banter. This is NOT a neutral stats bot - it has opinions, memories, and passion.

**Sample Interaction**:
> User (Arsenal mode): "What do you think of Tottenham?"
> AI: "Ah, the lot from down the lane? *chuckles* Look, we've got 13 league titles. They've got... what exactly? That one year they put the pressure on? North London is RED, always has been."

### 2. Third Knowledge Predictions
62.9% accuracy using 6 interaction patterns:
- `close_matchup` - Power diff < 10
- `midtable_clash` - Both teams positions 8-15
- `defensive_matchup` - Both teams defensive
- `parked_bus_risk` - Big favorite vs defensive underdog
- `derby_caution` - Historic rivalry
- `top_vs_top` - Top 6 clash

### 3. Dynamic Club Theming
UI colors change based on selected club. Arsenal red, Chelsea blue, Liverpool red - the whole app adapts to your colors.

---

## UK Football Language Rules

**ALWAYS use**:
- "match" not "game"
- "nil" not "zero" (e.g., "won 2-nil")
- "pitch" not "field"
- "kit" not "uniform"
- "gaffer" or "manager" not "coach"
- "fixture" not "matchup"
- "league table" not "standings" (in UI copy)
- "football" not "soccer"

**In UI Copy Examples**:
- "Today's Fixtures" not "Today's Games"
- "League Table" not "Standings"
- "Match Predictions" not "Game Predictions"
- "Clean sheet" not "Shutout"

---

## File Structure to Generate

```
frontend/
├── src/
│   ├── App.tsx                 # Main app with routing
│   ├── main.tsx                # Entry point
│   ├── index.css               # Tailwind imports
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx      # Nav with club selector
│   │   │   ├── Footer.tsx
│   │   │   └── Layout.tsx      # Main layout wrapper
│   │   │
│   │   ├── chat/
│   │   │   ├── ChatPage.tsx    # Main chat page
│   │   │   ├── ChatInput.tsx   # Message input
│   │   │   ├── ChatHistory.tsx # Message list
│   │   │   ├── MessageBubble.tsx
│   │   │   └── ClubSelector.tsx
│   │   │
│   │   ├── standings/
│   │   │   ├── StandingsPage.tsx
│   │   │   ├── StandingsTable.tsx
│   │   │   ├── FormBadge.tsx
│   │   │   └── ZoneIndicator.tsx
│   │   │
│   │   ├── fixtures/
│   │   │   ├── FixturesPage.tsx
│   │   │   ├── FixtureCard.tsx
│   │   │   └── LiveIndicator.tsx
│   │   │
│   │   └── predictions/
│   │       ├── PredictionsPage.tsx
│   │       ├── PredictionCard.tsx
│   │       ├── PatternBadge.tsx
│   │       └── ConfidenceBar.tsx
│   │
│   ├── services/
│   │   └── api.ts              # API client with mock toggle
│   │
│   ├── hooks/
│   │   ├── useClub.ts          # Club selection context
│   │   └── useChat.ts          # Chat state management
│   │
│   ├── types/
│   │   └── index.ts            # All TypeScript interfaces
│   │
│   └── constants/
│       ├── clubs.ts            # Club colors and data
│       └── mock-data.ts        # Mock data for development
│
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── index.html
```

---

## Generation Instructions

1. Generate ALL files listed in the file structure
2. Use React Router v6 for navigation
3. Use TailwindCSS for all styling (dark theme)
4. Include the USE_MOCK_DATA toggle in api.ts
5. Make the club selector persistent (localStorage)
6. Implement proper TypeScript types throughout
7. Add loading states and error handling
8. Make it mobile-responsive
9. Include subtle animations (Tailwind transitions)
10. Use UK football terminology in all UI copy

**Priority Order**:
1. Chat page (most important)
2. Standings page
3. Fixtures page
4. Predictions page

Generate a complete, working React application that showcases the Soccer-AI vision: "Fan at heart. Analyst in nature."
