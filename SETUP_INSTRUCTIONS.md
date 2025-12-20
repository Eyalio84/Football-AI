# Soccer-AI Setup Instructions

## Quick Start (PC)

### 1. Copy Database
```bash
cp data/soccer_ai.db backend/soccer_ai.db
```

### 2. Backend Setup
```bash
cd backend
pip install fastapi uvicorn anthropic python-dotenv aiohttp
```

Create `backend/.env`:
```
ANTHROPIC_API_KEY=your-key-here
```

Start backend:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Access
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

## What's Included

### Fan Personas (3)
- **Arsenal Fan** - Passionate Gunner with rivalry against Spurs
- **Chelsea Fan** - Blues supporter with rivalry against Arsenal
- **Man United Fan** - Red Devils fan with rivalry against Liverpool/Man City

### Knowledge Graph Data
- **Legends**: Iconic players for each club (Henry, Lampard, Cantona, etc.)
- **Rivalries**: Historical rivalries with context
- **Moments**: Historic moments with emotional weight
- **Mood**: Current club mood based on recent events

### Features
- KG-RAG hybrid retrieval (FTS5 + Graph)
- Security snap-back for prompt injection
- 5-tab team detail (Overview, Legends, Rivalries, Moments, Graph)
- vis.js knowledge graph visualization

## Testing
```bash
cd backend
python -m pytest -v
```

Expected: 122 tests passing

## Architecture
```
SQLite + FTS5 → FastAPI → Haiku API → React Frontend
```

This is a **domain template** - replicable for NBA, UFC, Cinema, etc.
