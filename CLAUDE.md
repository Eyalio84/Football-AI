# Soccer-AI - CLAUDE.md

**Last Updated**: April 10, 2026

## CRITICAL: Read This First

**Soccer-AI has TWO frontend directories. Only ONE should be used:**

| Directory | What It Is | Status |
|-----------|------------|--------|
| `frontend/` | React 19 + Vite 7 + TypeScript + Tailwind | PRIMARY |
| `flask-frontend/` | Simple Flask static server | TESTING ONLY - Ignore |

**The backend is FastAPI** (`backend/main.py`), NOT Flask. The `flask-frontend/` is just a lightweight testing tool that proxies to FastAPI.

---

## Project Vision

Soccer-AI is an **emotionally intelligent football companion** - not a stats bot.

**Core Philosophy** (from ARIEL_FULL_STORY.md):
> "What if the AI wasn't neutral? What if it was a fan?"

The AI should:
- FEEL the weight of rivalries
- Know you don't casually mention "that Agüero goal" to a Man United supporter
- Understand pre-match hope vs post-loss grief
- Use UK English: "match" not "game", "nil" not "zero", "pitch" not "field"

**Identity**: "Fan at heart. Analyst in nature."

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                           │
│  React Frontend (frontend/)                                 │
│  - Chat with club personas (20 clubs)                       │
│  - Games/fixtures display (live from football-data.org)     │
│  - Standings with form indicators                           │
│  - Predictor + Trivia integration                           │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (port 8000)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER                              │
│  FastAPI Backend (backend/main.py, 2385 lines)              │
│  - 91 endpoints, CORS configured, rate limiting + budget cap│
│  - Auto-refresh: standings/fixtures every 6 hours           │
│  - Club alias resolution (man_utd, spurs, city, etc.)       │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ INTELLIGENCE    │ │ KNOWLEDGE GRAPH │ │ PREDICTOR       │
│ ai_response.py  │ │ unified KG DB   │ │ backend/        │
│ rag.py          │ │ 773 nodes       │ │ predictor/      │
│ Fan Personas    │ │ 717 edges       │ │ Dixon-Coles v2  │
│ Haiku 4.5 API  │ │ 681 facts       │ │ 53.9% accuracy  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Directory Structure

