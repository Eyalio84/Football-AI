"""
Compound Intelligent Conversation System
Enables fluent, natural multi-turn conversations with fan personas

FACTS-BASED INTELLIGENCE:
1. Conversation Memory: Track entities mentioned across turns
2. Follow-up Detection: Resolve pronouns and implicit references
3. Emotional Continuity: Maintain fan mood and context
4. Smart Context Building: Don't repeat, build upon previous answers
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import re


@dataclass
class ConversationState:
    """
    Tracks conversation state for compound intelligence.

    FACTS STORED:
    - last_entities: Teams/players mentioned recently
    - last_topic: What was discussed (standings, fixtures, scores, etc.)
    - club_mood: Current emotional state of fan persona
    - discussed_facts: Set of facts already mentioned (avoid repetition)
    - turn_count: Number of exchanges
    - persona_data: CACHED personality data (loaded once, reused all turns)
    """
    conversation_id: str
    club: Optional[str] = None
    last_entities: Dict[str, List[str]] = field(default_factory=dict)
    last_topic: Optional[str] = None
    club_mood: Optional[str] = None
    discussed_facts: set = field(default_factory=set)
    turn_count: int = 0
    last_update: datetime = field(default_factory=datetime.now)
    # CRITICAL: Persona data cached for entire session (cost optimization!)
    persona_data: Optional[Dict] = None

    def add_entity(self, entity_type: str, entity_name: str):
        """Track entities mentioned in conversation."""
        if entity_type not in self.last_entities:
            self.last_entities[entity_type] = []
        if entity_name not in self.last_entities[entity_type]:
            self.last_entities[entity_type].append(entity_name)
        # Keep only last 5 of each type
        self.last_entities[entity_type] = self.last_entities[entity_type][-5:]

    def mark_fact_discussed(self, fact: str):
        """Mark a fact as already discussed to avoid repetition."""
        self.discussed_facts.add(fact)

    def was_discussed(self, fact: str) -> bool:
        """Check if this fact was already mentioned."""
        return fact in self.discussed_facts

    def increment_turn(self):
        """Increment turn counter and update timestamp."""
        self.turn_count += 1
        self.last_update = datetime.now()


# In-memory conversation states (use Redis in production)
_conversation_states: Dict[str, ConversationState] = {}


def get_conversation_state(conversation_id: str, club: Optional[str] = None) -> ConversationState:
    """Get or create conversation state."""
    if conversation_id not in _conversation_states:
        _conversation_states[conversation_id] = ConversationState(
            conversation_id=conversation_id,
            club=club
        )
    return _conversation_states[conversation_id]


def detect_follow_up(query: str, state: ConversationState) -> Tuple[bool, Optional[str]]:
    """
    Detect if query is a follow-up to previous conversation.

    Returns:
        (is_follow_up: bool, resolved_query: str)

    FOLLOW-UP INDICATORS:
    - Pronouns: "they", "them", "their", "he", "him"
    - Anaphora: "that team", "those players", "the club"
    - Short queries: "And today?", "What about fixtures?"
    - Continuation: "How about", "What else"
    """
    query_lower = query.lower()

    # Pattern 1: Pronouns referring to teams
    pronoun_patterns = [
        (r'\bthey\b', 'teams'),
        (r'\bthem\b', 'teams'),
        (r'\btheir\b', 'teams'),
        (r'\bthat team\b', 'teams'),
        (r'\bthe club\b', 'teams'),
        (r'\bhe\b', 'players'),
        (r'\bhim\b', 'players'),
        (r'\bhis\b', 'players'),
        (r'\bthat player\b', 'players'),
    ]

    for pattern, entity_type in pronoun_patterns:
        if re.search(pattern, query_lower):
            # Resolve pronoun to last mentioned entity
            if entity_type in state.last_entities and state.last_entities[entity_type]:
                last_entity = state.last_entities[entity_type][-1]
                # Replace pronoun with entity name
                resolved = re.sub(pattern, last_entity, query_lower, count=1)
                return True, resolved

    # Pattern 2: Short continuation queries
    continuation_patterns = [
        r'^and ',
        r'^how about ',
        r'^what about ',
        r'^what else',
        r'^anything else',
    ]

    for pattern in continuation_patterns:
        if re.search(pattern, query_lower):
            # This is a continuation of previous topic
            if state.last_topic:
                # Prepend context from last topic
                resolved = f"{state.last_topic} {query}"
                return True, resolved

    # Pattern 3: Bare topic queries (just "fixtures?", "scores?")
    bare_topics = ['fixtures', 'scores', 'standings', 'table', 'results', 'games']
    if query_lower.strip('?!. ') in bare_topics:
        # User asking for topic related to last mentioned team
        if 'teams' in state.last_entities and state.last_entities['teams']:
            last_team = state.last_entities['teams'][-1]
            resolved = f"{last_team} {query}"
            return True, resolved

    return False, None


def build_compound_context(
    query: str,
    base_context: str,
    base_sources: List[Dict],
    state: ConversationState
) -> Tuple[str, List[Dict], Dict]:
    """
    Build compound context that:
    1. Removes facts already discussed (avoid repetition)
    2. Adds emotional continuity markers
    3. Injects follow-up awareness

    Returns:
        (enriched_context, sources, metadata)
    """
    # Extract fact lines from base context
    context_lines = base_context.split('\n')
    new_lines = []

    for line in context_lines:
        # Skip empty lines
        if not line.strip():
            new_lines.append(line)
            continue

        # Check if this fact was already discussed
        # (Use first 50 chars as fact signature)
        fact_sig = line[:50].strip()
        if state.was_discussed(fact_sig):
            # Skip this fact - already mentioned
            continue

        # This is new information - include it
        new_lines.append(line)
        state.mark_fact_discussed(fact_sig)

    # Rebuild context
    enriched_context = '\n'.join(new_lines)

    # Add conversation metadata
    metadata = {
        'is_follow_up': state.turn_count > 0,
        'turn_count': state.turn_count,
        'last_topic': state.last_topic,
        'club_mood': state.club_mood,
        'known_entities': dict(state.last_entities)
    }

    # Add emotional continuity marker if club mood exists
    if state.club_mood:
        enriched_context = f"[Fan Mood: {state.club_mood}]\n\n{enriched_context}"

    # Add follow-up marker if this is a continuation
    if state.turn_count > 0:
        enriched_context = f"[Conversation Turn {state.turn_count + 1}]\n{enriched_context}"

    # HIGH IMPACT: Detect rival mentions and inject banter!
    if state.persona_data:
        import rag  # Import here to avoid circular dependency
        rivalry = rag.detect_rival_mention(query, state.persona_data)
        if rivalry:
            enriched_context = rag.enrich_with_rivalry(enriched_context, rivalry)
            metadata['rivalry_detected'] = rivalry.get('rival_name')
            metadata['rivalry_intensity'] = rivalry.get('intensity')

        # HIGH IMPACT: Detect squad queries and inject injury list!
        if rag.detect_squad_query(query):
            team_id = state.persona_data.get('team_id')
            if team_id:
                enriched_context = rag.enrich_with_injuries(enriched_context, team_id)
                metadata['injuries_injected'] = True

        # POLISH: Detect legend comparisons and inject legend context!
        if rag.detect_legend_comparison(query):
            enriched_context = rag.enrich_with_legends(enriched_context, state.persona_data)
            metadata['legends_injected'] = True

    return enriched_context, base_sources, metadata


def update_conversation_state(
    state: ConversationState,
    query: str,
    entities: Dict,
    intent: str,
    response: str
):
    """
    Update conversation state after each turn.

    FACTS UPDATED:
    - Entities mentioned (teams, players)
    - Current topic (intent)
    - Turn count
    """
    # Update entities
    if 'teams' in entities:
        for team in entities['teams']:
            state.add_entity('teams', team)

    if 'players' in entities:
        for player in entities['players']:
            player_name = player.get('name') if isinstance(player, dict) else player
            state.add_entity('players', player_name)

    # Update topic
    state.last_topic = intent

    # Increment turn
    state.increment_turn()


def enhance_prompt_with_context(
    base_prompt: str,
    state: ConversationState
) -> str:
    """
    Enhance AI prompt with conversation context for fluency.

    ENHANCEMENTS:
    - Previous entities mentioned
    - Emotional continuity instructions
    - Anti-repetition directive
    """
    enhancements = []

    # Add conversation awareness
    if state.turn_count > 0:
        enhancements.append(
            f"[CONVERSATION CONTEXT: This is turn {state.turn_count + 1}. "
            f"Last topic: {state.last_topic or 'general'}]"
        )

    # Add entity awareness
    if state.last_entities:
        entity_str = ", ".join([
            f"{k}: {', '.join(v[-2:])}"  # Last 2 of each type
            for k, v in state.last_entities.items()
            if v
        ])
        enhancements.append(
            f"[ENTITIES MENTIONED: {entity_str}]"
        )

    # Add anti-repetition directive
    if state.discussed_facts:
        enhancements.append(
            "[INSTRUCTION: Don't repeat facts from previous turns. "
            "Build on what you already told them, don't restate it.]"
        )

    # Add mood continuity
    if state.club_mood:
        enhancements.append(
            f"[FAN MOOD: {state.club_mood}. Maintain this emotional tone.]"
        )

    # Prepend enhancements to prompt
    if enhancements:
        return "\n".join(enhancements) + "\n\n" + base_prompt

    return base_prompt


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("Testing Compound Intelligent Conversation System")
    print("=" * 60)

    # Test 1: Follow-up detection
    print("\n[TEST 1] Follow-up Detection")
    print("-" * 40)

    state = ConversationState(conversation_id="test-1", club="arsenal")
    state.add_entity('teams', 'Arsenal')
    state.last_topic = "standings"

    test_queries = [
        ("How are they doing?", True),  # "they" = Arsenal
        ("And their fixtures?", True),  # "their" = Arsenal
        ("What about Liverpool?", False),  # New topic
        ("fixtures", True),  # Bare topic with known team
    ]

    for query, expected_follow_up in test_queries:
        is_follow_up, resolved = detect_follow_up(query, state)
        status = "✅" if is_follow_up == expected_follow_up else "❌"
        print(f"  {status} '{query}' -> Follow-up: {is_follow_up}")
        if resolved:
            print(f"     Resolved: '{resolved}'")

    # Test 2: Anti-repetition
    print("\n[TEST 2] Anti-Repetition")
    print("-" * 40)

    state2 = ConversationState(conversation_id="test-2")
    context1 = "Arsenal is 1st with 39 points\nManchester City is 2nd with 37 points"

    # First turn
    enriched1, _, _ = build_compound_context("standings", context1, [], state2)
    print(f"  Turn 1 context: {len(enriched1)} chars")

    # Second turn - same data should be filtered
    enriched2, _, _ = build_compound_context("standings again", context1, [], state2)
    print(f"  Turn 2 context: {len(enriched2)} chars (should be shorter)")
    print(f"  Facts filtered: {len(state2.discussed_facts)}")

    print("\n" + "=" * 60)
    print("Tests complete.")
