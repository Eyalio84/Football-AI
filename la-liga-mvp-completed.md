# La Liga MVP — Completion & Achievement Report

**Date**: April 2026  
**Status**: MVP Complete ✓  
**Proof of concept**: Multi-league fan persona architecture proven

---

## What Was Achieved

The La Liga MVP proves that Football-AI's architecture is **league-agnostic by design**. Adding a second league required no changes to the core AI engine — only configuration, data, and a dedicated UI page.

### System State After MVP

| Layer | Before | After |
|-------|--------|-------|
| Leagues supported | 1 (Premier League) | **2 (PL + La Liga)** |
| Total clubs | 20 | **40** |
| Clubs with full personas | 20 | **26** (6 La Liga added) |
| Historical matches in DB | 9,410 (E0) | **+9,008 SP1** = 18,418 |
| KG nodes | 773 | **+legend/moment nodes for 6 clubs** |
| Rivalries configured | PL only | **+El Clásico, Derbi Madrileño, Gran Derbi, Basque Derby, Derbi de la Comunitat** |
| Dialect regions | 5 (PL) | **+5 Spanish regions** (castilian, catalan, basque, andalusian, valencian) |
| Frontend routes | `/chat` | **+`/la-liga-chat`** |

### The 6 MVP Clubs

| Club ID | Display Name | Region | Rivals Configured | Stadium |
|---------|-------------|--------|-------------------|---------|
| `real_madrid` | Real Madrid | Castilian | Barcelona (1.0), Atletico (0.9) | Santiago Bernabéu |
| `barcelona` | FC Barcelona | Catalan | Real Madrid (1.0), Espanyol (0.85) | Spotify Camp Nou |
| `atletico_madrid` | Atlético Madrid | Castilian | Real Madrid (0.95), Barcelona (0.8) | Cívitas Metropolitano |
| `sevilla` | Sevilla FC | Andalusian | Real Betis (1.0) | Ramón Sánchez-Pizjuán |
| `athletic_bilbao` | Athletic Club | Basque | Real Sociedad (0.95) | San Mamés |
| `valencia` | Valencia CF | Valencian | Villarreal (0.8), Levante (0.7) | Mestalla |

### What Makes Each Club's AI Voice Distinct

Each persona is grounded by three combined layers:

1. **`voice_description`** — summary injected at the top of the system prompt
2. **`dialect.vocab_inject`** — regional language instructions (Catalan vs. Castilian vs. Basque)
3. **`dialect.phrases`** — authentic expressions injected naturally ("¡Hala Madrid!", "Visca el Barça!", "Aupa Athletic!")

The result: a Real Madrid fan says *"bestial"* where an Arsenal fan says *"great"*. A Barcelona fan drops *"Visca"* in celebration. An Athletic Bilbao fan talks about *cantera* (academy) philosophy.

---

## Architecture — How It All Fits Together

```
Leagues/La_Liga/
├── league_config.json          # 20 clubs with API IDs, CSV names, dialect regions
└── clubs/
    ├── real_madrid.json         # Full persona: dialect, legends, moments, rivalries
    ├── barcelona.json
    ├── atletico_madrid.json
    ├── sevilla.json
    ├── athletic_bilbao.json
    └── valencia.json

backend/league_loader.py        # Walks all Leagues/*/league_config.json at import time
    → CLUB_DISPLAY_NAMES (40 clubs)
    → CLUB_API_NAMES
    → RIVALRIES (26 clubs with rivalry data)
    → DIALECTS (26 clubs with dialect data)
    → ALL_LEAGUES { la_liga, premier_league }

backend/main.py
    VALID_CLUBS = set(CLUB_DISPLAY_NAMES.keys()) | {"analyst"}
    → ChatRequest.get_club() used at BOTH regular + stream endpoints
    → /api/v1/leagues endpoint returns all registered leagues + clubs

backend/persona_bridge.py
    → _get_base_prompt() is now league-aware
    → Spanish clubs get Spanish voice, Spanish region origin
    → PL clubs continue unchanged

frontend/src/pages/LaLigaChat.tsx
    → 6 hardcoded clubs — zero dependency on LeagueProvider
    → No race condition possible; club_id is always correct
    → Sends { message, club_id: "real_madrid" } to backend
```

### Why `/la-liga-chat` Is Its Own Page (Not Mixed into `/chat`)