```
soccer-AI/
├── CLAUDE.md                    # THIS FILE - Project instructions
├── README.md                    # Quick start guide
├── schema.sql                   # Database schema (14KB)
├── api_design.md                # API specification
│
├── backend/                     # FastAPI Backend
│   ├── main.py                  # FastAPI app (3368 lines, 91 endpoints)
│   ├── database.py              # SQLite + FTS5 + KG (2001 lines)
│   ├── rag.py                   # Hybrid RAG (1343 lines)
│   ├── ai_response.py           # Haiku 4.5 + personas (1272 lines)
│   ├── fan_enhancements.py      # Mood, rivalry, dialect (792 lines)
│   ├── models.py                # Pydantic models
│   ├── config.py                # 4D Persona config & feature flag
│   ├── persona_bridge.py        # 4D Persona integration layer
│   ├── live_football_provider.py # Live data -> 4D state
│   ├── security_session.py      # Session-based security
│   ├── conversation_intelligence.py # Conversation enrichment
│   ├── soccer_ai.db             # Main database
│   ├── unified_soccer_ai_kg.db  # Unified Knowledge Graph (41.8 MB)
│   ├── requirements.txt         # Python dependencies
│   ├── conftest.py              # Pytest fixtures
│   ├── pytest.ini               # Pytest configuration
│   ├── predictor/               # Match prediction module
│   │   ├── prediction_engine.py # Main prediction engine
│   │   ├── tri_lens_predictor.py # Tri-Lens fusion (55% Poisson + 45% Oracle)
│   │   ├── hybrid_oracle.py     # ELO + Pattern hybrid
│   │   ├── team_ratings.py      # ELO-style power ratings
│   │   ├── draw_detector.py     # 6 Third Knowledge patterns
│   │   ├── backtest_ratings.py  # Validation framework
│   │   └── tune_draw_threshold.py
│   ├── scripts/                 # Data management scripts
│   │   ├── refresh_season_data.py  # Live data refresh (auto-scheduled)
│   │   ├── generate_trivia.py      # Auto-generate trivia from match DB
│   │   └── enrich_iconic_matches.py # KG enrichment script
│   ├── rate_limiter.py          # Per-IP rate limits + daily budget cap
│   ├── live_companion.py        # Match day poller + fan reactions
│   ├── Dockerfile               # Docker config for Fly.io
│   ├── fly.toml                 # Fly.io deployment config
│   ├── .env.example             # Environment variable template
│   ├── kg/                      # Knowledge graph modules
│   ├── tests/                   # Test suite (102 tests)
│   │   ├── test_4d_behavioral.py   # 35 behavioral tests
│   │   ├── test_4d_integration.py  # 33 integration tests
│   │   └── test_kg_migration.py    # 34 KG migration tests
│   └── test_*.py                # Legacy individual test files
│
├── frontend/                    # React Frontend (Matchday Programme theme)
│   ├── src/
│   │   ├── App.tsx              # Main app
│   │   ├── pages/               # 12 pages
│   │   │   ├── Dashboard.tsx    # Games/fixtures
│   │   │   ├── Standings.tsx    # League table with zone drama
│   │   │   ├── Teams.tsx        # Club grid
│   │   │   ├── Chat.tsx         # Fan chat with club theming
│   │   │   ├── Predictions.tsx  # All fixtures with Dixon-Coles predictions
│   │   │   ├── Trivia.tsx       # 136-question trivia game
│   │   │   ├── Debate.tsx       # Two-persona debate mode
│   │   │   ├── Companion.tsx    # Match Day Live Companion
│   │   │   ├── MoodTimeline.tsx # Season Mood Timeline (pure SVG)
│   │   │   ├── PredictionCard.tsx # Shareable prediction cards
│   │   │   ├── Demo.tsx         # Portfolio guided tour (9 scenes)
│   │   │   └── TeamDetail.tsx   # Individual team view
│   │   ├── config/
│   │   │   ├── clubThemes.ts    # 20 club colour palettes
│   │   │   ├── ClubThemeProvider.tsx # Global club theme context
│   │   │   └── theme.ts        # Base theme + typography
│   │   ├── components/          # 28 UI components
│   │   ├── hooks/               # 4 custom React hooks
│   │   └── services/api.ts      # API client (458 lines, 30+ methods)
│   ├── package.json             # Dependencies (React 19, Vite 7, Tailwind)
│   └── vite.config.ts           # Vite config
│
├── flask-frontend/              # TESTING ONLY - Ignore
├── robert/                      # Ariel framework data
│
├── docs/                        # Documentation
│   ├── ARIEL_FULL_STORY.md      # The vision document
│   ├── SOCCER_AI_SYSTEM_ATLAS.md # Architecture diagrams
│   ├── API_DOCUMENTATION.md     # API docs
│   ├── architecture/            # 4D Persona Architecture spec
│   └── *.ctx                    # Context files
│
└── scripts/                     # Utility scripts
    └── seed_data.py             # Database seeding
```

---

## Quick Start

### 1. Start Backend

```bash
cd soccer-AI/backend

# Install dependencies
pip install -r requirements.txt
# Or manually: pip install fastapi uvicorn anthropic aiohttp python-dotenv httpx

# Set API keys in .env
ANTHROPIC_API_KEY=your-key-here
FOOTBALL_DATA_API_KEY=your-key-here

# Run server (auto-refreshes data every 6 hours)
uvicorn main:app --reload --port 8000
```

Backend: `http://localhost:8000` | API docs: `http://localhost:8000/docs`

### 2. Start Frontend

