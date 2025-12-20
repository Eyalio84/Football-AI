# Soccer-AI 4D Transformation Guide

> Transform Robert from scattered components to unified 4D persona with live API integration.

## The Vision

**Current State**: Robert's personality is assembled from pieces:
- Mood calculated in `fan_enhancements.py`
- Dialect injected separately
- Rivalry detected separately
- All manually stitched into system prompt

**Target State**: Robert is a computed 4D position:
```
P(t) = (x, y, z, t)
```
- **X** = Emotional state from LIVE match results (win → euphoric, loss → furious)
- **Y** = Relational state from knowledge graph (rivalry activated, legend mentioned)
- **Z** = Linguistic state (Scouse, Geordie, Cockney dialects)
- **T** = Temporal state (conversation trajectory, momentum)

The AI doesn't play a football fan. It **lives** one.

---

## Why This Matters

### The Costume Problem (Current)
```python
system_prompt = f"""You are Robert, a passionate {team} fan.
Current mood: {mood}
Dialect: Use {dialect} expressions"""
```

The mood is a **string**. If challenged, the AI has no defense.

### The 4D Solution (Target)
```python
state = provider.process({"result": "win", "our_score": 3, "their_score": 0})
# state.mood = "euphoric" (COMPUTED from real match data)
# state.confidence = 0.95 (GROUNDED in API response)
```

The mood is **computed from live data**. It's mathematically real.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SOCCER-AI BACKEND                         │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │   main.py       │───▶│  ai_response.py │                 │
│  │   (FastAPI)     │    │  (Haiku API)    │                 │
│  └────────┬────────┘    └────────┬────────┘                 │
│           │                      │                           │
│           ▼                      ▼                           │
│  ┌─────────────────────────────────────────┐                │
│  │         4D PERSONA LAYER (NEW)          │                │
│  │                                         │                │
│  │  ┌───────────────┐  ┌───────────────┐  │                │
│  │  │ RobertPersona │  │ FootballData  │  │                │
│  │  │ compute_state │◀─│ Provider      │  │                │
│  │  └───────────────┘  └───────┬───────┘  │                │
│  │                             │          │                │
│  └─────────────────────────────┼──────────┘                │
│                                │                            │
└────────────────────────────────┼────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  football-data.org API │
                    │  (Live match results)  │
                    └────────────────────────┘
```

---

## Implementation Steps

### Step 1: Add Framework Bridge

Create `backend/persona_bridge.py`:

```python
"""
Bridge to 4D Persona Architecture.

Connects Soccer-AI to the shared framework.
"""

import sys
import os

# Add framework to path
FRAMEWORK_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '4d_persona_architecture')
)
if FRAMEWORK_PATH not in sys.path:
    sys.path.insert(0, FRAMEWORK_PATH)

# Import from framework
from framework.persona_engine import PersonaEngine, Persona4D
from framework.ground_truth_providers import FootballDataProvider
from personas.robert.robert_4d import RobertPersona

__all__ = [
    'PersonaEngine',
    'Persona4D',
    'FootballDataProvider',
    'RobertPersona'
]
```

### Step 2: Update RobertPersona

Ensure `4d_persona_architecture/personas/robert/robert_4d.py` follows the pattern:

```python
class RobertPersona:
    """Robert the Football Fan - 4D Persona."""

    def __init__(self, team: str = "manchester_united"):
        self.entity_id = f"robert_{team}"
        self.team = team

        # Initialize dimension computers
        self.engine = PersonaEngine(
            emotional_computer=FootballEmotionalComputer(),
            relational_computer=FootballRelationalComputer(),
            linguistic_computer=FootballLinguisticComputer(),
            temporal_computer=FootballTemporalComputer()
        )

        self.base_prompt = self._get_base_prompt()

    def compute_state(
        self,
        context: str,
        conversation_history: list = None,
        match_result: dict = None
    ) -> Persona4D:
        """Compute Robert's 4D state."""
        return self.engine.compute_position(
            entity_id=self.entity_id,
            context=context,
            conversation_history=conversation_history or [],
            match_result=match_result  # Extra context for emotional computation
        )

    def get_system_prompt(self, state: Persona4D) -> str:
        """Get system prompt with 4D injection."""
        return self.engine.synthesize_prompt(state, self.base_prompt)
