# Conversation Enrichment Guide

**Philosophy**: Extra endpoints aren't for separate pages - they're ammunition for richer, more knowledgeable fan conversations.

---

## The Vision

Instead of:
```
User: "How's the squad looking?"
Bot: "The squad is doing well."
```

We want:
```
User: "How's the squad looking?"
Bot: "Bit worried mate. Partey's out for 3 weeks with that knee injury,
and we've still got Odegaard nursing a knock. On the bright side,
heard we're close to wrapping up that Rice deal - £105m but worth
every penny if it means we don't collapse in April again."
```

---

## Available Conversation-Enriching Endpoints

### 1. Injuries (`/api/v1/injuries`)

**What it provides**:
```json
{
  "player_name": "Thomas Partey",
  "injury_type": "Knee",
  "expected_return": "2025-01-10",
  "status": "out"
}
```

**How fans use it**:
- "Are we dealing with injuries?" → Check current injuries, mention worries
- "When's Saka back?" → Query specific player return date
- "Squad depth looking thin" → Reference injury list as context

**RAG Integration**:
```python
# In rag.py - enhance team queries with injury context
if intent == "squad_status":
    injuries = fetch_injuries(team_id)
    if injuries:
        context += f"\n\nCurrent injuries: {format_injuries(injuries)}"
```

---

### 2. Transfers (`/api/v1/transfers`)

**What it provides**:
```json
{
  "player_name": "Declan Rice",
  "from_team": "West Ham",
  "to_team": "Arsenal",
  "fee": "£105m",
  "transfer_type": "permanent",
  "date": "2024-07-15"
}
```

**How fans use it**:
- "What signings did we make?" → Show summer/winter transfers
- "Rice worth the money?" → Debate transfer fee with context
- "Who'd we let go?" → Mention departures with emotion

**RAG Integration**:
```python
# Enhance squad discussions with recent transfers
if query_mentions_new_signings(query):
    transfers = fetch_recent_transfers(team_id, months=6)
    context += format_transfer_context(transfers, club_persona)
```

**Emotional layering**:
```python
# Different fan reactions to same transfer
Arsenal fan: "£105m for Rice? Steep, but we needed that bite in midfield."
West Ham fan: "£105m!? Gutted to lose him, but that's generational money."
Spurs fan: "They paid WHAT for Rice? Mind the gap's getting wider..."
```

---

### 3. Legends (`/api/v1/legends`)

**What it provides**:
```json
{
  "name": "Thierry Henry",
  "years_active": "1999-2007",
  "goals": 228,
  "key_achievements": ["Premier League Golden Boot x4", "Invincible season"]
}
```

**How fans use it**:
- "Who's our best ever?" → Debate with legend stats
- "Anyone like Salah in our history?" → Compare current to legends
- "Tell me about [legend]" → Share stories/stats

**RAG Integration**:
```python
# Enhance comparison queries with legend context
if query_contains_comparison(query):
    legends = fetch_legends(team_id)
    # "Is Saka our best winger ever?"
    context += compare_to_legends(current_player="Saka", legends=legends, position="winger")
```

---

### 4. On This Day (`/api/v1/on-this-day`)

**What it provides**:
```json
{
  "date": "12-22",
  "year": 1989,
  "event": "Arsenal beat Liverpool 2-0 - Michael Thomas's title-clinching goal",
  "significance": "Last-minute goal wins the league at Anfield"
}
```

**How fans use it**:
- Automatically inject historical context on anniversary dates
- "Remember when..." → Trigger nostalgia with past events
- Pre-match hype using historical results vs opponent

**RAG Integration**:
```python
# Automatically add "on this day" context to every conversation
today = datetime.now().strftime("%m-%d")
historical_events = fetch_on_this_day(today, team_id)
if historical_events:
    context += f"\n\nOn this day: {format_historical_moment(historical_events[0])}"
```

---

### 5. Players Search (`/api/v1/players`)

**What it provides**:
```json
{
  "name": "Bukayo Saka",
  "position": "RW",
  "nationality": "England",
  "age": 22,
  "goals_this_season": 12,
  "assists_this_season": 8
}
```

**How fans use it**:
- "How's Saka doing?" → Show stats with emotion
- "Who's our top scorer?" → Rank players by goals
- "Any youngsters breaking through?" → Filter by age, highlight prospects

**RAG Integration**:
```python
# Enhance player queries with full stats
if intent == "player_info":
    player_data = search_players(query, team_id)
    if player_data:
        context += format_player_stats(player_data, add_fan_commentary=True)
```

