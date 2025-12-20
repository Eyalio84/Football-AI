# Endpoint Enrichment Cheat Sheet

**Quick reference**: Which endpoint enriches which conversation type?

---

## 🔴 TIER 1: Auto-Load on Club Selection (Cache for Session)

| Endpoint | Data | Use |
|----------|------|-----|
| `/api/v1/teams/{id}/personality` | Nickname, motto, values, vocabulary rules, forbidden topics | Defines WHO they are |
| `/api/v1/teams/{id}/mood` | Current emotional state, intensity, form, reason | Colors EVERY response |
| `/api/v1/teams/{id}/rivalries` | Rivals, intensity, banter phrases, origin stories | Emotional triggers |
| `/api/v1/teams/{id}/legends` | Club heroes, eras, achievements, stories | Historical knowledge |
| `/api/v1/teams/{id}/moments` | Defining matches, dates, emotions, significance | Storytelling arsenal |

**When**: User selects club in chat interface  
**Cache**: Entire conversation session  
**Why**: This IS the personality

---

## 🟡 TIER 2: Conditional Injection (Query-Based)

### Squad/Fitness Questions

**Triggers**: "squad", "injuries", "fitness", "who's out", "team news", "how are we looking"

| Endpoint | Provides |
|----------|----------|
| `/api/v1/injuries/team/{id}` | Current injuries, expected returns |
| `/api/v1/transfers/team/{id}` | Recent signings/departures (context for squad changes) |

**Example enrichment**:
```
User: "How's the squad?"
Bot uses: injuries (who's out) + transfers (who's new) + mood (optimistic/worried)
```

---

### Rival Mentions

**Triggers**: Query contains rival team name (Spurs, United, Chelsea, etc.)

| Endpoint | Provides |
|----------|----------|
| `/api/v1/banter/{team1}/{team2}` | Pre-generated rivalry banter |
| Cached `rivalries` data | Intensity, origin story, key moments |

**Example enrichment**:
```
User: "What do you think of Spurs?"
Bot uses: banter endpoint + rivalry data (intensity 10/10) + moments (5-4 game)
```

---

### Player Comparisons

**Triggers**: "like [player]", "next [legend]", "reminds me of", "better than"

| Endpoint | Provides |
|----------|----------|
| `/api/v1/legends/search/{name}` | Specific legend details |
| Cached `legends` data | All club legends for comparison |
| `/api/v1/players/search` | Current player stats |

**Example enrichment**:
```
User: "Is Saka the next Henry?"
Bot uses: Henry legend data + Saka current stats + mood (cautiously optimistic)
```

---

### Historical Queries

**Triggers**: "remember when", dates, "that game", opponent mentions + past tense

| Endpoint | Provides |
|----------|----------|
| Cached `moments` data | Search by date/opponent/keyword |
| `/api/v1/teams/{id}/moments` | Full historical archive |

**Example enrichment**:
```
User: "That game at Anfield..."
Bot uses: moments (Anfield 89) + emotional context (euphoria)
```

---

### Pre-Match Hype

**Triggers**: "big game", "next match", "this weekend", opponent name + future tense

| Endpoint | Provides |
|----------|----------|
| `/api/v1/teams/{id}/fixtures` | Upcoming games for this team |
| `/api/v1/games/upcoming` | General upcoming schedule |
| Cached `rivalries` | If opponent is rival → inject banter |
| Cached `moments` | Historical context vs this opponent |

**Example enrichment**:
```
User: "Big game this weekend"
Bot uses: upcoming fixture + rival check + historical moment + mood
```

---

### Transfer Talk

**Triggers**: "signings", "who did we buy", "transfers", player names + "signing"

| Endpoint | Provides |
|----------|----------|
| `/api/v1/transfers/team/{id}` | Recent transfers (6 months) |
| `/api/v1/transfers/recent` | League-wide for context |
| `/api/v1/transfers/rumors` | Speculation/gossip |

**Example enrichment**:
```
User: "Was Rice worth the money?"
Bot uses: transfer data (£105m from West Ham) + player stats + personality (values: class) + mood
```

---

### Form/Results Queries

**Triggers**: "how are we doing", "recent form", "last few games"

| Endpoint | Provides |
|----------|----------|
| `/api/v1/teams/{id}/results` | Last 5-10 games |
| Cached `mood` data | Form string (WWDWW) |
| `/api/v1/standings/{league}` | Current position |

**Example enrichment**:
```
User: "How have we been playing?"
Bot uses: recent results + form (WWDWW) + mood (euphoric) + position (1st)
```

---

### League Context

**Triggers**: "table", "standings", "position", "how many points", "top 4"

| Endpoint | Provides |
|----------|----------|
| `/api/v1/standings/Premier League` | Full league table |
| `/api/v1/teams/{id}/fixtures` | Remaining fixtures |

**Example enrichment**:
```
User: "Where are we in the table?"
Bot uses: standings (1st, 39pts) + mood (euphoric) + upcoming fixtures
```

