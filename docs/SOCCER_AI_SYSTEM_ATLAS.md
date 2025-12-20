# Soccer-AI System Atlas

## Architecture Overview

```mermaid
graph TB
    subgraph "CLIENT LAYER"
        UI[React Frontend]
        API_CLIENT[API Client]
    end

    subgraph "API LAYER"
        FASTAPI[FastAPI Server]
        ROUTERS[Route Handlers]
        MIDDLEWARE[Security Middleware]
    end

    subgraph "INTELLIGENCE LAYER"
        RAG[Hybrid RAG Engine]
        AI_RESP[AI Response Generator]
        PERSONA[Fan Persona System]
    end

    subgraph "KNOWLEDGE GRAPH LAYER"
        KG_NODES[(kg_nodes)]
        KG_EDGES[(kg_edges)]
        TRAVERSAL[Graph Traversal]
        CONTEXT[Entity Context]
    end

    subgraph "DATA LAYER"
        FTS5[FTS5 Search]
        TEAMS[(teams)]
        LEGENDS[(club_legends)]
        MOMENTS[(club_moments)]
        MOOD[(club_mood)]
        RIVALRIES[(club_rivalries)]
    end

    subgraph "EXTERNAL"
        HAIKU[Claude Haiku 4.5 API]
        FOOTBALL_DATA[football-data.org API]
    end

    UI --> API_CLIENT
    API_CLIENT --> FASTAPI
    FASTAPI --> ROUTERS
    ROUTERS --> MIDDLEWARE
    MIDDLEWARE --> RAG

    RAG --> FTS5
    RAG --> TRAVERSAL
    TRAVERSAL --> KG_NODES
    TRAVERSAL --> KG_EDGES
    CONTEXT --> MOOD

    RAG --> AI_RESP
    AI_RESP --> PERSONA
    AI_RESP --> HAIKU

    KG_NODES -.-> TEAMS
    KG_NODES -.-> LEGENDS
    KG_NODES -.-> MOMENTS
    KG_EDGES -.-> RIVALRIES
```

## Data Flow: Query to Response

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant SEC as Security
    participant RAG as Hybrid RAG
    participant KG as Knowledge Graph
    participant FTS as FTS5 Search
    participant AI as Haiku API

    U->>API: POST /api/v1/chat
    API->>SEC: detect_injection(query)

    alt Injection Detected
        SEC-->>U: snap_back_response
    else Clean Query
        SEC->>RAG: retrieve_hybrid(query)

        par Parallel Retrieval
            RAG->>FTS: search_all(query)
            RAG->>KG: extract_kg_entities(query)
            KG->>KG: traverse_kg(nodes)
            KG->>KG: get_entity_context()
        end

        RAG->>RAG: fuse_contexts(fts, kg, mood)
        RAG->>AI: generate_response_kg_rag()
        AI-->>U: relationship-aware response
    end
```

## Knowledge Graph Schema

```mermaid
erDiagram
    KG_NODES {
        int node_id PK
        string node_type
        int entity_id FK
        string name
        json properties
    }

    KG_EDGES {
        int edge_id PK
        int source_id FK
        int target_id FK
        string relationship
        float weight
        json properties
    }

    TEAMS {
        int id PK
        string name
        string league
    }

    CLUB_LEGENDS {
        int id PK
        int team_id FK
        string name
        string era
    }

    CLUB_MOMENTS {
        int id PK
        int team_id FK
        string title
        string emotion
    }

    CLUB_RIVALRIES {
        int id PK
        int team_id FK
        int rival_team_id FK
        int intensity
    }

    CLUB_MOOD {
        int id PK
        int team_id FK
        string current_mood
        float mood_intensity
    }

    KG_NODES ||--o{ KG_EDGES : "source_id"
    KG_NODES ||--o{ KG_EDGES : "target_id"
    KG_NODES }o--|| TEAMS : "entity_id (team)"
    KG_NODES }o--|| CLUB_LEGENDS : "entity_id (legend)"
    KG_NODES }o--|| CLUB_MOMENTS : "entity_id (moment)"
```

## Graph Relationship Types

```mermaid
graph LR
    subgraph "Node Types"
        TEAM((Team))
        LEGEND((Legend))
        MOMENT((Moment))
    end

    subgraph "Relationships"
        LEGEND -->|legendary_at| TEAM
        MOMENT -->|occurred_at| TEAM
        MOMENT -->|against| TEAM
        TEAM -->|rival_of| TEAM
    end

    style TEAM fill:#e74c3c
    style LEGEND fill:#f39c12
    style MOMENT fill:#3498db
