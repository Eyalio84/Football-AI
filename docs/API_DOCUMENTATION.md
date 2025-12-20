# Soccer-AI API Documentation

**Base URL**: `http://localhost:8000`
**API Version**: v1
**Prefix**: `/api/v1`

---

## Chat Endpoints

### POST /api/v1/chat

Send a message and receive an AI response with club persona.

**Request Body**:
```json
{
  "message": "How did we play last weekend?",
  "club": "arsenal",
  "conversation_id": "optional-uuid"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| message | string | Yes | User's message |
| club | string | No | Club ID (e.g., "arsenal", "manchester_united") |
| conversation_id | string | No | UUID for conversation continuity |

**Response**:
```json
{
  "response": "We had a cracking match, mate! Proper Arsenal performance...",
  "conversation_id": "uuid-here",
  "club": "arsenal"
}
```

### POST /api/v1/chat/stream

Streaming chat endpoint using Server-Sent Events.

**Request Body**: Same as `/api/v1/chat`

**Response**: SSE stream with JSON events:
```
data: {"text": "We had a "}
data: {"text": "cracking match"}
data: {"done": true, "conversation_id": "uuid"}
```

---

## 4D Persona Endpoints

### GET /api/v1/fan/{club}/4d-state

Get the computed 4D persona state for a club.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| club | string | Club ID (e.g., "liverpool") |

**Response**:
```json
{
  "enabled": true,
  "position_4d": {
    "x": {
      "mood": "confident",
      "intensity": 0.6,
      "reason": "Recent form: WWDLW (3 wins, 1 draw, 1 loss)"
    },
    "y": {
      "activated": false,
      "target": null,
      "relation_type": null,
      "intensity": 0
    },
    "z": {
      "dialect": "scouse",
      "distinctiveness": 0.8,
      "region": "north"
    },
    "t": {
      "step": 0,
      "momentum": "stable"
    }
  },
  "form_string": "WWDLW"
}
```

**Dimension Details**:

| Dimension | Field | Type | Description |
|-----------|-------|------|-------------|
| x (Emotional) | mood | string | euphoric, confident, neutral, nervous, frustrated |
| x | intensity | float | 0.0 - 1.0 |
| x | reason | string | Explanation of mood source |
| y (Relational) | activated | bool | Whether rivalry is active |
| y | target | string | Rival club name |
| y | relation_type | string | "rival", "ally" |
| y | intensity | float | Rivalry intensity 0-1 |
| z (Linguistic) | dialect | string | scouse, mancunian, cockney, etc. |
| z | region | string | north, midlands, london, south |
| t (Temporal) | step | int | Conversation turn number |
| t | momentum | string | rising, stable, falling |

### GET /api/v1/fan/{club}/mood

Get mood information (legacy endpoint, still works).

**Response**:
```json
{
  "mood": {
    "mood": "confident",
    "form_string": "WWDLW",
    "reason": "3 wins, 1 draw, 1 loss in last 5"
  }
}
```

### POST /api/v1/fan/{club}/check-rivalry

Check if a message contains a rivalry mention.

**Request Body**:
```json
{
  "message": "What do you think of Liverpool?"
}
```

**Response**:
```json
{
  "rivalry_detected": true,
  "rivalry": {
    "target": "Liverpool",
    "type": "rival",
    "intensity": 0.98,
    "derby_name": "North West Derby",
    "banter": ["One of the biggest rivalries in football..."]
  }
}
```

---

## Data Endpoints

### GET /api/v1/teams

Get all Premier League teams.

**Response**:
```json
{
  "teams": [
    {
      "id": "arsenal",
      "name": "Arsenal",
      "short_name": "ARS",
      "stadium": "Emirates Stadium"
    },
    ...
  ]
}
```

### GET /api/v1/standings

Get current Premier League standings.

**Response**:
```json
{
  "standings": [
    {
      "position": 1,
      "team": "Liverpool",
      "played": 20,
      "won": 15,
      "drawn": 3,
      "lost": 2,
      "gf": 48,
      "ga": 18,
      "gd": 30,
      "points": 48,
      "form": "WWWDW"
    },
    ...
  ]
}
```

### GET /api/v1/fixtures

Get upcoming fixtures.

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| team | string | null | Filter by team ID |
| limit | int | 10 | Number of fixtures to return |

**Response**:
```json
{
  "fixtures": [
    {
      "home_team": "Arsenal",
      "away_team": "Liverpool",
      "date": "2025-01-05",
      "time": "16:30",
      "competition": "Premier League"
    },
    ...
  ]
}
```

### GET /api/v1/fixtures/today

Get today's fixtures.

---

## Predictions Endpoints

### GET /api/v1/predictions/match/{home_team}/{away_team}

Get match prediction.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| home_team | string | Home team ID |
| away_team | string | Away team ID |

**Response**:
```json
{
  "home_team": "Arsenal",
  "away_team": "Chelsea",
  "prediction": "home_win",
  "confidence": 0.62,
  "probabilities": {
    "home_win": 0.45,
    "draw": 0.28,
    "away_win": 0.27
  },
  "power_ratings": {
    "home": 82.5,
    "away": 78.3
  },
  "draw_patterns": ["close_matchup"]
}
```

### GET /api/v1/predictions/weekend

Get predictions for all weekend fixtures.

---

## Trivia Endpoints

### GET /api/v1/trivia

Get a trivia question.

**Query Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| team_id | int | Team ID for team-specific questions |

**Response**:
```json
{
  "data": {
    "question": "Who scored Arsenal's first goal at the Emirates Stadium?",
    "correct_answer": "Thierry Henry",
    "wrong_answers": ["Dennis Bergkamp", "Robin van Persie", "Cesc Fabregas"],
    "explanation": "Henry scored a penalty in the first match at Emirates..."
  }
}
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": "Error message here",
  "detail": "Additional details if available"
}
```

**HTTP Status Codes**:
| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Club IDs

Valid club IDs for API requests:

| ID | Club Name |
|----|-----------|
| arsenal | Arsenal |
| aston_villa | Aston Villa |
| bournemouth | AFC Bournemouth |
| brentford | Brentford |
| brighton | Brighton & Hove Albion |
| chelsea | Chelsea |
| crystal_palace | Crystal Palace |
| everton | Everton |
| fulham | Fulham |
| leicester | Leicester City |
| liverpool | Liverpool |
| manchester_city | Manchester City |
| manchester_united | Manchester United |
| newcastle | Newcastle United |
| nottingham_forest | Nottingham Forest |
| southampton | Southampton |
| tottenham | Tottenham Hotspur |
| west_ham | West Ham United |
| wolves | Wolverhampton Wanderers |

---

## CORS

The API allows requests from:
- `http://localhost:5173` (React dev)
- `http://localhost:5000` (Flask frontend)
- `http://localhost:8000` (API docs)

---

## Rate Limiting

No rate limiting is currently enforced, but the API uses session-based security to prevent abuse.

---

## API Documentation UI

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
