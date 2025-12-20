# Soccer-AI API Design

**Version**: 1.0 (MVP)
**Framework**: FastAPI (Python)
**Base URL**: `/api/v1`

---

## Core Endpoints

### Chat (Primary Interface)

```
POST /api/v1/chat
```

The main endpoint. User asks natural language question, gets AI response.

**Request:**
```json
{
  "message": "How did Manchester United play yesterday?",
  "conversation_id": "optional-uuid-for-context"
}
```

**Response:**
```json
{
  "response": "Manchester United drew 1-1 against Everton yesterday at Old Trafford. Bruno Fernandes scored from the penalty spot in the 67th minute, but Everton equalized through Calvert-Lewin in the 82nd minute. United had 62% possession but struggled to break down Everton's defensive block.",
  "conversation_id": "uuid",
  "sources": [
    {"type": "game", "id": 123},
    {"type": "player_stats", "ids": [456, 789]}
  ],
  "confidence": 0.95
}
```

**Flow:**
1. Parse user message
2. FTS5 search across tables (RAG retrieval)
3. Build context from relevant rows
4. Send to Haiku API with context
5. Return natural language response

---

### Players

```
GET /api/v1/players
GET /api/v1/players/{id}
GET /api/v1/players/{id}/stats
GET /api/v1/players/search?q={query}
```

**List Players:**
```
GET /api/v1/players?team_id=1&position=Forward&limit=20&offset=0
```

**Player Detail:**
```json
{
  "id": 1,
  "name": "Erling Haaland",
  "team": {"id": 1, "name": "Manchester City"},
  "position": "Forward",
  "nationality": "Norway",
  "jersey_number": 9,
  "stats_summary": {
    "games": 18,
    "goals": 15,
    "assists": 4,
    "rating_avg": 7.8
  },
  "current_injury": null,
  "recent_form": ["G", "G", "A", "-", "G"]
}
```

**Player Stats (Season):**
```
GET /api/v1/players/1/stats?season=2024-25
```

---

### Teams

```
GET /api/v1/teams
GET /api/v1/teams/{id}
GET /api/v1/teams/{id}/squad
GET /api/v1/teams/{id}/fixtures
GET /api/v1/teams/{id}/results
```

**Team Detail:**
```json
{
  "id": 1,
  "name": "Manchester City",
  "short_name": "MAN CITY",
  "league": "Premier League",
  "country": "England",
  "stadium": "Etihad Stadium",
  "standing": {
    "position": 2,
    "points": 35,
    "form": "WWDWW"
  },
  "next_game": {
    "opponent": "Liverpool",
    "date": "2024-12-22",
    "venue": "home"
  }
}
```

---

### Games

```
GET /api/v1/games
GET /api/v1/games/{id}
GET /api/v1/games/live
GET /api/v1/games/today
GET /api/v1/games/upcoming
```

**Game Detail:**
```json
{
  "id": 123,
  "date": "2024-12-18",
  "time": "20:00",
  "status": "finished",
  "home_team": {"id": 1, "name": "Manchester United", "score": 1},
  "away_team": {"id": 2, "name": "Everton", "score": 1},
  "venue": "Old Trafford",
  "attendance": 73500,
  "events": [
    {"minute": 67, "type": "goal", "player": "Bruno Fernandes", "team": "home"},
    {"minute": 82, "type": "goal", "player": "Calvert-Lewin", "team": "away"}
  ],
  "stats": {
    "possession": {"home": 62, "away": 38},
    "shots": {"home": 15, "away": 8}
  }
}
```

---

### Injuries

```
GET /api/v1/injuries
GET /api/v1/injuries/active
GET /api/v1/injuries/team/{team_id}
```

**Active Injuries:**
```json
{
  "injuries": [
    {
      "player": {"id": 5, "name": "Bukayo Saka"},
      "team": {"id": 3, "name": "Arsenal"},
      "injury_type": "Hamstring",
      "severity": "Moderate",
      "expected_return": "2024-12-28",
      "games_missed": 3
    }
  ],
  "total": 45
}
```

---

### Transfers

