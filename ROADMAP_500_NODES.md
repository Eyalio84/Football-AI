# Soccer-AI Roadmap to 500 Nodes

## Current State (Dec 27, 2024)

```
┌────────────────────────────────────────┐
│        CURRENT KG STATUS               │
├────────────────────────────────────────┤
│  Total Nodes:     138                  │
│  Total Edges:     236                  │
│  KB Facts:        98                   │
│  Target:          500 nodes            │
│  Gap:             362 nodes needed     │
└────────────────────────────────────────┘
```

### Node Distribution
| Type           | Count | Notes                           |
|----------------|-------|---------------------------------|
| api_endpoint   | 64    | Architecture (keep as-is)       |
| fan_persona    | 19    | All 20 PL teams                 |
| data_table     | 12    | System schema                   |
| trophy         | 10    | Need expansion                  |
| club           | 8     | **CRITICAL GAP**                |
| person         | 1     | **CRITICAL GAP**                |
| match          | 1     | **CRITICAL GAP**                |

---

## The Problem

The KG is architecture-heavy (64 api_endpoints) but **football-light**:
- Only 1 person (Alex Ferguson)
- Only 1 match (4-3 Derby)
- Only 8 clubs (need 20+ minimum)

For "the fan I really want", we need **football knowledge**, not architecture endpoints.

---

## Phase 1: Foundation Teams (Target: +100 nodes)

### Goal: Complete Big 6 + Historic Rivals

| Team | Nodes Needed | Source |
|------|--------------|--------|
| Manchester United | +20 | PDF (Ferguson, Best, Charlton, Rooney...) |
| Liverpool | +20 | PDF (Shankly, Dalglish, Gerrard, Salah...) |
| Arsenal | +20 | PDF (Wenger, Henry, Bergkamp, Adams...) |
| Chelsea | +20 | PDF (Mourinho, Lampard, Terry, Drogba...) |
| Manchester City | +15 | WebSearch (Guardiola era) |
| Tottenham | +5 | WebSearch (basic) |

**Execution:**
```bash
# For each team:
python ingest.py pdf /path/to/TeamName.PDF
python ingest.py pdf /path/to/List_of_TeamName_players.PDF
```

**Nodes created:**
- Club (1 per team)
- Manager (2-3 legendary per team)
- Players (10-15 per team)
- Stadium (1 per team)
- Key matches (2-3 per team)

---

## Phase 2: Trophies & Seasons (Target: +80 nodes)

### Goal: Complete Trophy Network

| Trophy Type | Count | Examples |
|-------------|-------|----------|
| Domestic League | 3 | Premier League, Championship, League One |
| Domestic Cup | 5 | FA Cup, League Cup, Community Shield... |
| European | 5 | UCL, Europa, Super Cup... |
| Seasons | 33 | 1992-93 to 2024-25 |

**Nodes per season:**
- Season entity (1)
- Champion edge (1)
- Top scorer edge (1)

**Execution:**
```bash
# WebSearch for trophy history
python ingest.py query "FA Cup winners since 1992"
# Manual trophy nodes
python ingest.py fact "Arsenal won the 1998 FA Cup Final 2-0 against Newcastle"
```

---

## Phase 3: Legends & Stats (Target: +120 nodes)

### Goal: Top 50 All-Time PL Players

| Category | Players | Source |
|----------|---------|--------|
| Top Scorers | 20 | WebSearch (Shearer, Rooney, Aguero...) |
| Assist Kings | 10 | WebSearch (Giggs, Fabregas, De Bruyne...) |
| Goalkeepers | 10 | WebSearch (Schmeichel, Cech, Seaman...) |
| Defenders | 10 | WebSearch (Ferdinand, Terry, Adams...) |

**Per player:**
- Person node (1)
- played_for edges (2-3)
- Career stats in properties

**Execution:**
```bash
# Bulk player facts
python ingest.py file legends.txt
```

---

## Phase 4: Iconic Matches (Target: +62 nodes)

### Goal: 50 Most Memorable PL Matches

| Category | Count | Examples |
|----------|-------|----------|
| Title deciders | 10 | Aguero 93:20, Arsenal 1989... |
| Derby classics | 15 | 4-3 Manchester, 4-4 Liverpool-Arsenal... |
| European finals | 10 | Istanbul 2005, Moscow 2008... |
| Cup finals | 15 | Memorable FA Cup moments |