```

### Step 3: Modify main.py

Replace scattered mood/dialect/rivalry calls:

```python
# OLD (scattered)
mood = calculate_mood_from_results(team, results)
dialect = get_dialect_config(team)
rivalry_context = detect_rivalry(query, team)
system_prompt = build_prompt(mood, dialect, rivalry_context, ...)

# NEW (unified)
from persona_bridge import RobertPersona, FootballDataProvider

# Initialize once at startup
persona = RobertPersona(team=selected_team)
provider = FootballDataProvider(team=selected_team, api_key=FOOTBALL_API_KEY)

# In chat handler
@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    # Fetch live match data
    match_data = await get_latest_match(request.team)

    # Compute ground truth state
    ground_state = provider.process(match_data)

    # Compute 4D position
    state_4d = persona.compute_state(
        context=request.message,
        conversation_history=request.history,
        match_result=match_data
    )

    # Get 4D-injected prompt
    system_prompt = persona.get_system_prompt(state_4d)

    # Call Haiku (existing code)
    response = await generate_response(
        messages=request.messages,
        system=system_prompt,
        ...
    )

    return {"response": response, "mood": state_4d.x.mood}
```

### Step 4: Connect Live API

The `FootballDataProvider` already exists in `ground_truth_providers.py`.
Connect it to `football_api.py`:

```python
# backend/live_integration.py

from football_api import FootballDataAPI
from persona_bridge import FootballDataProvider

class LiveFootballProvider(FootballDataProvider):
    """Extended provider with live API integration."""

    def __init__(self, team: str, api_key: str = None):
        super().__init__(team=team, api_key=api_key)
        self.live_api = FootballDataAPI(api_key)

    async def fetch_and_process(self) -> dict:
        """Fetch live data and compute state."""
        # Get latest match from live API
        match = await self.live_api.get_latest_match(self.team_config["id"])

        if match:
            # Process through ground truth provider
            state = self.process(match)
            return {
                "match": match,
                "state": state,
                "mood": state.mood,
                "intensity": state.intensity
            }

        return {"match": None, "state": None, "mood": "neutral"}
```

### Step 5: Update ai_response.py

Replace manual prompt assembly:

```python
# OLD
def build_system_prompt(team, mood, dialect, rivalry_context, rag_context):
    prompt = KG_RAG_SYSTEM_PROMPT
    prompt += f"\n\nCurrent mood: {mood}"
    prompt += f"\n\nDialect: {dialect}"
    if rivalry_context:
        prompt += f"\n\nRivalry: {rivalry_context}"
    return prompt

# NEW
def build_system_prompt(persona: RobertPersona, state_4d: Persona4D, rag_context: str):
    """Build prompt using 4D injection."""
    # Get 4D-injected base prompt
    base = persona.get_system_prompt(state_4d)

    # Add RAG context
    return f"""{base}

---

## Retrieved Context

{rag_context}

---

Use the context above to answer questions. Stay in character.
"""
```

---

## The 4D Dimensions for Robert

### X-Axis: Emotional (Match Results)

```python
class FootballEmotionalComputer(DimensionComputer):
    """Compute mood from match results."""

    RESULT_MOODS = {
        "win": {"mood": "euphoric", "intensity": 0.9},
        "draw": {"mood": "tense", "intensity": 0.6},
        "loss": {"mood": "frustrated", "intensity": 0.8}
    }

    RIVALRY_BOOST = 0.2  # Extra intensity for rivalry matches

    def compute(self, context: dict, entity_id: str) -> EmotionalState:
        match = context.get("match_result", {})
        result = match.get("result", "neutral")
        is_rivalry = match.get("is_rivalry", False)

        mood_data = self.RESULT_MOODS.get(result, {"mood": "neutral", "intensity": 0.5})

        intensity = mood_data["intensity"]
        if is_rivalry:
            intensity = min(1.0, intensity + self.RIVALRY_BOOST)
            if result == "win":
                mood = "ecstatic"  # Beat a rival!
            elif result == "loss":
                mood = "devastated"  # Lost to a rival!
            else:
                mood = mood_data["mood"]
        else:
            mood = mood_data["mood"]

        return EmotionalState(
            value=1.0 if result == "win" else -1.0 if result == "loss" else 0.0,
            mood=mood,
            intensity=intensity,
            reason=f"Result: {result} vs {match.get('opponent', 'unknown')}",
            grounded_in=[match]
        )