The original `/chat` page uses `LeagueProvider.clubsForLeague` — a context value populated by an async fetch to `/api/v1/leagues`. During the 200-400ms before that fetch completes, `clubsForLeague` is empty and the component falls back to `getClubs()`, which returns PL clubs. If the user clicked quickly, they'd select an Arsenal card even while thinking they were choosing a La Liga club.

The dedicated page eliminates this entirely: the 6 clubs are **in the source code**, not fetched. The `handleClubSelect` function also validates against the hardcoded list before committing.

---

## How to Add the Remaining 14 La Liga Clubs

The league config already lists all 20 clubs. Six have full JSON knowledge files. To add the remaining 14, follow these steps:

### Step 1: Identify Which Clubs to Add

The 14 clubs already in `league_config.json` but without club JSON files:

| Club ID | Display Name | Division Region | API ID |
|---------|-------------|-----------------|--------|
| `real_betis` | Real Betis | Andalusian | 90 |
| `real_sociedad` | Real Sociedad | Basque | 92 |
| `villarreal` | Villarreal | Valencian | 94 |
| `getafe` | Getafe CF | Castilian | 298 |
| `celta_vigo` | Celta Vigo | Galician | 558 |
| `osasuna` | CA Osasuna | Navarrese | 727 |
| `rayo_vallecano` | Rayo Vallecano | Castilian | 87 |
| `mallorca` | RCD Mallorca | Balearic | 798 |
| `girona` | Girona FC | Catalan | 298 |
| `espanyol` | RCD Espanyol | Catalan | 80 |
| `deportivo_alaves` | Deportivo Alavés | Basque | 263 |
| `leganes` | CD Leganés | Castilian | 745 |
| `valladolid` | Real Valladolid | Castilian | 250 |
| `las_palmas` | UD Las Palmas | Canarian | 275 |

### Step 2: Create the Club JSON File

For each club, create `Leagues/La_Liga/clubs/{club_id}.json`.

**Copy this template and fill in the blanks:**

```json
{
  "id": "real_betis",
  "display_name": "Real Betis",
  "sport": "football",
  "league_id": "la_liga",
  "voice_description": "Passionate Bético — the working-class soul of Seville. We live and die for Real Betis. Manuel Pellegrini gave us glory. Vamos mi Betis.",

  "dialect": {
    "replacements": {
      "good": "de lujo",
      "great": "bestial",
      "mate": "chaval"
    },
    "phrases": [
      "¡Viva el Betis manque pierda!",
      "Béticos somos, Béticos seremos.",
      "El Villamarín es una fiesta."
    ],
    "vocab_inject": "Speak with warm Andalusian passion. Use 'chaval', 'ole' for flair. Reference the Betis identity — working-class heart, proud rivals of Sevilla. 'Viva el Betis manque pierda' (Long live Betis even if we lose) — that phrase defines our soul."
  },

  "legends": [
    {
      "name": "Joaquín Sánchez",
      "era": "2002-2023",
      "story": "Mr Betis himself. The most beloved Bético of all time, a local boy who spent most of his career here and led the club to Europa League glory.",
      "achievements": ["Copa del Rey 2005", "Europa League 2022"],
      "fan_nickname": "El Niño"
    }
  ],

  "iconic_moments": [
    {
      "title": "Copa del Rey 2022 — First Title in 25 Years",
      "date": "2022-04-23",
      "opponent": "Valencia",
      "score": "1-1 (5-4 pens)",
      "emotion": "euphoric",
      "significance": "First Copa in 25 years. Joaquín lifted the trophy. The whole city wept."
    }
  ],

  "biggest_tragedies": [],

  "rivalries": {
    "sevilla": {
      "intensity": 1.0,
      "name": "Gran Derbi de Andalucía",
      "banter": [
        "Sevilla think they own this city. They don't.",
        "The Gran Derbi is more than a match — it's a way of life."
      ]
    }
  },

  "coaches": [
    {
      "name": "Manuel Pellegrini",
      "era": "2020-present",
      "achievements": ["Europa League QF 2022", "Copa del Rey 2022"]
    }
  ],

  "stadium": {
    "name": "Estadio Benito Villamarín",
    "capacity": 60721,
    "atmosphere_note": "One of the loudest stadiums in Spain during derbis."
  }
}
```

