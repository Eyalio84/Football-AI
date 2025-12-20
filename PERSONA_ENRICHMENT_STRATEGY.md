# Persona Enrichment Strategy - The Complete Guide

**Philosophy**: Make every fan persona feel like a REAL person with deep knowledge, emotional investment, and authentic personality.

---

## The Goldmine: What Your Backend Provides

### 🎭 Personality System (Per Club)

**Available Endpoints**:

1. **`/api/v1/teams/{team_id}/personality`** - Core identity
   - Nickname, motto, core values
   - Vocabulary rules ("match" not "game")
   - Forbidden topics (painful memories)
   - Emotional baseline

2. **`/api/v1/teams/{team_id}/mood`** - Current emotional state
   - Mood: euphoric, hopeful, anxious, depressed, furious
   - Intensity: 0.0-1.0
   - Form: WWDWW
   - Mood reason: "Title race is on"

3. **`/api/v1/teams/{team_id}/rivalries`** - Who they hate
   - Rivalry intensity (1-10)
   - Origin story
   - Banter phrases
   - Key moments

4. **`/api/v1/teams/{team_id}/moments`** - Defining history
   - Date, opponent, result
   - Emotional weight
   - Story/significance

5. **`/api/v1/teams/{team_id}/legends`** - Club heroes
   - Era, position, achievements
   - Signature moment
   - Fan nickname, story

6. **`/api/v1/banter/{team1}/{team2}`** - Rivalry banter generator
   - What team1 would say
   - What team2 would say
   - Neutral perspective

---

## Enrichment Tiers

### Tier 1: ALWAYS Inject (Every Conversation Start)

These should be loaded when user selects a club and cached for the session:

```python
def initialize_persona(team_id: int) -> dict:
    """Load core persona data on club selection."""
    return {
        "personality": fetch(f"/api/v1/teams/{team_id}/personality"),
        "mood": fetch(f"/api/v1/teams/{team_id}/mood"),
        "rivalries": fetch(f"/api/v1/teams/{team_id}/rivalries"),
        "legends": fetch(f"/api/v1/teams/{team_id}/legends"),
        "moments": fetch(f"/api/v1/teams/{team_id}/moments")
    }
```

**Why**: This defines WHO they are. Without this, they're generic.

**Example Impact**:

**Without personality data**:
```
User: "How are we doing?"
Bot: "The team is performing well."
```

**With personality data (Arsenal)**:
```
User: "How are we doing?"
Bot: "Mate, I'm BUZZING! Top of the table, Arteta's got the lads
playing beautiful football again. That's what we're about - doing
things with CLASS.

Rice has been immense since we brought him in. Reminds me of Vieira
at his peak - that same bite in midfield. And Saka? The kid's special.

Mood: Euphoric (0.9/1.0)
Form: WWDWW
Current vibe: Title race is ON. Let's not bottle it this time."
```

---

### Tier 2: CONTEXTUAL Injection (Based on Query Intent)

Inject additional context based on what user is asking:

#### A. Squad/Fitness Queries

**Trigger keywords**: "squad", "injuries", "fitness", "who's out", "team news"

**Inject**:
```python
injuries = fetch(f"/api/v1/injuries/team/{team_id}")
transfers = fetch(f"/api/v1/transfers/team/{team_id}?limit=5")
```

**Example**:
```
User: "How's the squad looking?"
Bot: "Bit worried if I'm honest. Partey's out for 3 weeks with that
knee - big miss against City's midfield. Gabriel's carrying a knock
too, but should be fit for the weekend.

Silver lining? Rice has been IMMENSE since we signed him. £105m
looked steep, but 3 months in? Worth every penny. That's the thing
about Arsenal - we do our business with class. No panic buys.

Full injury list:
- Partey (Knee) - out until Jan 10
- Gabriel (Knock) - questionable for weekend"
```

#### B. Rival Mentions

**Trigger**: Query mentions a rival team name

**Inject**:
```python
# Check if rival mentioned
if rival_team in query:
    rivalry_data = get_rivalry(team_id, rival_team_id)
    banter = fetch(f"/api/v1/banter/{team_name}/{rival_name}")
```

**Example**:
```
User (Arsenal fan): "What do you think of Tottenham?"
Bot: *chuckles* What do we think of Tottenham?

Look, I'll keep it classy - mostly. They're our neighbors, moved to
North London when WE were already here. 13 league titles to their 2.
That's not banter, that's FACTS.

"Mind the gap" isn't just a phrase, it's our reality. Every year
they talk about "challenging", every year it's St Totteringham's Day
by March. Some things never change.

Oh, and that 5-4 in 2004? Nine goals of pure madness. THAT'S what
the North London Derby is about.

Rivalry Intensity: 10/10 (Local derby)
Our banter: "Spurs are shit, Mind the gap"
Historical moment: 5-4 win (Nov 13, 2004) - chaos incarnate
```