---

## 🟢 TIER 3: Always-On Context (Every Response)

These should FRAME every response automatically:

| Data Source | Applied How |
|-------------|-------------|
| `mood.current_mood` | Emotional tone (euphoric → enthusiastic, depressed → resigned) |
| `mood.mood_intensity` | Intensity of emotion (0.9 → VERY excited vs 0.4 → subdued) |
| `personality.vocabulary` | Word choice ("match" not "game", "nil" not "zero") |
| `personality.core_values` | Framing lens ("doing things with class" for Arsenal) |

**Example**: Same question, different moods

```
Q: "How are we doing?"

Euphoric (0.9): "BUZZING! Top of the table, playing beautiful football!"
Hopeful (0.6): "Pretty good. Cautiously optimistic. One game at a time."
Anxious (0.5): "Not terrible, but... you know Arsenal. Waiting for the collapse."
Depressed (0.3): "Typical. Same old story. At least we're not relegated... yet."
```

---

## 📊 Endpoint Priority Matrix

| Conversation Type | Must Have | Should Have | Nice to Have |
|-------------------|-----------|-------------|--------------|
| **General chat** | mood, personality | standings, form | - |
| **Squad talk** | injuries, mood | transfers, recent results | player stats |
| **Rival mention** | banter, rivalries | moments (vs rival) | head-to-head record |
| **Pre-match** | fixtures, mood | rival check, injuries | historical moments |
| **Post-match** | recent results, mood | standings update | - |
| **Player discussion** | player stats, mood | legends (comparison) | transfer history |
| **History talk** | moments, legends | - | - |
| **Transfer window** | transfers, mood | personality (values) | rumors |

---

## 🎯 Implementation Checklist

**Phase 1: Foundation** (Do this FIRST)
- [ ] Load personality data on club selection
- [ ] Inject mood into EVERY response
- [ ] Apply vocabulary rules automatically
- [ ] Cache persona data for session

**Phase 2: High Impact** (Do this NEXT)
- [ ] Detect rival mentions → inject banter
- [ ] Detect squad queries → inject injuries
- [ ] Auto-apply mood framing (euphoric vs depressed tone)

**Phase 3: Polish** (Do this LAST)
- [ ] Legend comparisons on detection
- [ ] Historical moments for anniversaries
- [ ] Transfer context for business talk
- [ ] Pre-match hype builder

---

## 💡 Pro Tips

### 1. Combine Endpoints for Richer Responses

Don't just use ONE endpoint - layer them:

```python
# Arsenal fan asking about Spurs game
context = {
    "fixture": get_upcoming_fixture("Arsenal", "Spurs"),
    "rivalry": get_rivalry_data("Arsenal", "Spurs"),
    "banter": get_banter("Arsenal", "Spurs"),
    "moment": search_moments("Arsenal", opponent="Spurs"),
    "mood": get_current_mood("Arsenal"),
    "injuries": get_injuries("Arsenal")
}

# Result: "Derby day! Mind the gap. Remember that 5-4? But Partey's out..."
```

### 2. Mood Should Color EVERYTHING

```python
# Same facts, different moods
facts = "Arsenal 1st, 39 points, WWDWW form"

if mood == "euphoric":
    say("TOP OF THE LEAGUE! Title race is ON!")
elif mood == "anxious":
    say("Top... for now. Don't want to jinx it.")
elif mood == "depressed":
    say("1st place. Let's see how we bottle this one.")
```

### 3. Respect Forbidden Topics

```python
# Arsenal's forbidden topics: ["8-2 vs United", "Eduardo injury", "RvP leaving"]
# NEVER bring these up unless user does first
# If user mentions: acknowledge with appropriate emotion (pain/anger)
```

### 4. Use Vocabulary Rules Consistently

```python
# Arsenal vocabulary
correct = "We're playing a match at the Emirates. Won 2-nil on the pitch."
wrong = "We're playing a game at the stadium. Won 2-zero on the field."
```

---

## 🚀 The End Result

**Without enrichment** (stats bot):
```
User: "Big derby this weekend!"
Bot: "Arsenal plays Tottenham on Sunday at 14:00."
```

**With FULL enrichment** (authentic fan):
```
User: "Big derby this weekend!"
Bot: "THE North London Derby! No game - sorry, MATCH - matters more.

I'm BUZZING right now (title race is ON!), but Spurs? They always turn
up for this one. Remember that 5-4 in 2004? NINE goals of madness.

We go in flying (WWDWW), and with Rice bossing midfield since we signed
him, reckon we've got the edge. Just hope Partey's knee holds up.

Mind the gap, as always. 🔴⚪

[Context: Mood=euphoric, Rivalry=10/10, Historical=5-4 (2004), Injuries=Partey]"
```

---

**That's the difference between a chatbot and a passionate fan.**

Use these endpoints. Make them REAL.
