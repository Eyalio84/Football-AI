# Soccer-AI

## Reference Implementation of the 4D Persona Architecture

**Author**: Eyal Nof
**Created**: December 2025 | **Last Updated**: April 2026

> *"The AI doesn't play a character. It lives one."*

---

## What's New: A Novel AI Architecture

This project demonstrates the **4D Persona Architecture**, a paradigm shift in how AI personas are designed:

| Traditional | 4D Persona |
|-------------|------------|
| "Be enthusiastic" | Enthusiasm *derived* from winning streak |
| Static text prompt | Dynamic 4D coordinate |
| Actor in costume | Character inhabiting reality |

### The Four Dimensions

```
P(t) = (x, y, z, t)

x = Emotional   -> Mood derived from ACTUAL match results
y = Relational  -> Position in club->rivals->legends knowledge graph
z = Linguistic  -> Regional dialect (Scouse, Geordie, Cockney)
t = Temporal    -> Evolution trajectory through time
```

### Embodied RAG

Traditional RAG retrieves facts. **Embodied RAG computes feelings.**

When Arsenal loses three matches, the AI fan isn't *told* to be frustrated -- it *is* frustrated, because the data says so.

**[Full Specification](docs/architecture/4D-PERSONA-ARCHITECTURE.md)** | **[arXiv Paper](docs/arxiv/4d-persona-architecture-v2.pdf)**

---

## What Is Soccer-AI?

An emotionally intelligent football companion that **feels the game with you**.

- **Supports your club** with authentic fan emotion (20 Premier League personas)
- **Speaks proper football** (match, nil, pitch - never "soccer")
- **Knows rivalries** and won't praise your enemies (43 rivalry edges, intensity-scaled)
- **Debates rivals** -- pit two fan personas against each other on any topic
- **Predicts matches** with Dixon-Coles + Bookmaker ensemble (53.9% accuracy, 50% draw precision)
- **Remembers legends and moments** -- 78 iconic matches in the knowledge graph
- **Tests your knowledge** with 136 auto-generated trivia questions
- **Stays current** -- live data auto-refreshes every 6 hours from football-data.org
- **Remembers YOUR story** -- share personal fan memories, recalled naturally in future chats
- **Shareable cards** -- prediction cards for social media at `/card/Arsenal/City`
- **Reacts to mood** -- kinetic theming: rain overlay for despair, glow pulse for euphoria
- **Portfolio demo** -- self-contained guided tour at `/demo` (no API keys needed)

---

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
# Set API keys in .env:
# ANTHROPIC_API_KEY=sk-ant-...
# FOOTBALL_DATA_API_KEY=your-key-here
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Backend: http://localhost:8000 | Frontend: http://localhost:5173

---

## Features

### Dynamic Mood System (Dimension X)
Mood computed from **actual match results** -- anti-gaslighting by design:
```
Arsenal:   euphoric   (1st, 70 pts) - "We're top of the league!"
Man City:  confident  (2nd, 61 pts) - "Right in the mix"
Wolves:    despairing (20th, 17 pts) - "What's the point..."
```

### Rivalry Banter (Dimension Y)
43 rivalry edges with intensity-scaled prompts:
- **0.9+ intensity** (blood rivalry): Contempt, tribal pride, no neutral analysis
- **0.7+ intensity**: Disdain, backhanded compliments
- Arsenal + "Spurs?" -> *"Have you clapped eyes at the table? They're in 17th!"*
- Man Utd + "City?" -> *"All that money... proper frustrating to watch"*

### Local Dialect (Dimension Z)
Regional voice identity:
- **Liverpool**: Scouse ("la", "sound", "boss")
- **Newcastle**: Geordie ("howay", "canny", "like")
- **Man United**: Mancunian ("our kid", "proper")
- **Arsenal**: Cockney ("blimey", "ain't we")

### Trivia System (136 questions, 6 categories)
Auto-generated from 230K match database:
- **records**: Biggest wins, season records, ELO peaks
- **head2head**: Dominance patterns between teams
- **history**: Famous comebacks
- **stats**: Scoreline frequencies, home/away records
- **rivalries**: Derby match counts and records
- **legends**: Knowledge base facts

---

## Architecture

```
React Frontend (Vite 7 + React 19 + Tailwind)
      |
      v
FastAPI Backend (91 endpoints, rate-limited) ----+
      |                                          |
      v                                          v
+---------------------------------------------+
|              4D PERSONA ENGINE               |
+------------+-----------+-----------+---------+
| EMOTIONAL  | RELATIONAL| LINGUISTIC| TEMPORAL|
| (X-axis)   | (Y-axis)  | (Z-axis)  | (T-axis)|
|            |           |           |         |
| Match DB   | KG Graph  | Dialect DB| History |
| Form calc  | 43 rivals | Voice map | Memory  |
| Mood derive| 78 matches| Inject    | Momentum|
+------------+-----------+-----------+---------+
                    |
                    v
            Dynamic System Prompt
                    |
                    v
              Claude Haiku 4.5
```