```

### Y-Axis: Relational (Rivalries & Legends)

```python
class FootballRelationalComputer(DimensionComputer):
    """Detect active relationships from context."""

    def compute(self, context: dict, entity_id: str) -> RelationalState:
        message = context.get("context", "").lower()
        team = entity_id.split("_")[1]  # robert_liverpool → liverpool

        # Check rivalries
        rivalries = self._get_rivalries(team)
        for rival, intensity in rivalries.items():
            if rival in message:
                return RelationalState(
                    activated=True,
                    relation_type="rival",
                    target=rival,
                    intensity=intensity / 10,
                    context={"banter_mode": True}
                )

        # Check legends
        legends = self._get_legends(team)
        for legend in legends:
            if legend.lower() in message:
                return RelationalState(
                    activated=True,
                    relation_type="legend",
                    target=legend,
                    intensity=0.8,
                    context={"nostalgia_mode": True}
                )

        return RelationalState(activated=False)
```

### Z-Axis: Linguistic (Regional Dialects)

```python
class FootballLinguisticComputer(DimensionComputer):
    """Inject regional dialect."""

    DIALECTS = {
        "liverpool": {
            "dialect": "scouse",
            "phrases": ["la", "boss", "sound", "dead good"],
            "voice": "Scouse accent - warm, musical, drops letters"
        },
        "newcastle": {
            "dialect": "geordie",
            "phrases": ["pet", "howay", "canny", "wey aye"],
            "voice": "Geordie accent - warm, distinctive, proud"
        },
        "london": {
            "dialect": "cockney",
            "phrases": ["bruv", "innit", "proper", "mate"],
            "voice": "London accent - direct, streetwise"
        }
    }

    def compute(self, context: dict, entity_id: str) -> LinguisticState:
        team = entity_id.split("_")[1]
        region = self._get_region(team)
        dialect_data = self.DIALECTS.get(region, {"dialect": "neutral"})

        return LinguisticState(
            dialect=dialect_data["dialect"],
            distinctiveness=0.8,
            vocabulary={"phrases": dialect_data.get("phrases", [])},
            voice_instruction=dialect_data.get("voice", "")
        )
```

### T-Axis: Temporal (Conversation Flow)

```python
class FootballTemporalComputer(DimensionComputer):
    """Track conversation trajectory."""

    def compute(self, context: dict, entity_id: str) -> TemporalState:
        history = context.get("conversation_history", [])

        return TemporalState(
            step=len(history),
            trajectory=[],  # Filled by engine
            velocity={},
            momentum={},
            memory=self._extract_salient_topics(history)
        )

    def _extract_salient_topics(self, history: list) -> list:
        """Extract memorable topics from conversation."""
        topics = []
        for turn in history[-5:]:
            content = turn.get("content", "").lower()
            if "goal" in content:
                topics.append("goals discussed")
            if "transfer" in content:
                topics.append("transfers discussed")
            if any(rival in content for rival in ["liverpool", "city", "united"]):
                topics.append("rivalry mentioned")
        return topics[:3]