```bash
cd soccer-AI/frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

---

## API Endpoints (Key)

### Chat
```
POST /api/v1/chat
{
  "message": "How did Arsenal play?",
  "club": "arsenal"  // Activates fan persona. Aliases work: "man_utd", "spurs", "city"
}
```

### Fan Persona
```
GET /api/v1/fan/{club}/mood           # Current mood (computed from results)
GET /api/v1/fan/{club}/full           # Full enhancements (mood + rivalry + dialect)
GET /api/v1/fan/{club}/4d-state       # Full 4D position
POST /api/v1/fan/{club}/check-rivalry # Rivalry detection
```

### Live Data (from football-data.org)
```
GET /api/v1/live/standings    # Live PL table
GET /api/v1/live/fixtures     # Upcoming matches
GET /api/v1/live/results      # Recent results
```

### Predictions
```
POST /api/v1/predict          # Manual prediction
GET /api/v1/match/preview/{home_id}/{away_id}  # Full match preview
```

### Trivia (136 questions, 6 categories)
```
GET /api/v1/trivia                    # Random question
GET /api/v1/trivia?category=records   # By category
POST /api/v1/trivia/check?question_id=1&answer=...  # Check answer
GET /api/v1/trivia/stats              # Category/difficulty breakdown
```

### Fan Debate (two personas arguing)
```
POST /api/v1/debate
{
  "club_a": "arsenal",
  "club_b": "tottenham",
  "topic": "Who is the bigger club?",
  "rounds": 3  // 1-5 exchanges per side
}
```

### Live Match Companion (simulated + real)
```
GET  /api/v1/live/companion/matches                        # Available simulations
POST /api/v1/live/companion/simulate/{match}/{club}        # Start sim, returns session_id
GET  /api/v1/live/companion/events/{session_id}?after=N    # Poll for new events
```

### Season Mood Timeline
```
GET /api/v1/fan/{club}/mood-timeline?season=2024  # 38-match mood trajectory
```

### Shareable Prediction Cards
```
GET /api/v1/predict/v2/{home}/{away}/card  # Card data + AI take one-liner
```

### User Fan Memories
```
GET    /api/v1/fan/memories/{session_id}   # Recall stored memories
POST   /api/v1/fan/memories                # Store a memory
DELETE /api/v1/fan/memories/{session_id}   # Clear memories
```
Memories are also auto-detected in chat ("I was at Istanbul 2005", "my dad took me") and recalled naturally in future conversations.

### Frontend Routes
```
/demo            # Portfolio guided tour (no API needed)
/companion       # Match Day Live Companion
/mood-timeline   # Season emotional arc
/debate          # Fan debate
/trivia          # Trivia game
/card/:home/:away  # Shareable prediction card (standalone, no nav)
```

See `docs/API_CONTRACTS.md` for full specification.

---

## The Predictor Module

**Location**: `backend/predictor/`

### V2: Dixon-Coles + Bookmaker Ensemble (Current)

**Architecture**: 40% Dixon-Coles (attack/defense + rho correlation) + 60% Bookmaker odds (vig-removed implied probabilities)

| Metric | V1 (Tri-Lens) | V2 (DC+BK) |
|--------|--------------|------------|
| Overall Accuracy | 53.2% | **53.9%** |
| Draw Precision | 17.3% | **50.0%** |
| Brier Score | 0.580 | 0.584 |

**Key files**:
| File | Purpose |
|------|---------|
| `predictor/dixon_coles.py` | Dixon-Coles model + bookmaker odds + backtest |
| `predictor/tri_lens_predictor.py` | V1 Tri-Lens (still available) |
| `predictor/prediction_engine.py` | Legacy prediction engine |

**V2 API Endpoints**:
```
GET /api/v1/predict/v2/{home}/{away}   # Single match (DC + bookmaker ensemble)
GET /api/v1/predict/v2/upcoming        # All upcoming fixtures
GET /api/v1/predict/v2/backtest        # Accuracy metrics
```

### V1: Tri-Lens (Legacy, still available)

55% Poisson + 45% Oracle + Upset Detection. 6 Third Knowledge patterns.

---

## Fan Personas (20 Clubs)

Each Premier League club has a unique persona with:
- **Emotional state**: Computed from actual match results (anti-gaslighting)
- **Legends**: Club icons to reference
- **Moments**: 78 iconic matches/moments in KG
- **Rivalries**: 43 rivalry edges with intensity weights (0.6-1.0)
- **Dialect**: Regional voice (Scouse, Geordie, Mancunian, Cockney, Midlands)

**Rivalry intensity scales prompt behavior**:
- 0.9+ (blood rivalry): Contempt and tribal pride, no neutral analysis
- 0.7+ (serious): Clear disdain, backhanded compliments only
- Below 0.7: Cheeky banter with some balance

**Club aliases accepted**: `man_united`/`man_utd`/`united`, `man_city`/`city`, `spurs`, `villa`, `palace`, `forest`, `hammers`, `toon`

**Predictor Explainability**: When users ask about upcoming matches, the fan persona weaves Dixon-Coles prediction data (probabilities, xG, most likely score) naturally into their response — *"My gut says Arsenal, numbers back us — 1.75 xG"* — not as a data dump.

**User Fan Memory**: Users can share personal football memories (*"I was at Istanbul 2005"*). These are auto-detected, stored, and recalled in future conversations: *"You were there! Your dad took you when you were 12."*

**Kinetic Theming**: The UI shifts behaviour based on mood — euphoric gets vibrant glow pulse, despairing gets muted colours + rain grain overlay, anxious gets flicker animation.

---

## 4D Persona Architecture

**Location**: `backend/config.py`, `backend/persona_bridge.py`, `backend/live_football_provider.py`

### The 4D Position: P(t) = (x, y, z, t)

| Dimension | Name | What It Controls | Example |
|-----------|------|------------------|---------|
| **X** | Emotional | Mood computed from match results | Win 3-0 -> euphoric |
| **Y** | Relational | Rivalry activation from KG edges | Mention Everton to Liverpool -> rivalry mode |
| **Z** | Linguistic | Regional dialect groupings | Liverpool -> Scouse, Arsenal -> Cockney |
| **T** | Temporal | Conversation trajectory & momentum | Rising/falling/stable |

### Dialect Regions

| Region | Clubs | Dialect |
|--------|-------|---------|
| North | Liverpool, Everton | Scouse |
| North | Man United, Man City | Mancunian |
| North | Newcastle, Leeds, Sunderland | Geordie |
| Midlands | Aston Villa, Wolves | Midlands |
| London | Arsenal, Chelsea, Spurs, West Ham, Crystal Palace, Brentford, Fulham | Cockney |
| South | Brighton, Bournemouth, Southampton | Neutral |

### Feature Flag

```python
# backend/config.py
USE_4D_PERSONA = True   # Use 4D architecture
USE_4D_PERSONA = False  # Fallback to legacy fan_enhancements
```

---

## Unified Knowledge Graph

**Database**: `backend/unified_soccer_ai_kg.db` (41.8 MB)

| Table | Count | Purpose |
|-------|-------|---------|
| nodes | 773 | Teams, legends, stadiums, persons, matches |
| edges | 717 | Rivalries (43), iconic matches (43), legends, moments |
| match_history | 230,557 | Historical matches (2000-2025) for mood + trivia |
| elo_history | 26,410 | Match predictions |
| kb_facts | 681 | Knowledge base |

**Node Types**: persons (362), api_endpoints (64), matches (54), seasons (34), clubs (25), moments (24), stadiums (21), teams (20), legends (18)

**Edge Types**:
- `rival_of`: Team <-> Team (43 edges with intensity weights)
- `iconic_match_for`: Match -> Team (43 edges)
- `legendary_at`: Legend -> Team
- `occurred_at`: Moment -> Team

---

## Automatic Data Refresh

The backend automatically refreshes live data on startup and every 6 hours:
- **Standings**: 20 PL teams with W/D/L, points, position
- **Fixtures**: Upcoming 14 days of matches
- **Results**: Recent 14 days of results
- **Moods**: Recomputed from standings when form strings unavailable

**Data source**: football-data.org (free tier, 10 req/min)
**Script**: `backend/scripts/refresh_season_data.py`

---

## Testing

**Total: 102 tests passing**

```bash
cd backend