```
GET /api/v1/transfers
GET /api/v1/transfers/recent
GET /api/v1/transfers/rumors
GET /api/v1/transfers/team/{team_id}
```

**Recent Transfers:**
```json
{
  "transfers": [
    {
      "player": {"id": 10, "name": "Example Player"},
      "from_team": {"id": 5, "name": "Chelsea"},
      "to_team": {"id": 8, "name": "AC Milan"},
      "type": "loan",
      "fee": null,
      "date": "2024-12-15",
      "status": "completed"
    }
  ]
}
```

---

### Standings

```
GET /api/v1/standings/{league}
GET /api/v1/standings/{league}/form
```

**League Standings:**
```json
{
  "league": "Premier League",
  "season": "2024-25",
  "standings": [
    {
      "position": 1,
      "team": {"id": 4, "name": "Liverpool"},
      "played": 17,
      "won": 12,
      "drawn": 4,
      "lost": 1,
      "gf": 38,
      "ga": 15,
      "gd": 23,
      "points": 40,
      "form": "WWWDW"
    }
  ]
}
```

---

### Search (Unified)

```
GET /api/v1/search?q={query}&type={players|teams|games|all}
```

Uses FTS5 across all tables.

**Response:**
```json
{
  "query": "Haaland",
  "results": {
    "players": [{"id": 1, "name": "Erling Haaland", "team": "Manchester City"}],
    "teams": [],
    "games": [],
    "news": [{"id": 50, "title": "Haaland scores hat-trick..."}]
  },
  "total": 5
}
```

---

### News

```
GET /api/v1/news
GET /api/v1/news/{id}
GET /api/v1/news/team/{team_id}
GET /api/v1/news/player/{player_id}
```

---

## Internal Endpoints (Admin/Automation)

```
POST /api/v1/admin/update/games      # Trigger game updates
POST /api/v1/admin/update/injuries   # Trigger injury updates
POST /api/v1/admin/update/transfers  # Trigger transfer updates
GET  /api/v1/admin/stats             # Database statistics
GET  /api/v1/health                  # Health check
```

---

## Response Format

All responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "timestamp": "2024-12-18T20:00:00Z"
  },
  "error": null
}
```

Error response:
```json
{
  "success": false,
  "data": null,
  "meta": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Player with ID 999 not found"
  }
}
```

---

## Rate Limiting

- Chat endpoint: 30 requests/minute (AI cost protection)
- Read endpoints: 100 requests/minute
- Admin endpoints: 10 requests/minute

---

## Authentication (Future)

MVP: No auth (public read-only)
V2: API key for chat endpoint
V3: User accounts + usage tracking

---

## Query Parameters (Standard)

| Parameter | Type | Description |
|-----------|------|-------------|
| limit | int | Results per page (default: 20, max: 100) |
| offset | int | Skip N results (pagination) |
| sort | string | Sort field (e.g., "date", "name") |
| order | string | "asc" or "desc" |

---

## Example Chat Queries → RAG Flow

**User**: "Who scored for Arsenal yesterday?"

**RAG Flow**:
1. Extract entities: "Arsenal", "yesterday", "scored"
2. FTS5 query: `SELECT * FROM games WHERE date = '2024-12-17' AND (home_team_id = 3 OR away_team_id = 3)`
3. Get game events: `SELECT * FROM game_events WHERE game_id = ? AND event_type = 'goal'`
4. Build context: "Arsenal played Everton. Goals: Saka (23'), Martinelli (67')"
5. Send to Haiku: "Based on this context, answer: Who scored for Arsenal yesterday?"
6. Return natural response

---

## File Structure (Backend)

```
backend/
├── main.py              # FastAPI app + routes
├── database.py          # SQLite connection + queries
├── models.py            # Pydantic models (request/response)
├── rag.py               # RAG retrieval logic
├── ai_response.py       # Haiku API integration
├── routers/
│   ├── chat.py          # /chat endpoint
│   ├── players.py       # /players endpoints
│   ├── teams.py         # /teams endpoints
│   ├── games.py         # /games endpoints
│   └── admin.py         # /admin endpoints
└── soccer_ai.db         # SQLite database
```