**Research tips for each club**:
- Wikipedia for legends, stadium capacity, Copa del Rey history
- FBref.com for historical managers and trophy lists
- For rivalries, look up the derby name + typical intensity
- For dialect: Andalusian → chaval, ole; Basque → aupa, kaixo; Galician → neutral/Portuguese-influenced; Catalan → Visca, tío; Canarian → guanche references

### Step 3: Add the Club Palette to `frontend/src/config/clubThemes.ts`

Find the `CLUB_PALETTES` object and add an entry:

```typescript
// Real Betis — green/white
real_betis: {
  primary: '#00A650',
  secondary: '#FFFFFF',
  gradient: 'linear-gradient(135deg, #00A65015, #00A65030)',
  textOnPrimary: '#FFFFFF',
},

// Real Sociedad — blue/white
real_sociedad: {
  primary: '#003DA5',
  secondary: '#FFFFFF',
  gradient: 'linear-gradient(135deg, #003DA515, #003DA530)',
  textOnPrimary: '#FFFFFF',
},

// Villarreal — yellow
villarreal: {
  primary: '#FFD700',
  secondary: '#004F9F',
  gradient: 'linear-gradient(135deg, #FFD70015, #FFD70030)',
  textOnPrimary: '#004F9F',
},

// Celta Vigo — sky blue
celta_vigo: {
  primary: '#75AADB',
  secondary: '#FFFFFF',
  gradient: 'linear-gradient(135deg, #75AADB15, #75AADB30)',
  textOnPrimary: '#FFFFFF',
},

// Espanyol — blue/white diagonal
espanyol: {
  primary: '#005B9F',
  secondary: '#FFFFFF',
  gradient: 'linear-gradient(135deg, #005B9F15, #005B9F30)',
  textOnPrimary: '#FFFFFF',
},
```