# Run ALL tests
python -m pytest tests/ -v

# By suite
python -m pytest tests/test_4d_behavioral.py -v   # 35 behavioral tests
python -m pytest tests/test_4d_integration.py -v   # 33 integration tests
python -m pytest tests/test_kg_migration.py -v     # 34 KG migration tests
```

| Suite | Tests | Coverage |
|-------|-------|----------|
| Behavioral | 35 | Identity, mood grounding, team switching, rivalry, anti-gaslighting |
| Integration | 33 | Config, providers, PersonaBridge, system prompt |
| KG Migration | 34 | Schema, nodes, edges, FTS, traversal, idempotency |

---

## Environment Variables

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
FOOTBALL_DATA_API_KEY=your-key-here
```

---

## Cost Model & Rate Limiting

- Haiku 4.5 API: ~$0.002 per chat, ~$0.012 per debate, ~$0.018 per companion sim
- **Daily budget cap**: $5/day (configurable via `DAILY_BUDGET_CAP` env var)
- **Per-IP rate limits**: chat 30/min, debate 5/hr, companion 3/hr
- When budget exceeded: AI endpoints return friendly fallback, non-AI features keep working
- Budget status: `GET /api/v1/budget`

## Deployment

- **Frontend**: Vercel (React SPA, `vite build`)
- **Backend**: Fly.io (Docker, `fly.toml` + `Dockerfile` in `backend/`)
- **GitHub**: https://github.com/Eyalio84/Football-AI
- **Portfolio**: https://www.verbalogix.com
- **CORS**: Pre-configured for verbalogix.com, football-ai.vercel.app, + env var `CORS_ORIGINS`
- **Security**: All API keys in `.env` (gitignored), `.env.example` provided

---

## The Vision (Remember This)

From ARIEL_FULL_STORY.md:

> "That lad on the tip of his toes, split second before Beckham's freekick.
> That's the feeling. That's always the feeling."

This is NOT a stats bot. This is a fan companion that:
- Celebrates victories with you
- Mourns losses with you
- Knows your rivals and hates them too
- Speaks authentic football language

**Fan at heart. Analyst in nature.**