```

## Module Responsibility Map

```mermaid
mindmap
  root((Soccer-AI))
    Backend
      database.py 2001 lines
        SQLite Connection
        FTS5 Search
        KG Schema
        KG Traversal
        CRUD Operations
      rag.py 1343 lines
        Entity Extraction
        Intent Detection
        FTS5 Retrieval
        KG Retrieval
        Context Fusion
      ai_response.py 1272 lines
        Security Layer
        Intensity-Scaled Rivalry Prompts
        Haiku 4.5 Integration
        KG-RAG Generation
        Cost Tracking
      fan_enhancements.py 792 lines
        Mood Engine 6 states
        Rivalry Detection 43 edges
        Local Dialect 6 regions
      main.py 2385 lines
        FastAPI App 91 endpoints
        Auto-Refresh Scheduler
        Club Alias Resolution
        CORS Config
    Scripts
      refresh_season_data.py
        Auto every 6 hours
        Standings + Fixtures + Moods
      generate_trivia.py
        Mines 230K match history
        136 questions 6 categories
      enrich_iconic_matches.py
        KG enrichment
    Data
      Teams 23 & Players
      Games & Live Fixtures
      Standings Live
      Club Personality
        Legends
        78 Iconic Moments
        43 Rivalries
        Computed Mood
    Unified Knowledge Graph
      773 Nodes
        362 Persons
        54 Matches
        25 Clubs
        24 Moments
        21 Stadiums
        20 Teams
      717 Edges
        rival_of 43
        iconic_match_for 43
        legendary_at
        occurred_at
```

## Security Flow (Session-Based Escalation)

```mermaid
stateDiagram-v2
    [*] --> NORMAL: New Session

    NORMAL --> WARNED: 1st Injection (0ms delay)
    WARNED --> CAUTIOUS: 2nd Injection (500ms delay)
    CAUTIOUS --> ESCALATED: 3rd Injection (1000ms delay)
    ESCALATED --> ESCALATED: More Injections (2000ms delay)

    ESCALATED --> PROBATION: Genuine Query
    PROBATION --> NORMAL: 5 Clean Queries
    PROBATION --> ESCALATED: Injection Attempt

    WARNED --> NORMAL: 5 Clean Queries
    CAUTIOUS --> NORMAL: 10 Clean Queries

    note right of NORMAL: snap_back response
    note right of ESCALATED: security_persona response
```

## Security Response Types

```mermaid
graph TD
    subgraph "Detection"
        QUERY[User Query] --> DETECT{Injection Pattern?}
    end

    subgraph "Session State"
        DETECT -->|Yes| STATE{Current State?}
        STATE -->|normal/warned/cautious| SNAP[Fan Snap-Back]
        STATE -->|escalated| SECURITY[Security Persona]
    end

    subgraph "Rate Limiting"
        SNAP --> DELAY1[+0-1000ms delay]
        SECURITY --> DELAY2[+2000ms delay]
    end

    subgraph "Logging"
        DELAY1 --> LOG[Log to security_log]
        DELAY2 --> LOG
        LOG --> RESPONSE[Return Response]
    end

    DETECT -->|No| CLEAN[Clean Query Processing]
    CLEAN --> RAG[Hybrid RAG]
    RAG --> RESPONSE

    style SECURITY fill:#e74c3c
    style SNAP fill:#f39c12
    style CLEAN fill:#27ae60
```

## Trivia System Flow

```mermaid
graph LR
    subgraph "Request"
        REQ[GET /trivia] --> PARAMS{team_id? difficulty?}
    end

    subgraph "Selection"
        PARAMS -->|Filter| QUERY[Query trivia_questions]
        QUERY --> RANDOM[Random Selection]
    end

    subgraph "Response"
        RANDOM --> FORMAT[Format Question]
        FORMAT --> HIDE[Hide correct_answer]
        HIDE --> CLIENT[Return to Client]
    end

    subgraph "Check"
        ANSWER[POST /trivia/check] --> VERIFY{Match?}
        VERIFY -->|Yes| CORRECT[✓ + Explanation]
        VERIFY -->|No| WRONG[✗ + Correct Answer]
    end

    style CORRECT fill:#27ae60
    style WRONG fill:#e74c3c
