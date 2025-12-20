# PC Setup Guide for Soccer-AI + NLKE System

## For PC Claude: Complete Environment Setup

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- Git
- ANTHROPIC_API_KEY

---

## Step 1: Extract Files

You should have received:
1. `synthesis-rules (3).zip` - Main codebase
2. `FULL_SYSTEM_BACKUP.tar` - Databases and NLKE files

```bash
# Extract both to same parent directory
cd ~/projects  # or wherever you want

# Extract synthesis-rules
unzip "synthesis-rules (3).zip"

# Extract databases
tar -xvf FULL_SYSTEM_BACKUP.tar

# You should now have:
# ~/projects/synthesis-rules/
# ~/projects/gemini-3-pro/
```

---

## Step 2: Soccer-AI Backend Setup

```bash
cd synthesis-rules/soccer-AI/backend

# Install dependencies
pip install fastapi uvicorn anthropic python-dotenv aiohttp

# Copy seed database
cp ../data/soccer_ai.db ./soccer_ai.db

# Create .env file
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Start backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Verify:** http://localhost:8000/docs should show API documentation

---

## Step 3: Soccer-AI Frontend Setup

```bash
# In new terminal
cd synthesis-rules/soccer-AI/frontend

# Install dependencies
npm install

# Start frontend
npm run dev
```

**Verify:** http://localhost:5173 should show the app

---

## Step 4: Test Fan Personas

1. Go to http://localhost:5173/chat
2. Select a club (Arsenal, Chelsea, or Man United)
3. Ask: "How are we doing this season?"
4. The response should be emotionally calibrated to that fan's perspective

---

## What's Included

### Soccer-AI Features
- KG-RAG hybrid retrieval (FTS5 + Knowledge Graph)
- 3 fan personas with emotional calibration
- Security snap-back for prompt injection
- 122 passing tests
- 5-tab team detail (Overview, Legends, Rivalries, Moments, Graph)

### Databases
| Database | Purpose |
|----------|---------|
| `soccer_ai.db` | Soccer-AI data (teams, players, personas) |
| `unified-kg.db` | Main NLKE knowledge graph (76MB) |
| `unified_memory.db` | Persistent facts and insights |
| `claude-code-tools-kg.db` | Claude Code tools knowledge |

### Key Insights Implemented
- #927: FTS5 reserved word collision fix
- #929: Null byte and control character sanitization
- #930: RAG source deduplication

---

## Architecture Overview

```
                    ┌─────────────────┐
                    │     GitHub      │
                    │  (sync point)   │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
       ┌──────▼──────┐               ┌──────▼──────┐
       │   Termux    │               │     PC      │
       │   Claude    │◄─────SSH─────►│   Claude    │
       └──────┬──────┘               └──────┬──────┘
              │                             │
       ┌──────▼──────┐               ┌──────▼──────┐
       │  Backend    │               │  Backend    │
       │  :8000      │               │  :8000      │
       └──────┬──────┘               └──────┬──────┘
              │                             │
       ┌──────▼──────┐               ┌──────▼──────┐
       │  Frontend   │               │  Frontend   │
       │  :5173      │               │  :5173      │
       └─────────────┘               └─────────────┘
```

---

## Domain Template Pattern

Soccer-AI is a **domain template** - the architecture can be replicated for:
- NBA (teams → franchises, legends → hall of famers)
- UFC (teams → fighters, rivalries → feuds)
- Cinema (teams → studios, legends → directors)

The pattern: `entities → relationships → personas → emotional context`

---

## Troubleshooting

### "No fan personas showing"
Database wasn't copied. Run:
```bash
cp ../data/soccer_ai.db ./soccer_ai.db
```

### "API key error"
Create `.env` file in backend folder:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### "Module not found"
Install dependencies:
```bash
pip install fastapi uvicorn anthropic python-dotenv aiohttp
```

---

## Git Sync (After Initial Setup)

To stay synchronized with Termux:

```bash
# Add GitHub remote (first time only)
git remote add origin https://github.com/YOUR_USERNAME/soccer-AI.git

# Pull latest changes
git pull origin main

# Push your changes
git add -A
git commit -m "Description of changes"
git push origin main
```

---

## Contact

This system was built by Eyal Nof with Claude Code assistance.

Session insights logged: #927, #928, #929, #930