---

## Implementation Strategy

### Phase 1: RAG Enhancement (Automatic Context Injection)

Update `rag.py` to automatically pull relevant context:

```python
def retrieve_hybrid_enriched(query: str, club: str = None) -> dict:
    """
    Enhanced retrieval that automatically injects conversation-enriching context.
    """
    # Base retrieval (existing)
    context, sources, metadata = retrieve_hybrid(query, club)

    # Enrich with contextual endpoints
    enrichments = []

    # 1. On This Day (always inject if available)
    today = datetime.now().strftime("%m-%d")
    historical = fetch_on_this_day(today, team_id)
    if historical:
        enrichments.append(f"📅 On this day in {historical['year']}: {historical['event']}")

    # 2. Injuries (inject for squad/team health queries)
    if query_about_squad_fitness(query):
        injuries = fetch_current_injuries(team_id)
        if injuries:
            enrichments.append(f"🏥 Current injuries: {format_injury_list(injuries)}")

    # 3. Transfers (inject for recent activity queries)
    if query_about_transfers(query):
        transfers = fetch_recent_transfers(team_id, months=3)
        if transfers:
            enrichments.append(f"📝 Recent moves: {format_transfer_summary(transfers)}")

    # 4. Player stats (inject for performance queries)
    if query_about_player_performance(query):
        player_name = extract_player_name(query)
        if player_name:
            stats = fetch_player_stats(player_name, team_id)
            enrichments.append(f"📊 {player_name}: {format_quick_stats(stats)}")

    # Combine enrichments with base context
    if enrichments:
        context = "\n\n".join([context] + enrichments)

    return context, sources, {**metadata, "enrichments": len(enrichments)}
```

### Phase 2: Persona-Specific Framing

Different clubs care about different things:

```python
def format_injury_for_persona(injury: dict, club: str) -> str:
    """Emotional framing based on club culture."""

    base = f"{injury['player_name']} out until {injury['expected_return']}"

    if club == "arsenal":
        # Arsenal fans: Tactical worry
        return f"{base} - reckon Arteta goes with Jorginho or pushes Havertz deeper?"

    elif club == "liverpool":
        # Liverpool fans: Intensity/press concern
        return f"{base} - that's our press compromised. Who covers the ground?"

    elif club == "manchester_city":
        # City fans: Squad depth confidence
        return f"{base} - not ideal, but depth chart's still strong. Next man up."

    elif club == "newcastle":
        # Newcastle fans: Investment/squad building anxiety
        return f"{base} - this is why we needed more depth in the window..."
```

### Phase 3: Conversation Triggers

Add conversational hooks that naturally lead to these topics:

```python
# In ai_response.py persona prompts
CONVERSATION_HOOKS = {
    "arsenal": [
        "If asked about squad, mention current injuries naturally",
        "If discussing transfers, reference the Rice fee debate",
        "If opponent is Spurs/Chelsea, bring up historical derby moments"
    ],
    "liverpool": [
        "Always note if Van Dijk or Salah fitness comes up",
        "Transfer discussions should reference Klopp's strategy",
        "Historical mentions: Istanbul 2005, Gerrard's slip (carefully)"
    ]
}
```

---

## Example Enriched Conversations

### Example 1: Squad Health Query

**User**: "Are we in good shape for the City game?"

**Without enrichment**:
```
Bot: "The team is looking strong."
```

**With enrichment**:
```
Bot: "Bit nervous, if I'm honest. Partey's still out with that knee issue
- won't be back until mid-January. That means Jorginho anchoring against
Haaland's runs, which... well, you saw what happened last time.

On the plus side, Rice has been immense since we brought him in. £105m
looked steep in July, but 3 months in? Worth every penny. His ball-winning
vs Chelsea last week was pure class.

Oh, and fun fact - on this day in 2007, we beat City 3-1 at Eastlands.
Adebayor hat-trick. Different times, eh?"

📊 Context sources:
- Injuries endpoint: Partey out until 2025-01-10
- Transfers: Rice from West Ham, £105m, Jul 2024
- On This Day: Dec 22, 2007 Arsenal 3-1 Man City
```

### Example 2: Transfer Debate

**User**: "Was Rice worth the money?"

**Without enrichment**:
```
Bot: "He's been playing well."
```