```

## Predictor Integration (IMPLEMENTED)

```mermaid
graph TB
    subgraph "Fan App (Soccer-AI)"
        FAN[Chat Interface]
        PERSONA[Fan Personas x20]
        TRIVIA[Trivia System 136 Qs]
        MOOD[(club_mood - computed)]
    end

    subgraph "Predictor Module (backend/predictor/)"
        RATINGS[team_ratings.py]
        DRAWS[draw_detector.py]
        BACKTEST[backtest_ratings.py]
        TUNE[tune_draw_threshold.py]
    end

    subgraph "Third Knowledge Patterns"
        P1[close_matchup]
        P2[midtable_clash]
        P3[defensive_matchup]
        P4[parked_bus_risk]
        P5[derby_caution]
        P6[top_vs_top]
    end

    subgraph "Prediction Flow"
        RATINGS -->|power_diff| DRAWS
        P1 & P2 & P3 & P4 & P5 & P6 -->|patterns| DRAWS
        DRAWS -->|53.9% accuracy| FAN
    end

    subgraph "API Endpoints"
        API1[GET /predictions/match/home/away]
        API2[GET /predictions/weekend]
    end

    DRAWS --> API1
    DRAWS --> API2

    style RATINGS fill:#f39c12
    style DRAWS fill:#9b59b6
    style FAN fill:#3498db
```

### Predictor Accuracy Metrics

| Metric | V1 (Tri-Lens) | V2 (DC+BK) |
|--------|--------------|------------|
| Overall Accuracy | 53.2% | **53.9%** |
| Draw Precision | 17.3% | **50.0%** |
| Brier Score | 0.580 | 0.584 |
| Architecture | 55% Poisson + 45% Oracle | **40% Dixon-Coles + 60% Bookmaker** |

### Third Knowledge Pattern Details

| Pattern | Trigger Condition | Draw Boost |
|---------|-------------------|------------|
| `close_matchup` | Power diff < 10 | 1.3x - 1.8x |
| `midtable_clash` | Both teams positions 8-15 | 1.4x |
| `defensive_matchup` | Both teams defensive style | 1.35x |
| `parked_bus_risk` | Big favorite + defensive underdog | 1.25x |
| `derby_caution` | Rivalry match | 1.3x |
| `top_vs_top` | Both in top 6 | 1.25x |

## Gap Tracker Architecture

```mermaid
graph TD
    subgraph "Source Documents"
        DOCS[.md/.ctx files]
        SCHEMA[schema.sql]
        TESTS[test_*.py]
    end

    subgraph "Scanner"
        SCAN[scan_implementation_gaps.py]
        PARSE[Parse TODO/PENDING]
        COMPARE[Compare docs vs main.py]
    end

    subgraph "Database"
        GAPS[(implementation_gaps)]
    end

    subgraph "Admin API"
        GET[GET /admin/gaps]
        UPDATE[POST /admin/gaps/{id}/status]
    end

    DOCS --> SCAN
    SCHEMA --> SCAN
    TESTS --> SCAN
    SCAN --> PARSE
    PARSE --> COMPARE
    COMPARE --> GAPS

    GAPS --> GET
    UPDATE --> GAPS

    style GAPS fill:#e67e22