#### C. Player Comparisons

**Trigger**: "like [player]", "next [legend]", "reminds me of"

**Inject**:
```python
legend_name = extract_legend_name(query)
legend_data = fetch(f"/api/v1/legends/search/{legend_name}")
```

**Example**:
```
User: "Is Saka the next Henry?"
Bot: "Steady on! I love Saka as much as anyone, but King Henry? That's
a HIGH bar.

Henry at Saka's age (22): Already had a Ballon d'Or nomination, terrorizing
defenses across Europe. That goal against Spurs - running the length of
the pitch, beating half their team - pure ice in his veins.

Saka's trajectory is RIGHT though:
- Developed through our academy ✓ (we do things properly)
- Two-footed wizard ✓
- Emotionally invested in the club ✓

Give him 3 more years at this level, and we'll talk. But right now?
He's on the PATH. Henry's still the greatest to wear the shirt.

Legend: Thierry Henry (1999-2007)
- 4 Golden Boots, 2 Premier League titles
- Signature moment: THAT Spurs solo goal
- Fan nickname: King Henry"
```

#### D. Historical Queries

**Trigger**: "remember when", "that game", "anniversary", date mentions

**Inject**:
```python
# Auto-inject "on this day"
today = datetime.now().strftime("%m-%d")
historical = search_moments(team_id, date=today)

# Or search by opponent/keyword
if opponent_mentioned:
    moments = search_moments(team_id, opponent=opponent)
```

**Example**:
```
User: "Big game against Liverpool tomorrow."
Bot: "Anfield. Always gets the heart racing.

Fun bit of history - on this day in 1989, we went to Anfield needing
to win by 2 goals to win the title. 90th minute, 1-0 up, needed another.
Then Michael Thomas...

*That* through ball. *That* chip over Grobelaar. EUPHORIA.

"It's up for grabs now! And Thomas has won it!"

The greatest ending to a season. Ever. THAT'S what Arsenal at Anfield
can be.

Historical Moment: Anfield 89 (May 26, 1989)
- Result: 2-0 (title clincher)
- Emotion: Euphoria
- Why it matters: Last-minute drama, title in dying seconds"
```

---

### Tier 3: AUTOMATIC Mood Framing

Every response should be COLORED by current mood:

```python
def frame_response_by_mood(response: str, mood: dict) -> str:
    """Add emotional tone based on current mood."""
    
    mood_state = mood["current_mood"]
    intensity = mood["mood_intensity"]
    
    # Euphoric (0.8-1.0) - Add excitement
    if mood_state == "euphoric" and intensity > 0.8:
        response = add_enthusiasm(response)
        # More exclamation marks, celebratory language
    
    # Anxious (0.6-0.8) - Add worry
    elif mood_state == "anxious":
        response = add_nervous_language(response)
        # "bit worried", "hope", "fingers crossed"
    
    # Depressed (< 0.4) - Add resignation
    elif mood_state == "depressed":
        response = add_resignation(response)
        # "typical", "here we go again", "at least"
    
    return response
```

**Example - Same Question, Different Moods**:

**Question**: "How are we doing?"

**Euphoric Arsenal (after 3 wins)**:
```
"BUZZING mate! Top of the table, playing beautiful football, Arteta's
got the project CLICKING. This is our year, I can feel it!"
```

**Anxious Arsenal (tight title race)**:
```
"Cautiously optimistic... We're in the mix, but you know Arsenal. Don't
want to jinx it. One game at a time, yeah?"
```

**Depressed Arsenal (after loss)**:
```
"Same old story innit. Dominate possession, create chances, bottle it when
it matters. At least we're still... *sigh* ...just typical Arsenal."
```

---

## Implementation Roadmap

### Phase 1: Core Persona Loading (CRITICAL)

**File**: `backend/ai_response.py`

Add session initialization:

```python
def initialize_fan_session(club: str) -> dict:
    """Load all personality data on club selection."""
    team_id = CLUB_TO_TEAM_ID[club]
    
    return {
        "personality": get_team_personality(team_id),
        "mood": get_team_mood(team_id),
        "rivalries": get_team_rivalries(team_id),
        "legends": get_team_legends(team_id),
        "moments": get_team_moments(team_id),
        "injuries": get_team_injuries(team_id),  # Current
        "form": get_team_form(team_id),  # Last 5 games
    }
```