---

## Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `backend/main.py` | 3,368 | FastAPI app, 91 endpoints, rate-limited, budget-capped |
| `backend/database.py` | 2,001 | SQLite + FTS5 + KG queries |
| `backend/rag.py` | 1,343 | Hybrid RAG retrieval |
| `backend/ai_response.py` | 1,272 | Haiku 4.5 + intensity-scaled rivalry prompts |
| `backend/fan_enhancements.py` | 792 | Mood engine, rivalry detection, dialects |
| `backend/persona_bridge.py` | -- | 4D Persona integration layer |
| `backend/live_football_provider.py` | -- | Live API + DB fallback |
| `backend/unified_soccer_ai_kg.db` | 41.8 MB | Unified knowledge graph |
| `backend/scripts/refresh_season_data.py` | -- | Auto-refresh standings/fixtures/moods |
| `backend/scripts/generate_trivia.py` | -- | Mine match_history for trivia |
| `backend/scripts/enrich_iconic_matches.py` | -- | Add iconic match nodes to KG |
| `frontend/src/pages/Demo.tsx` | -- | Portfolio guided tour (7 scenes, zero API calls) |
| `frontend/src/pages/Debate.tsx` | -- | Fan debate UI (two-persona exchange) |
| `frontend/src/pages/Trivia.tsx` | -- | Trivia game (136 Qs, 6 categories, scoring) |
| `frontend/src/config/clubThemes.ts` | -- | 20 club colour palettes + theme provider |
| `frontend/src/pages/Companion.tsx` | -- | Match Day Live Companion |
| `frontend/src/pages/MoodTimeline.tsx` | -- | Season Mood Timeline (pure SVG) |
| `backend/predictor/dixon_coles.py` | -- | Dixon-Coles model + bookmaker odds + backtest |
| `backend/live_companion.py` | -- | Live match poller + fan reaction generator |
| `frontend/src/pages/PredictionCard.tsx` | -- | Shareable prediction card (social media) |
| `frontend/src/components/Teams/FourDRadar.tsx` | -- | 4D Coordinate Visualizer (SVG radar) |

---

## System Stats

| Metric | Value |
|--------|-------|
| Tests Passing | **102/102** |
| API Endpoints | 91 |
| KG Nodes | 773 (362 persons, 54 matches, 25 clubs, 24 moments) |
| KG Edges | 717 (43 rivalries, 43 iconic matches) |
| Match History | 230,557 records |
| KB Facts | 681 |
| Trivia Questions | 136 (6 categories) |
| Fan Personas | 20 (all PL clubs) |
| Dialect Regions | 6 (Scouse, Geordie, Mancunian, Cockney, Midlands, Neutral) |
| Feature Flag | `USE_4D_PERSONA = True` |
| Data Refresh | Auto every 6 hours (football-data.org) |
| Frontend Pages | 12 (Games, Table, Clubs, Chat, Predictions, Trivia, Debate, Companion, MoodTimeline, PredictionCard, Demo, TeamDetail) |
| Prediction Accuracy | 53.9% overall, 50% draw precision (Dixon-Coles + Bookmaker v2) |
| Club Colour Palettes | 20 (dynamic CSS theme shifting) |
| Typography | Barlow Condensed + Source Serif 4 + JetBrains Mono |
| Rate Limiting | Per-IP (30 chat/min, 5 debate/hr) + $5/day global budget cap |
| Deployment | Vercel (frontend) + Fly.io (backend) |
| Security | API keys in .env (gitignored), CORS whitelist, rate limiting |

---

## Deployment

| Component | Platform | Config |
|-----------|----------|--------|
| Frontend | Vercel | `vite build` output, `VITE_API_URL` env var |
| Backend | Fly.io | `backend/Dockerfile` + `fly.toml`, London region |
| GitHub | [Eyalio84/Football-AI](https://github.com/Eyalio84/Football-AI) | Public repo |
| Portfolio | [verbalogix.com](https://www.verbalogix.com) | Demo at `/demo` |

---

## Citation

```bibtex
@article{nof2025persona4d,
  title={4D Persona Architecture: A Dimensional Model for Embodied AI Agents},
  author={Nof, Eyal},
  year={2025},
  note={Reference implementation: Soccer-AI}
}
```

---

## License

MIT License

---

**Created by Eyal Nof** | **December 2025 -- April 2026**

*Fan at heart. Architect by discovery.*