```

---

## Testing the Integration

### Unit Test: 4D State Computation

```python
# tests/test_4d_integration.py

def test_win_triggers_euphoric():
    persona = RobertPersona(team="manchester_united")
    provider = FootballDataProvider(team="manchester_united")

    match = {"result": "win", "our_score": 3, "their_score": 0, "opponent": "Arsenal"}
    ground_state = provider.process(match)

    assert ground_state.mood == "euphoric"
    assert ground_state.intensity > 0.8

def test_rivalry_loss_triggers_devastated():
    provider = FootballDataProvider(team="manchester_united")

    match = {"result": "loss", "our_score": 0, "their_score": 3, "opponent": "Liverpool"}
    ground_state = provider.process(match)

    assert ground_state.mood == "devastated"  # Lost to rival
    assert ground_state.intensity > 0.9

def test_dialect_injection():
    persona = RobertPersona(team="liverpool")
    state = persona.compute_state("What about Gerrard?")

    assert state.z.dialect == "scouse"
    assert "la" in state.z.vocabulary.get("phrases", [])
```

### Integration Test: Full Chat Flow

```python
def test_live_api_to_response():
    """Test: Live API → Ground Truth → 4D State → Haiku → Response"""

    # 1. Simulate live API response
    match = {"result": "win", "our_score": 2, "their_score": 1, "opponent": "Chelsea"}

    # 2. Process through ground truth
    provider = FootballDataProvider(team="manchester_united")
    ground_state = provider.process(match)
    assert ground_state.mood == "euphoric"

    # 3. Compute 4D state
    persona = RobertPersona(team="manchester_united")
    state_4d = persona.compute_state(
        context="How are you feeling about the match?",
        match_result=match
    )
    assert state_4d.x.mood == "euphoric"

    # 4. Generate system prompt
    prompt = persona.get_system_prompt(state_4d)
    assert "EUPHORIC" in prompt.upper()
    assert "Chelsea" in prompt or "win" in prompt.lower()
```

---

## Migration Checklist

### Phase 1: Framework Connection
- [ ] Create `backend/persona_bridge.py`
- [ ] Test imports work
- [ ] Verify RobertPersona exists in framework

### Phase 2: Replace Scattered Logic
- [ ] Replace `calculate_mood_from_results()` → `provider.process()`
- [ ] Replace `get_dialect_config()` → `state_4d.z.dialect`
- [ ] Replace `detect_rivalry()` → `provider.detect_historical_context()`
- [ ] Replace manual prompt → `persona.get_system_prompt(state_4d)`

### Phase 3: Live API Integration
- [ ] Connect `FootballDataProvider` to `football_api.py`
- [ ] Test live match → ground truth → mood
- [ ] Verify real-time updates

### Phase 4: Testing & Validation
- [ ] Add 4D unit tests
- [ ] Integration tests pass
- [ ] No behavioral regression
- [ ] Robert still sounds like Robert

---

## Expected Outcomes

After transformation:

1. **Live Mood**: Robert's mood changes based on REAL match results
   - Man United wins 3-0 → Robert is EUPHORIC
   - Man United loses to Liverpool → Robert is DEVASTATED

2. **Unified Architecture**: Single `compute_state()` call replaces 4+ scattered functions

3. **Anti-Gaslighting**: If user says "You're not really a fan", Robert can point to:
   - Ground truth: "My mood was computed from the 3-0 win yesterday"
   - Data source: football-data.org API

4. **Consistency**: Same 4D framework as Eyal-AI, Barry (tutor), Marcus (student)

---

## Reference Implementation

See: `/storage/emulated/0/Download/eyal-ai/pkg/conversation/chat_engine.py`

This file shows the pattern:
- `_init_4d_persona()` - Initialize persona + provider
- `compute_4d_state()` - Compute P(t) = (x, y, z, t)
- `chat()` - Use computed state for system prompt
- `export_context()` - Provider mode for external tools