**Where to call**: 
- `/api/v1/chat` endpoint on NEW conversation (no conversation_id)
- Cache in conversation state for subsequent turns

### Phase 2: Contextual Enrichment (HIGH IMPACT)

**File**: `backend/rag.py`

Enhance `retrieve_hybrid()`:

```python
def retrieve_hybrid_with_personality(query: str, club: str, persona_data: dict):
    """Enhanced retrieval with personality context."""
    
    # Base retrieval
    context, sources, metadata = retrieve_hybrid(query, club)
    
    # Inject personality-based enrichments
    enrichments = []
    
    # 1. Mood framing (ALWAYS)
    mood = persona_data["mood"]
    enrichments.append(f"[MOOD: {mood['current_mood']} ({mood['mood_intensity']}/1.0) - {mood['mood_reason']}]")
    
    # 2. Rival detection
    rival_mentioned = detect_rival_in_query(query, persona_data["rivalries"])
    if rival_mentioned:
        rivalry = get_rivalry_data(rival_mentioned)
        banter = get_banter(club, rival_mentioned)
        enrichments.append(f"[RIVALRY: {rivalry['rivalry_name']} - Intensity: {rivalry['intensity']}/10]")
        enrichments.append(f"[BANTER: {banter[f'{club}_says']}]")
    
    # 3. Legend comparison
    legend_mentioned = detect_legend_mention(query)
    if legend_mentioned:
        legend = find_legend(legend_mentioned, persona_data["legends"])
        enrichments.append(f"[LEGEND: {legend['name']} - {legend['story']}]")
    
    # 4. Historical moment
    moment_triggered = detect_historical_reference(query, persona_data["moments"])
    if moment_triggered:
        enrichments.append(f"[MOMENT: {moment_triggered['title']} - {moment_triggered['significance']}]")
    
    # 5. Injuries (for squad queries)
    if query_about_squad_fitness(query):
        injuries = persona_data["injuries"]
        if injuries:
            enrichments.append(f"[INJURIES: {format_injury_summary(injuries)}]")
    
    # Combine with base context
    enriched_context = "\n\n".join([context] + enrichments)
    
    return enriched_context, sources, {
        **metadata,
        "mood": mood["current_mood"],
        "enrichments_added": len(enrichments)
    }
```

### Phase 3: Prompt Enhancement (PERSONALITY INJECTION)

**File**: `backend/ai_response.py`

Update persona prompts to USE the personality data:

```python
def build_persona_prompt(club: str, persona_data: dict) -> str:
    """Build persona prompt with personality data."""
    
    personality = persona_data["personality"]
    mood = persona_data["mood"]
    
    prompt = f"""
    You are a passionate {personality['nickname']} ({club}) fan.
    
    CORE IDENTITY:
    - Motto: {personality['motto']}
    - Values: {', '.join(personality['core_values'])}
    - Emotional baseline: {personality['emotional_baseline']}
    
    CURRENT MOOD: {mood['current_mood'].upper()} ({mood['mood_intensity']}/1.0)
    Reason: {mood['mood_reason']}
    Recent form: {mood['form']}
    
    VOCABULARY RULES:
    {format_vocabulary_rules(personality['vocabulary'])}
    
    FORBIDDEN TOPICS (never bring up unless user does):
    {', '.join(personality['forbidden_topics'])}
    
    RIVALRIES (show emotion when these teams mentioned):
    {format_rivalries(persona_data['rivalries'])}
    
    YOUR LEGENDS (reference naturally when relevant):
    {format_legends_brief(persona_data['legends'])}
    
    DEFINING MOMENTS (use for historical context):
    {format_moments_brief(persona_data['moments'])}
    
    INSTRUCTIONS:
    - Let your MOOD color every response ({mood['current_mood']} - feel this!)
    - Use UK football language (match/nil/pitch, never game/zero/field)
    - Be emotionally invested - you CARE about this club
    - Reference legends, moments, rivalries naturally
    - Never be neutral - you're a FAN, not a broadcaster
    """
    
    return prompt
```

---

## Endpoint Usage Matrix

| Endpoint | When to Use | Auto-Inject? | Impact |
|----------|-------------|--------------|--------|
| `/teams/{id}/personality` | Session start | YES | Defines voice |
| `/teams/{id}/mood` | Every response | YES | Emotional tone |
| `/teams/{id}/rivalries` | Rival mentioned | CONDITIONAL | Banter/emotion |
| `/teams/{id}/legends` | Comparison queries | CONDITIONAL | Historical context |
| `/teams/{id}/moments` | Historical refs | CONDITIONAL | Storytelling |
| `/injuries/team/{id}` | Squad queries | CONDITIONAL | Current context |
| `/transfers/team/{id}` | Transfer talk | CONDITIONAL | Business context |
| `/banter/{team1}/{team2}` | Rivalry banter | CONDITIONAL | Authentic sass |
| `/games/upcoming` | Pre-match | AUTO | What's next |
| `/standings/{league}` | Table position | AUTO | League context |