```

## Current Stats (Updated April 10, 2026)

| Metric | Value |
|--------|-------|
| **Unified KG Nodes** | **773** (362 persons, 54 matches, 25 clubs, 24 moments) |
| **Unified KG Edges** | **717** (43 rivalries, 43 iconic matches) |
| Match History | 230,557 records |
| KB Facts | 681 |
| Fan Personas | **20** (one per Premier League club) |
| Dialect Regions | 6 (Scouse, Geordie, Mancunian, Cockney, Midlands, Neutral) |
| Iconic Matches/Moments | 78 (54 matches + 24 moments) |
| Rivalry Edges | 43 (with intensity weights 0.6-1.0) |
| **Trivia Questions** | **136** (6 categories: records, h2h, history, stats, rivalries, legends) |
| Security States | 5 (normal -> escalated) |
| **Test Cases** | **102** (35 behavioral + 33 integration + 34 KG) |
| **API Endpoints** | **91** (V2 predictions, debate, companion, mood timeline, cards, memories, budget) |
| API Cost/Query | ~$0.002 (Haiku 4.5) |
| **Predictor Accuracy** | **53.9%** (Dixon-Coles + Bookmaker v2) |
| **Draw Precision** | **50.0%** (up from 17.3%) |
| Third Knowledge Patterns | 6 |
| Data Refresh | Auto every 6 hours (football-data.org) |
| **Frontend Pages** | **12** (Games, Table, Clubs, Chat, Predictions, Trivia, Debate, Companion, MoodTimeline, PredictionCard, Demo, TeamDetail) |
| Club Colour Palettes | 20 (dynamic CSS variable theming) |
| Typography | Barlow Condensed + Source Serif 4 + JetBrains Mono |
| Portfolio Demo | /demo — 7 scenes, zero API calls, keyboard navigation |
| Fan Debate Mode | /debate -- two personas argue, 1-5 rounds |
| User Fan Memories | Auto-detected in chat, recalled in future conversations |
| Predictor Explainability | Fan weaves Dixon-Coles data naturally into responses |
| Kinetic Theming | Mood-responsive CSS: rain for despair, glow for euphoria |
| 4D Radar Visualizer | SVG diamond radar in chat header + Demo page |
| Shareable Cards | /card/:home/:away with AI take + verbalogix.com branding |

## File Structure

```
soccer-AI/
├── CLAUDE.md                    # Project instructions
├── README.md                    # Quick start guide
├── schema.sql                   # Database schema
├── api_design.md               # API specification
├── docs/
│   ├── ARIEL_FULL_STORY.md              # Original vision document
│   ├── SOCCER_AI_SYSTEM_ATLAS.md        # This file
│   ├── API_CONTRACTS.md                 # Full API specification
│   ├── architecture/                    # 4D Persona Architecture spec
│   └── arxiv/                           # arXiv paper
├── backend/
│   ├── main.py                 # FastAPI app (3368 lines, 91 endpoints)
│   ├── database.py             # DB + KG layer (2001 lines)
│   ├── rag.py                  # Hybrid RAG (1343 lines)
│   ├── ai_response.py          # AI generation + rivalry scaling (1272 lines)
│   ├── fan_enhancements.py     # Mood, rivalry, dialect (792 lines)
│   ├── config.py               # 4D Persona feature flag
│   ├── persona_bridge.py       # 4D integration layer
│   ├── live_football_provider.py # Live data -> 4D state
│   ├── models.py               # Pydantic models
│   ├── security_session.py     # Injection protection
│   ├── conversation_intelligence.py # Conversation enrichment
│   ├── rate_limiter.py          # Per-IP rate limits + budget cap
│   ├── live_companion.py        # Match day poller + fan reactions
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment variable template
│   ├── Dockerfile              # Docker config for Fly.io
│   ├── fly.toml                # Fly.io deployment config
│   ├── soccer_ai.db            # Main database (gitignored)
│   ├── unified_soccer_ai_kg.db # Unified KG 41.8 MB (gitignored)
│   ├── scripts/
│   │   ├── refresh_season_data.py  # Auto-refresh (every 6h)
│   │   ├── generate_trivia.py      # Trivia from match DB
│   │   └── enrich_iconic_matches.py # KG enrichment
│   ├── predictor/              # Match prediction module
│   │   ├── prediction_engine.py    # Main engine
│   │   ├── dixon_coles.py          # V2: Dixon-Coles + Bookmaker ensemble
│   │   ├── tri_lens_predictor.py   # V1: Tri-Lens fusion (legacy)
│   │   ├── hybrid_oracle.py        # ELO + Pattern hybrid
│   │   ├── poisson_predictor.py    # Poisson xG model
│   │   ├── team_ratings.py         # ELO power ratings
│   │   ├── draw_detector.py        # 6 Third Knowledge patterns
│   │   └── backtest_ratings.py     # Validation framework
│   ├── kg/                     # Knowledge graph modules
│   ├── tests/                  # 102 tests (35+33+34)
│   │   ├── test_4d_behavioral.py   # 35 behavioral tests
│   │   ├── test_4d_integration.py  # 33 integration tests
│   │   └── test_kg_migration.py    # 34 KG migration tests
│   └── test_*.py               # Legacy test files
├── frontend/                   # React 19 + Vite 7 + Tailwind (Matchday Programme)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/              # 8 pages
│   │   │   ├── Dashboard.tsx, Standings.tsx, Teams.tsx, TeamDetail.tsx
│   │   │   ├── Chat.tsx        # Fan chat with club theming
│   │   │   ├── Trivia.tsx      # 136-question trivia game
│   │   │   ├── Debate.tsx      # Two-persona debate mode
│   │   │   ├── Predictions.tsx  # All fixtures with Dixon-Coles predictions
│   │   │   ├── Companion.tsx   # Match Day Live Companion
│   │   │   ├── MoodTimeline.tsx # Season Mood Timeline (pure SVG)
│   │   │   ├── PredictionCard.tsx # Shareable prediction card
│   │   │   └── Demo.tsx        # Portfolio guided tour (no API)
│   │   ├── components/Teams/
│   │   │   └── FourDRadar.tsx  # 4D SVG radar visualizer
│   │   ├── config/
│   │   │   ├── clubThemes.ts   # 20 club colour palettes
│   │   │   ├── ClubThemeProvider.tsx # Global theme context
│   │   │   └── theme.ts        # Base theme + typography
│   │   ├── components/         # 28 UI components
│   │   ├── hooks/              # 4 custom hooks
│   │   └── services/api.ts     # API client (458 lines)
│   └── package.json
├── robert/                     # Ariel framework data
└── flask-frontend/             # Testing only - ignore
```