**With enrichment**:
```
Bot: "Look, £105m makes you gulp. British record fee, that. But watch him
against the big sides - Chelsea, City, Liverpool - the lad's everywhere.

12 starts, 2 goals, 4 assists. Not flashy numbers, but it's what he does
WITHOUT the ball that's changed us. We don't collapse in April anymore
because we've got that spine.

West Ham fans are gutted, obviously. Generational talent they developed,
now bossing midfield for their rivals. But £105m? That's 'build a new
stand' money for them.

Compare him to Vieira at his peak? Not quite there yet, but the trajectory's
right. Paddy was 27 when he hit his absolute prime. Rice is only 24."

📊 Context sources:
- Transfers: Rice details (£105m, from West Ham)
- Players: Rice stats (12 starts, 2G, 4A)
- Legends: Patrick Vieira comparison context
```

### Example 3: Pre-Match Context Injection

**User**: "Big game tomorrow."

**Without enrichment**:
```
Bot: "Yes, looking forward to it."
```

**With enrichment**:
```
Bot: "Derby day. These games are never just 3 points, are they?

Bit worried about our backline with Gabriel carrying that knock, but
Saliba's been unreal this season. If he stays fit, we've got a chance.

Fun bit of history - on this day in 1983, we beat them 2-1 at White Hart
Lane. Tony Woodcock scored the winner in the 89th minute. Their fans still
haven't forgiven him for that one.

Also, remember we just brought in Timber from Ajax - £40m. Dutch international,
covers fullback AND centre-back. Tactical flexibility that Arteta loves. Could
see him starting if Gabriel doesn't pass the fitness test.

Come on you Gunners. Let's make it 4 wins in a row in this fixture."

📊 Context sources:
- Injuries: Gabriel questionable
- Transfers: Timber from Ajax, £40m
- On This Day: 1983 Arsenal 2-1 Spurs (Dec 22)
- Standings: Current 4-game derby win streak
```

---

## Technical Implementation Checklist

### Backend Updates

- [x] Fix route ordering (`/games/{game_id}` moved after specific routes)
- [ ] Add enrichment helpers in `rag.py`:
  ```python
  def fetch_injury_context(team_id: int) -> Optional[str]
  def fetch_transfer_context(team_id: int, months: int = 6) -> Optional[str]
  def fetch_on_this_day_context(date: str, team_id: int) -> Optional[str]
  def fetch_legend_comparison(player: str, team_id: int) -> Optional[str]
  ```

- [ ] Update `retrieve_hybrid()` to call enrichment helpers based on query intent

### Persona Updates

- [ ] Add `CONVERSATION_HOOKS` dict to each persona in `ai_response.py`
- [ ] Update persona prompts to naturally weave in contextual info:
  ```
  "When discussing squad fitness, reference current injuries naturally"
  "When debating transfers, cite actual fees and show emotional reaction"
  "When asked about history, pull from legends and 'on this day' moments"
  ```

### Intent Detection

- [ ] Add new intent types in `rag.py`:
  ```python
  "squad_fitness" → Check injuries
  "transfer_talk" → Check recent transfers
  "player_comparison" → Check legends + current stats
  "pre_match_hype" → Check on-this-day + injuries + form
  ```

---

## Cost Considerations

**Current cost per query**: ~$0.002 (Haiku)

**With enrichment**:
- Base query: $0.002
- +3 endpoint calls (injuries, transfers, on-this-day): negligible (local DB)
- +15% token increase (richer context): ~$0.0003
- **Total**: ~$0.0023/query (15% increase for 3x richer conversations)

**Worth it?** Absolutely. The difference between:
- "Team is good" (robotic, forgettable)
- "Bit worried about Partey's knee, but Rice has been boss since we signed him for £105m. On this day in '07 we beat City 3-1..." (engaging, memorable)

---

## Next Steps

1. **Implement enrichment helpers** in `rag.py`
2. **Test with one persona** (Arsenal) to validate approach
3. **Measure engagement**: Do users ask follow-up questions more often?
4. **Expand to all 20 personas** once proven
5. **Add feedback loop**: Track which enrichments users respond to most

---

## The Philosophy

> "The best football conversations aren't recitations of xG and pass completion %.
> They're arguments about whether Rice was worth £105m, worry about Partey's fitness,
> nostalgia about Vieira's prime, and hype about derby day.
>
> These endpoints give our AI fans the ammunition to have THOSE conversations."

**Fan at heart. Analyst in nature. Now with the knowledge to prove it.**