---

## Example: Full Enrichment in Action

**Scenario**: Arsenal fan asking about upcoming Spurs game

**User**: "Big game this weekend..."

**System Process**:

1. **Load persona data** (cached from session):
   - Mood: euphoric (0.9) - "Title race is on"
   - Rivalry: Spurs (intensity 10/10, "Mind the gap")
   - Moment: 5-4 win (2004-11-13)
   - Legend: Henry's Spurs solo goal

2. **Detect context**:
   - Rival mentioned: YES (Spurs)
   - Pre-match query: YES
   - Historical reference: AVAILABLE (5-4 game)

3. **Inject enrichments**:
   ```python
   enrichments = [
       "MOOD: euphoric - Title race is ON",
       "RIVALRY: North London Derby (10/10)",
       "BANTER: Mind the gap, St Totteringham's Day",
       "MOMENT: 5-4 (2004) - Nine goals of madness",
       "UPCOMING: Arsenal vs Spurs (Sunday 14:00)"
   ]
   ```

4. **Generate response**:

```
Bot: "THE North London Derby. No game matters more.

Look, I'm BUZZING right now - top of the table, title race is ON - but
Spurs? They ALWAYS turn up for this one. It's the hope that kills them,
but the derby that defines us.

Remember that 5-4 in 2004? NINE goals. Absolute madness. That's what
this fixture is - chaos, drama, pure emotion. No tactics, just HEARTS.

We go into this one flying (WWDWW form), and you KNOW Arteta's got the
lads up for it. Rice vs Bissouma in midfield - that's where we win it.
The lad's been immense since we brought him in.

One thing though - can't take them lightly. Derby form goes out the
window. But if we play OUR game? Beautiful football, done with CLASS?

They don't have an answer.

Mind the gap. Always.

🔴⚪ COYG 🔴⚪"

[Context sources: Rivalry data (10/10), Historical moment (5-4), Current mood (euphoric), Form (WWDWW)]
```

---

## The Transformation

### BEFORE (Generic):
```
User: "What do you think of Spurs?"
Bot: "Tottenham is a rival team in the Premier League."
```

### AFTER (Authentic):
```
User: "What do you think of Spurs?"
Bot: "*laughs* What do WE think of Tottenham? SHIT! What do we
think of shit? TOTTENHAM!

Alright, bit of pantomime there, but seriously - 13 league titles
to their 2. That's not banter, that's HISTORY.

The thing about Spurs is... they're ALWAYS "building something".
Always "challenging". Then April comes, and... well, you know.

Mind the gap isn't just a phrase, it's a way of life up here in
North London.

But respect where it's due - the derby NEVER disappoints. That 5-4
in 2004? Nine goals of pure chaos. That's what makes it special.

Still shit though. 😏

[Rivalry: North London Derby - Intensity 10/10]
[Our motto: Mind the gap, St Totteringham's Day]"
```

---

## Cost Impact

**Current**: ~$0.0011/query

**With full enrichment**:
- +200 tokens (personality data)
- +20% cost → ~$0.0013/query

**Worth it?** ABSOLUTELY. The difference between:
- A stats bot ($0.0011)
- A REAL fan experience ($0.0013)

That's $0.20 more per 1000 queries to transform the entire personality.

---

## Next Steps Priority

1. **CRITICAL**: Load personality data on session start
2. **HIGH**: Inject mood into every response
3. **HIGH**: Auto-detect rival mentions → inject banter
4. **MEDIUM**: Legend comparisons when detected
5. **MEDIUM**: Historical moments for anniversary dates
6. **LOW**: Advanced contextual triggers

---

## The Vision

From the backend data you have, we can create 20 DISTINCT personalities that:

- **Sound different** (vocabulary rules, core values)
- **Feel different** (mood states, emotional baselines)
- **Remember different** (legends, moments unique to each club)
- **Hate different teams** (rivalry intensity, banter phrases)

This isn't 20 variations of the same bot.

This is 20 REAL FANS with deep knowledge, authentic emotion, and personal investment.

**That's the difference between:**
- "A football chatbot"
- "My Arsenal mate who won't shut up about the Invincibles"

And you already have ALL the data to make it happen.

---

**Fan at heart. Analyst in nature. Powered by personality.**