**Per match:**
- Match node (1)
- played_in edges (2)
- scored_in edges (3-5)

---

## Execution Timeline

```
Week 1: Phase 1 - Foundation Teams
├── Download 6 team PDFs from Wikipedia
├── Run parser on each
├── Verify: 100+ new nodes
│
Week 2: Phase 2 - Trophies & Seasons
├── WebSearch trophy histories
├── Create season nodes
├── Verify: 80+ new nodes
│
Week 3: Phase 3 - Legends
├── WebSearch top players
├── Create player nodes with careers
├── Verify: 120+ new nodes
│
Week 4: Phase 4 - Matches
├── WebSearch iconic matches
├── Create match nodes
├── Verify: 62+ new nodes
│
TOTAL: 362+ new nodes → 500 target achieved
```

---

## Quick Wins (Do Today)

### 1. Add Missing Big 6 Clubs
```bash
python ingest.py fact "Manchester City F.C. was founded in 1880, known as The Cityzens"
python ingest.py fact "Tottenham Hotspur was founded in 1882, known as Spurs"
```

### 2. Add Top 5 All-Time Scorers
```bash
python ingest.py fact "Alan Shearer scored 260 Premier League goals, the all-time record"
python ingest.py fact "Wayne Rooney scored 208 Premier League goals for Everton and Manchester United"
python ingest.py fact "Andrew Cole scored 187 Premier League goals"
python ingest.py fact "Sergio Aguero scored 184 Premier League goals, all for Manchester City"
python ingest.py fact "Frank Lampard scored 177 Premier League goals"
```

### 3. Add Current Champions
```bash
python ingest.py fact "Liverpool won the 2024-25 Premier League under manager Arne Slot"
```

---

## Metrics Dashboard

| Metric | Current | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|---------|---------|---------|---------|---------|
| Nodes  | 138     | 238     | 318     | 438     | **500** |
| Edges  | 236     | 350     | 450     | 600     | 700     |
| Facts  | 98      | 200     | 350     | 500     | 600     |
| Clubs  | 8       | 20      | 20      | 20      | 20      |
| Persons| 1       | 60      | 70      | 120     | 120     |
| Matches| 1       | 10      | 15      | 20      | 70      |

---

## Automated Expansion Script

```python
# expand_kg.py - Run this to bulk expand
from fact_ingestion_pipeline import FactPipeline

TEAMS_TO_ADD = [
    "Manchester City", "Tottenham Hotspur", "Newcastle United",
    "Aston Villa", "West Ham United", "Brighton"
]

TOP_SCORERS = [
    ("Alan Shearer", 260, ["Blackburn", "Newcastle"]),
    ("Wayne Rooney", 208, ["Everton", "Manchester United"]),
    ("Andrew Cole", 187, ["Newcastle", "Manchester United"]),
    ("Sergio Aguero", 184, ["Manchester City"]),
    ("Frank Lampard", 177, ["West Ham", "Chelsea"]),
]

pipeline = FactPipeline()

# Add teams
for team in TEAMS_TO_ADD:
    pipeline.add_fact(f"{team} is a Premier League football club")

# Add scorers
for name, goals, clubs in TOP_SCORERS:
    pipeline.add_fact(
        f"{name} scored {goals} Premier League goals for {' and '.join(clubs)}",
        entities=[name] + clubs
    )

pipeline.close()
```

---

## Why 500 Nodes?

Based on analysis, 500 nodes provides:
- **Coverage**: All 20 PL teams with depth
- **Connectivity**: Rich relationship graph for traversal
- **RAG Quality**: Enough facts for meaningful retrieval
- **Fan Experience**: Answers to 90%+ of common questions

Below 500: Too sparse, many queries return empty
Above 500: Diminishing returns, maintenance overhead

---

## Next Steps

1. **Run Quick Wins** (30 mins) → +15 nodes
2. **Download Big 6 PDFs** → Prep for Phase 1
3. **Execute Phase 1** → +100 nodes
4. **Validate RAG** → Test query coverage

*Document created: 2024-12-27*
*Current: 138 nodes | Target: 500 nodes | Gap: 362*