Add similar entries for the remaining clubs. Use the club's official kit colours.  
Reference: [Wikipedia category: La Liga clubs](https://en.wikipedia.org/wiki/La_Liga) — each club article has a colour infobox.

### Step 4: Add Stadium Info to `LaLigaChat.tsx`

The `LA_LIGA_CLUBS` array in `frontend/src/pages/LaLigaChat.tsx` has the 6 MVP entries. Expand it:

```typescript
const LA_LIGA_CLUBS: LaLigaClub[] = [
  // ... existing 6 clubs ...

  // ADD: Remaining 14
  {
    id: 'real_betis',
    displayName: 'Real Betis',
    stadium: 'Estadio Benito Villamarín',
    city: 'Seville',
    tagline: '¡Viva el Betis manque pierda!',
  },
  {
    id: 'real_sociedad',
    displayName: 'Real Sociedad',
    stadium: 'Reale Arena',
    city: 'San Sebastián',
    tagline: 'Basque identity. La Real.',
  },
  {
    id: 'villarreal',
    displayName: 'Villarreal CF',
    stadium: 'Estadio de la Cerámica',
    city: 'Villarreal',
    tagline: 'The Yellow Submarine. Europa League champions.',
  },
  {
    id: 'getafe',
    displayName: 'Getafe CF',
    stadium: 'Coliseum Alfonso Pérez',
    city: 'Getafe',
    tagline: 'Madrid\'s fighting spirit. Geta carajo.',
  },
  {
    id: 'celta_vigo',
    displayName: 'Celta Vigo',
    stadium: 'Estadio de Balaídos',
    city: 'Vigo',
    tagline: 'Galician soul. Always fight.',
  },
  {
    id: 'osasuna',
    displayName: 'CA Osasuna',
    stadium: 'El Sadar',
    city: 'Pamplona',
    tagline: 'Navarrese pride. Aupa Osasuna.',
  },
  {
    id: 'rayo_vallecano',
    displayName: 'Rayo Vallecano',
    stadium: 'Campo de Fútbol de Vallecas',
    city: 'Madrid',
    tagline: 'Working class. Red belt. Always proud.',
  },
  {
    id: 'mallorca',
    displayName: 'RCD Mallorca',
    stadium: 'Visit Mallorca Estadi',
    city: 'Palma',
    tagline: 'Island pride. Visca Mallorca.',
  },
  {
    id: 'girona',
    displayName: 'Girona FC',
    stadium: 'Estadio Municipal de Montilivi',
    city: 'Girona',
    tagline: 'Catalan underdogs. Força Girona.',
  },
  {
    id: 'espanyol',
    displayName: 'RCD Espanyol',
    stadium: 'RCDE Stadium',
    city: 'Barcelona',
    tagline: 'Barcelona\'s other club. Periquito.',
  },
  {
    id: 'deportivo_alaves',
    displayName: 'Deportivo Alavés',
    stadium: 'Estadio de Mendizorroza',
    city: 'Vitoria-Gasteiz',
    tagline: 'Basque heart. Aupa Glorioso.',
  },
  {
    id: 'leganes',
    displayName: 'CD Leganés',
    stadium: 'Estadio Municipal de Butarque',
    city: 'Leganés',
    tagline: 'South Madrid. Pépineros.',
  },
  {
    id: 'valladolid',
    displayName: 'Real Valladolid',
    stadium: 'Estadio José Zorrilla',
    city: 'Valladolid',
    tagline: 'Castile and León. Corazón Pucela.',
  },
  {
    id: 'las_palmas',
    displayName: 'UD Las Palmas',
    stadium: 'Estadio Gran Canaria',
    city: 'Las Palmas',
    tagline: 'Canary Islands. Orgullo canario.',
  },
]
```

### Step 5: Sync to Home Directory

After editing frontend files, always sync to the running Vite instance:

```bash
HOME="$HOME/soccer-ai-frontend/src"
SRC="/storage/emulated/0/Download/synthesis-rules/soccer-AI/frontend/src"

cp "$SRC/pages/LaLigaChat.tsx" "$HOME/pages/LaLigaChat.tsx"
cp "$SRC/config/clubThemes.ts" "$HOME/config/clubThemes.ts"
```

### Step 6: Restart the Backend (If Adding New Club JSONs)

`league_loader.py` runs at import time. For new club JSON files to be picked up, the backend must restart:

```bash
# In the backend terminal, Ctrl+C then:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Or send SIGHUP to the uvicorn process — `--reload` mode will detect the new files in the Leagues/ directory.

### Step 7: Verify

```bash
# Test new club persona
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about your biggest derby", "club_id": "real_betis"}'

# Check mood is computed
curl http://localhost:8000/api/v1/fan/real_betis/mood

# Check leagues API returns all 20 clubs
curl http://localhost:8000/api/v1/leagues | python3 -c "
import sys,json; d=json.load(sys.stdin)
ll = next(l for l in d['data'] if l['competition_code']=='PD')
print(f'La Liga clubs: {ll[\"club_count\"]}')
"
```

---

## How Moods Work (Already Automatic)

No extra steps needed for moods — they are **computed automatically** from match results.

The pipeline:

1. `backend/scripts/refresh_season_data.py` polls `football-data.org` every 6 hours
2. It stores form strings (`WWDLL`) in the standings cache
3. `fan_enhancements.calculate_mood_from_results()` maps form → mood state:

| Form Pattern | Mood |
|-------------|------|
| 4-5 wins | `euphoric` |
| 3 wins | `confident` |
| Mixed W/D | `steady` |
| Mixed L/D | `anxious` |
| 4-5 losses | `despairing` |
| Many draws | `frustrated` |

4. For La Liga clubs, form data comes from `?competition=PD` API calls

**The only requirement**: La Liga clubs must be in the backend's `VALID_CLUBS` set (they are, since `league_loader.py` loads all 40 clubs dynamically).

---

## How Rivalries Work — Adding or Strengthening

Rivalries are defined in each club's JSON file under the `rivalries` key. The backend reads them via `league_loader.RIVALRIES`.

**Structure:**

```json
"rivalries": {
  "opponent_club_id": {
    "intensity": 0.95,
    "name": "Derby Name",
    "banter": [
      "Banter line 1 the persona might say",
      "Banter line 2"
    ]
  }
}
```

**Intensity scale** (controls how the AI responds):

| Intensity | Behavior |
|-----------|----------|
| `1.0` | Blood rivalry — contempt, tribal pride, zero neutrality |
| `0.9` | Deep hatred — dismissive, can't say a good word |
| `0.8` | Strong rivalry — clear disdain, backhanded compliments |
| `0.7` | Serious rivalry — cheeky banter, some respect |
| `< 0.7` | Minor rivalry — gentle ribbing |

**To strengthen an existing rivalry**: edit the club's JSON file, increase intensity, add more banter lines, restart backend.

**To add a new rivalry**: add the entry to BOTH clubs' JSON files (the relationship should be mutual).

**Example**: To add the Derbi de la Comunitat (Valencia vs Villarreal):

In `Leagues/La_Liga/clubs/valencia.json`:
```json
"rivalries": {
  "villarreal": { "intensity": 0.80, "name": "Derbi de la Comunitat", "banter": ["Yellow Submarine? More like a yellow bath toy."] }
}
```

In `Leagues/La_Liga/clubs/villarreal.json` (once created):
```json
"rivalries": {
  "valencia": { "intensity": 0.80, "name": "Derbi de la Comunitat", "banter": ["Valencia fans forget we beat them to a Europa League title."] }
}
```

---

## How to Add Legends

Legends are defined in `legends` array in the club JSON. They are loaded into the KG by `Leagues/extractors/build_kg.py` and injected into the system prompt as persona context.

**Minimum data per legend:**

```json
{
  "name": "David Villa",
  "era": "2003-2010",
  "story": "El Guaje — the greatest scorer in Spanish football history at the time. Born to score, El Guaje defined a golden era at Valencia and went on to win everything with Spain.",
  "achievements": ["2004 La Liga with Valencia", "2010 World Cup Golden Boot (Spain)", "2008 Euro with Spain"],
  "fan_nickname": "El Guaje"
}
```

After editing, run the KG builder to update the graph database:

```bash
cd /storage/emulated/0/Download/synthesis-rules/soccer-AI
python3 Leagues/extractors/build_kg.py --league la_liga
```

---

## How to Add Iconic Moments

Iconic moments define the club's emotional history — what a fan will reference in conversation with joy or pain.

```json
{
  "title": "2001 Champions League Final — Heartbreak in Milan",
  "date": "2001-05-23",
  "opponent": "Bayern Munich",
  "score": "1-1 (5-4 pens — Valencia lost)",
  "emotion": "tragic",
  "significance": "Valencia were the best team in Europe for two years. They reached back-to-back UCL finals and lost both. That pain defines a generation of Valencianistas."
}
```

**Emotion values**: `euphoric`, `triumphant`, `iconic`, `tragic`, `bittersweet`

---

## How to Add Regional Dialect Flavour

The `dialect` block controls three layers of voice injection:

```json
"dialect": {
  "replacements": {
    "good": "de lujo",
    "great": "bestial",
    "mate": "chaval"
  },
  "phrases": [
    "¡Viva el Betis manque pierda!",
    "El Villamarín nunca duerme."
  ],
  "vocab_inject": "Free-text instruction to the AI about voice and register. This is injected directly into the system prompt. Be specific: tell the AI what expressions to use, what cultural references to make, what posture to take (proud, humble, defiant, working-class)."
}
```

**By region:**

| Region | Clubs | Key phrases | `vocab_inject` guidance |
|--------|-------|------------|------------------------|
| Castilian | Real Madrid, Atletico, Getafe, Rayo, Leganes, Valladolid | ¡Vamos!, tío, bestial, brutal | Standard Spanish passion, direct, proud |
| Catalan | Barcelona, Girona, Espanyol | Visca!, tío, Barça, Camp Nou | Weave in Catalan pride, La Masia, Catalan identity, "Més que un club" |
| Basque | Athletic Bilbao, Real Sociedad, Alavés | Aupa!, Euskadi, kaixo, cantera | Basque pride and identity, cantera philosophy, community identity |
| Andalusian | Sevilla, Real Betis | ¡Ole!, chaval, mi Sevilla, mi Betis | Warm southern energy, expressive, passionate, proud of local identity |
| Valencian | Valencia, Villarreal | Amunt!, che, Mestalla | Valencian community pride, 'Amunt' for rallying, 'che' as local address |
| Galician | Celta Vigo | ¡Vamos!, Galicia, Portuguese-adjacent | Celtic influence, proud Atlantic identity, fighting spirit |
| Canarian | Las Palmas | Orgullo canario, islas | Island pride, distinctly non-mainland, sunny passion |
| Balearic | Mallorca | Visca Mallorca, illes | Island and Catalan-influenced identity |

---

## Future Enhancements for La Liga

Once all 20 clubs are complete, these features add significant depth:

### 1. El Clásico Prediction Integration
When a Barcelona or Real Madrid fan asks about an upcoming Clásico, the chat should automatically pull Dixon-Coles prediction data (`GET /api/v1/predict/v2/real_madrid/barcelona`) and weave it into the response.

Already works for PL clubs — just needs the SP1 Dixon-Coles model to be validated.

### 2. La Liga Standings Page
`/standings` currently shows PL only. Add `?competition=PD` parameter:

```typescript
// frontend/src/pages/Standings.tsx
const { competition } = useLeague()
const data = await getStandings(competition)
```

The backend already supports `?competition=PD` on the standings endpoint.

### 3. La Liga Trivia
`backend/scripts/generate_trivia.py` accepts a `--division` parameter. Run:
```bash
python3 backend/scripts/generate_trivia.py --division SP1
```
This generates trivia questions from SP1 match history — 9,008 matches of data.

### 4. La Liga Live Match Companion
The `/companion` page runs simulations against PL clubs. Adding La Liga means:
- Using `?competition=PD` in fixture calls
- Adding La Liga match simulations to `live_companion.py`

### 5. Fan Debate — La Liga Edition
`POST /api/v1/debate` already accepts any two clubs. The debate endpoint will work for La Liga clubs immediately once their personas are loaded. Add a "La Liga rivalries" preset to the debate UI.

---

## Verified Working

| Feature | Tested | Result |
|---------|--------|--------|
| Real Madrid persona (`club_id: "real_madrid"`) | ✓ | Spanish castilian voice, ¡Hala Madrid!, mentions Bernabéu, European Cups |
| Barcelona persona (`club_id: "barcelona"`) | ✓ | Mentions 2011, Messi, Visca el Barça, Catalan pride |
| Both via `club_id` field (not `club`) | ✓ | Models.py `get_club()` method resolves both fields |
| Stream endpoint uses `get_club()` | ✓ | Fixed in main.py line 459 |
| La Liga route `/la-liga-chat` | ✓ | Page renders, navigation entry visible |
| Mood badges on La Liga club cards | ✓ | Fetches from `/api/v1/fan/{club_id}/mood` |
| VALID_CLUBS includes La Liga clubs | ✓ | Built dynamically from `league_loader.CLUB_DISPLAY_NAMES` |

---

## Files Changed in This MVP

### New Files
- `Leagues/La_Liga/league_config.json` — 20-club La Liga config
- `Leagues/La_Liga/clubs/real_madrid.json` — Full persona
- `Leagues/La_Liga/clubs/barcelona.json` — Full persona
- `Leagues/La_Liga/clubs/atletico_madrid.json` — Full persona
- `Leagues/La_Liga/clubs/sevilla.json` — Full persona
- `Leagues/La_Liga/clubs/athletic_bilbao.json` — Full persona
- `Leagues/La_Liga/clubs/valencia.json` — Full persona
- `backend/league_loader.py` — Dynamic multi-league loader
- `frontend/src/pages/LaLigaChat.tsx` — Isolated La Liga chat UI
- `frontend/src/config/runtimeConfig.ts` — Runtime-mutable API URL + debug flags
- `frontend/src/components/Config/ConfigDrawer.tsx` — Left-edge settings drawer
- `future-SaaS-vision.md` — Product vision document

### Modified Files
- `backend/main.py` — Dynamic VALID_CLUBS, `get_club()` on both chat endpoints, multi-league endpoints
- `backend/models.py` — Added `club_id` field + `get_club()` to ChatRequest
- `backend/config.py` — Uses league_loader instead of hardcoded dicts
- `backend/fan_enhancements.py` — Dynamic RIVALRIES + DIALECTS from league_loader
- `backend/persona_bridge.py` — League-aware `_get_base_prompt()` (Spanish voice for La Liga)
- `backend/live_football_provider.py` — Competition-aware API calls
- `backend/football_api.py` — `competition` param on fixture/results methods
- `frontend/src/routes/index.tsx` — Added `/la-liga-chat` route
- `frontend/src/components/Layout/Navigation.tsx` — LA LIGA nav entry + LeagueSwitcher
- `frontend/src/components/Chat/ClubSelection.tsx` — LeagueTabBar, La Liga clubs
- `frontend/src/config/clubThemes.ts` — 6 La Liga club palettes
- `frontend/src/config/LeagueProvider.tsx` — Fetches leagues from backend, persists to localStorage
- `frontend/src/services/api.ts` — Uses runtimeConfig.apiUrl instead of hardcoded URL

---

*The concept is proven. The architecture scales. Add data — get a new persona.*
