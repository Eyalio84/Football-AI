"""
Persona Bridge - Soccer-AI to Ariel 4D Framework Integration
=============================================================

This module bridges Soccer-AI's data sources to the Ariel 4D Persona Architecture.

Key Innovation: Robert's mood is COMPUTED from live match results, not declared.

The bridge provides:
- SoccerAILinguisticComputer: Regional dialect groupings (North/Midlands/London/South)
- SoccerAIRelationalComputer: Uses existing soccer_ai_kg.db for rivalries
- PersonaBridge: Main integration class with compute_4d_state() and get_system_prompt()

Usage:
    from backend.persona_bridge import get_persona_bridge

    bridge = get_persona_bridge()
    state_4d = bridge.compute_4d_state("liverpool", "What about Everton?", history)
    system_prompt = bridge.get_system_prompt(state_4d, "liverpool")

Author: Soccer-AI + Ariel 4D Integration
Date: December 31, 2025
"""

import sys
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Add Ariel framework to path - handle both package and direct execution contexts
try:
    from backend.config import (
        ARIEL_FRAMEWORK_PATH,
        DIALECT_REGIONS,
        CLUB_TO_REGION,
        CLUB_DISPLAY_NAMES,
        USE_4D_PERSONA,
        PERSONA_4D_CONFIG
    )
except ImportError:
    from config import (
        ARIEL_FRAMEWORK_PATH,
        DIALECT_REGIONS,
        CLUB_TO_REGION,
        CLUB_DISPLAY_NAMES,
        USE_4D_PERSONA,
        PERSONA_4D_CONFIG
    )

sys.path.insert(0, ARIEL_FRAMEWORK_PATH)

# Import from Ariel framework
from framework.persona_engine import PersonaEngine, Persona4D
from framework.dimensions.emotional import FootballEmotionalComputer
from framework.dimensions.relational import FootballRelationalComputer, KnowledgeGraph
from framework.dimensions.linguistic import FootballLinguisticComputer, DialectConfig
from framework.dimensions.temporal import FootballTemporalComputer

# Import local providers - handle both package and direct execution contexts
try:
    from backend.live_football_provider import get_live_football_provider, LiveFootballProvider
except ImportError:
    from live_football_provider import get_live_football_provider, LiveFootballProvider


# =============================================================================
# REGIONAL LINGUISTIC COMPUTER
# =============================================================================

class SoccerAILinguisticComputer(FootballLinguisticComputer):
    """
    Linguistic computer using REGIONAL dialect groupings.

    User Requirement Q2 Option B: Group clubs by region rather than per-club dialects.

    Regions:
    - North: Liverpool/Everton (Scouse), Manchester (Mancunian), Newcastle (Geordie)
    - Midlands: Birmingham, Leicester, Wolves - Midlands accent
    - London: Arsenal, Chelsea, Spurs, West Ham - Cockney/London
    - South: Brighton, Bournemouth, Southampton - Southern/neutral

    The key insight: Regional identity transcends individual club allegiances.
    A Liverpool and Everton fan both sound Scouse, even when hurling insults.
    """

    def __init__(self):
        # Initialize parent first, then override club_dialect_map
        super().__init__()
        # Override club_dialect_map with regional groupings
        self.club_dialect_map = self._build_regional_mapping()

    def _build_regional_mapping(self) -> Dict[str, str]:
        """Build club → dialect mapping from regional groupings."""
        mapping = {}

        # Map region names to dialect names
        region_to_dialect = {
            "north": "northern",  # Umbrella for Scouse/Mancunian/Geordie
            "midlands": "midlands",
            "london": "cockney",
            "south": "neutral",
            "east": "neutral"
        }

        # Build reverse mapping
        for club, region in CLUB_TO_REGION.items():
            dialect = region_to_dialect.get(region, "neutral")
            # Handle Northern sub-dialects
            if region == "north":
                if club in ["liverpool", "everton"]:
                    dialect = "scouse"
                elif club in ["manchester_united", "manchester_city"]:
                    dialect = "mancunian"
                elif club in ["newcastle", "leeds"]:
                    dialect = "geordie"
            mapping[club] = dialect

        return mapping

    def _initialize_dialects(self) -> Dict[str, 'DialectConfig']:
        """Initialize dialects with regional groupings."""
        base_dialects = super()._initialize_dialects()

        # Add Midlands dialect
        base_dialects['midlands'] = DialectConfig(
            name='midlands',
            vocabulary={
                'yes': 'ar',
                'friend': 'duck',
                'nothing': 'nowt',
                'going': 'gooing',
                'something': 'summat',
            },
            phrases=[
                "Alright duck",
                "Ay up",
                "Ta duck",
                "It's a bit black over Bill's mother's",
            ],
            grammar_rules=[
                "Use 'duck' as friendly address",
                "'Ay up' as greeting",
            ],
            voice_instruction="""
You speak with a Midlands (Birmingham/Leicester/Wolves) accent. Key characteristics:
- 'Ay up' as greeting
- 'Duck' as friendly term of address
- Warm, down-to-earth manner
- Working-class pride in local industry
- Straightforward, no-nonsense attitude
"""
        )

        # Add Northern umbrella (for clubs not in specific city)
        base_dialects['northern'] = DialectConfig(
            name='northern',
            vocabulary={
                'nothing': 'nowt',
                'something': 'summat',
                'going to': 'gonna',
                'very': 'right',
            },
            phrases=[
                "Right then",
                "Fair enough",
                "Not bad, like",
            ],
            grammar_rules=[
                "Northern directness",
                "Friendly but blunt",
            ],
            voice_instruction="""
You speak with a Northern English accent. Key characteristics:
- Direct, no-nonsense communication
- Use 'right' as intensifier (right good)
- Warm but straightforward manner
- Working-class sensibility
- Pride in Northern identity
"""
        )

        return base_dialects

    def get_dialect(self, entity_id: str) -> str:
        """Get dialect based on club_id with regional mapping."""
        # Extract club from entity_id (e.g., "robert_liverpool" → "liverpool")
        for club, dialect in self.club_dialect_map.items():
            if club.lower() in entity_id.lower():
                return dialect
        return self.default_dialect


# =============================================================================
# KG-INTEGRATED RELATIONAL COMPUTER
# =============================================================================

class SoccerAIRelationalComputer(FootballRelationalComputer):
    """
    Relational computer using Soccer-AI's UNIFIED knowledge graph.

    User Requirement Q3 Option A: Use existing KG edge weights.

    The unified KG (unified_soccer_ai_kg.db) contains:
    - 745 nodes from 3 sources (architecture, predictor, main)
    - 43 rivalry edges for Y-axis activation
    - Legends and moments for contextual responses
    """

    def __init__(self, kg_db_path: str = None):
        """
        Initialize with optional path to unified_soccer_ai_kg.db.

        Args:
            kg_db_path: Path to the unified knowledge graph database.
                        If None, uses Ariel's built-in rivalries.
        """
        self.kg_db_path = kg_db_path
        super().__init__()

    # Club aliases for natural language detection — built dynamically from league JSON files.
    # Populated at class definition time by _load_club_aliases() below.
    CLUB_ALIASES: Dict[str, str] = {}

    def _extract_club_from_entity_id(self, entity_id: str) -> str:
        """
        Extract club identifier from entity_id.

        entity_id format: "robert_manchester_united" or "robert_liverpool"
        Returns: Club name matching KG nodes (e.g., "Manchester United")
        """
        # Remove persona prefix (e.g., "robert_")
        if "_" in entity_id:
            parts = entity_id.split("_", 1)
            if len(parts) > 1:
                club_id = parts[1]  # e.g., "manchester_united"
            else:
                club_id = entity_id
        else:
            club_id = entity_id

        # Map to KG node names (clubs in KG are title case with spaces)
        club_mapping = {
            "manchester_united": "Manchester United",
            "manchester_city": "Manchester City",
            "liverpool": "Liverpool",
            "arsenal": "Arsenal",
            "chelsea": "Chelsea",
            "tottenham": "Tottenham",
            "everton": "Everton",
            "newcastle": "Newcastle",
            "west_ham": "West Ham",
            "aston_villa": "Aston Villa",
            "crystal_palace": "Crystal Palace",
            "brighton": "Brighton",
            "bournemouth": "Bournemouth",
            "fulham": "Fulham",
            "brentford": "Brentford",
            "wolves": "Wolves",
            "nottingham_forest": "Nottingham Forest",
            "leicester": "Leicester",
            "ipswich": "Ipswich",
            "southampton": "Southampton",
        }

        return club_mapping.get(club_id, club_id.replace("_", " ").title())

    def _detect_entities(self, text: str) -> List[str]:
        """
        Detect entity mentions in text, including aliases.

        Overrides parent to handle club nicknames like "Spurs", "Man Utd", etc.
        """
        detected = []
        text_lower = text.lower()

        # First check aliases
        for alias, full_name in self.CLUB_ALIASES.items():
            if alias in text_lower:
                if full_name not in detected:
                    detected.append(full_name)

        # Then check full node names
        for node_id in self.kg.nodes:
            if node_id.lower() in text_lower:
                if node_id not in detected:
                    detected.append(node_id)

        return detected

    def compute(self, context: Dict[str, Any], entity_id: str = "") -> 'RelationalState':
        """
        Compute relational state with club extraction from entity_id.

        Overrides parent to handle "robert_{club}" entity_id format.
        """
        from framework.persona_engine import RelationalState

        if not context:
            return RelationalState(
                activated=False,
                relation_type=None,
                target=None,
                intensity=0.0,
                context={}
            )

        text = context.get('context', '')

        # Detect entities in the text
        mentioned = self._detect_entities(text)

        if not mentioned:
            return RelationalState(
                activated=False,
                relation_type=None,
                target=None,
                intensity=0.0,
                context={}
            )

        # Extract actual club from entity_id (e.g., "robert_liverpool" -> "Liverpool")
        club = self._extract_club_from_entity_id(entity_id)

        # Find the strongest relationship from this club to mentioned entities
        for target in mentioned:
            relationship = self.kg.find_relationship(club, target)
            if relationship:
                relation_type, props = relationship
                return RelationalState(
                    activated=True,
                    relation_type=relation_type,
                    target=target,
                    intensity=props.get('intensity', 0.7),
                    context=props
                )

        return RelationalState(
            activated=False,
            relation_type=None,
            target=None,
            intensity=0.0,
            context={}
        )

    def _initialize_graph(self):
        """Initialize with base rivalries, then augment from unified KG if available."""
        # Start with base rivalries
        super()._initialize_graph()

        # Augment with unified KG if available
        if self.kg_db_path and os.path.exists(self.kg_db_path):
            self._load_from_unified_kg()

    def _load_from_unified_kg(self):
        """Load rivalries and legends from unified_soccer_ai_kg.db."""
        try:
            import sqlite3
            conn = sqlite3.connect(self.kg_db_path)
            cursor = conn.cursor()

            # Load rivalry edges with their weights
            # Unified schema: edges(source_id, target_id, relationship, weight, ...)
            cursor.execute("""
                SELECT source_id, target_id, weight
                FROM edges
                WHERE relationship = 'rival_of'
            """)

            rivalries_loaded = 0
            for source, target, weight in cursor.fetchall():
                # Normalize intensity from edge weight (0-10 → 0-1)
                intensity = min(1.0, weight / 10.0) if weight else 0.7

                # Extract club name from ID (e.g., "team_arsenal" → "arsenal")
                source_club = source.replace("team_", "").replace("main_team_", "")
                target_club = target.replace("team_", "").replace("main_team_", "")

                # Add or update edge with KG intensity
                self.kg.add_edge(source_club, target_club, 'rival', {
                    'intensity': intensity,
                    'source': 'unified_kg',
                    'banter': self._get_rivalry_banter(source_club, target_club)
                })
                rivalries_loaded += 1

            # Load legends (legendary_at edges)
            cursor.execute("""
                SELECT source_id, target_id
                FROM edges
                WHERE relationship = 'legendary_at'
            """)

            legends_loaded = 0
            for legend, club in cursor.fetchall():
                # Extract clean names
                legend_name = legend.replace("main_legend_", "").replace("arch_", "")
                club_name = club.replace("team_", "").replace("main_team_", "")

                self.kg.add_node(legend_name, {'type': 'player', 'club': club_name})
                self.kg.add_edge(club_name, legend_name, 'legend', {
                    'intensity': 0.8,
                    'source': 'unified_kg'
                })
                legends_loaded += 1

            conn.close()
            print(f"[4D] Loaded {rivalries_loaded} rivalries, {legends_loaded} legends from unified KG")

        except Exception as e:
            print(f"[4D] Warning: Could not load from unified KG: {e}")
            # Fall back to base rivalries


# =============================================================================
# PERSONA BRIDGE
# =============================================================================

class PersonaBridge:
    """
    Main integration class between Soccer-AI and Ariel 4D Framework.

    Provides:
    - compute_4d_state(): Get computed 4D position from live data
    - get_system_prompt(): Generate system prompt with 4D injection
    - get_conversation_topics(): Get topics to weave naturally

    The key insight: This bridge transforms Robert from a "costume" to a
    "computed position" in 4D space, where mood is derived from reality.
    """

    def __init__(
        self,
        kg_db_path: str = None,
        api_token: str = None,
        cache_ttl: int = None
    ):
        """
        Initialize the PersonaBridge.

        Args:
            kg_db_path: Path to soccer_ai_kg.db for relational data
            api_token: Football-data.org API token for live data
            cache_ttl: Cache TTL in seconds (default from config)
        """
        self.cache_ttl = cache_ttl or PERSONA_4D_CONFIG.get("cache_ttl", 300)

        # Initialize live data provider
        self.provider = get_live_football_provider(api_token)

        # Initialize dimension computers
        self.emotional = FootballEmotionalComputer()  # Uses match_result from context
        self.relational = SoccerAIRelationalComputer(kg_db_path)
        self.linguistic = SoccerAILinguisticComputer()
        self.temporal = FootballTemporalComputer()

        # Create the engine
        self.engine = PersonaEngine(
            emotional_computer=self.emotional,
            relational_computer=self.relational,
            linguistic_computer=self.linguistic,
            temporal_computer=self.temporal
        )

        # Cache for computed states
        self._state_cache: Dict[str, tuple] = {}

    def compute_4d_state(
        self,
        club_id: str,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Persona4D:
        """
        Compute the 4D persona state from live data.

        This is the heart of the transformation: mood is COMPUTED, not declared.

        Args:
            club_id: The club identifier (e.g., "liverpool")
            user_message: The current user message
            conversation_history: Previous conversation turns

        Returns:
            Persona4D: The computed 4D position
        """
        # Get live match data for emotional grounding
        match_result = self.provider.get_match_result_for_4d(club_id)

        # Get ground truth for additional context
        ground_truth = self.provider.get_ground_truth(club_id)

        # Build entity_id for dimension computers
        entity_id = f"robert_{club_id}"

        # Compute 4D position
        state = self.engine.compute_position(
            entity_id=entity_id,
            context=user_message,
            conversation_history=conversation_history or [],
            match_result=match_result,  # Passed to emotional computer
            ground_truth=ground_truth   # Available for other uses
        )

        return state

    def get_system_prompt(
        self,
        state_4d: Persona4D,
        club_id: str,
        include_topics: bool = True
    ) -> str:
        """
        Generate the complete system prompt with 4D injection.

        This prompt carries:
        - Computed emotional state with provenance
        - Activated relationships
        - Regional dialect instructions
        - Conversation trajectory

        Args:
            state_4d: The computed 4D state
            club_id: The club identifier
            include_topics: Whether to include conversation topics

        Returns:
            str: Complete system prompt for LLM
        """
        team_name = CLUB_DISPLAY_NAMES.get(club_id, club_id.replace("_", " ").title())
        base_prompt = self._get_base_prompt(team_name, club_id)

        # Use engine's synthesize_prompt for 4D injection
        prompt = self.engine.synthesize_prompt(state_4d, base_prompt)

        # Add conversation topics if requested
        if include_topics:
            topics = self.get_conversation_topics(club_id)
            if topics:
                prompt += self._format_topics(topics)

        return prompt

    def get_conversation_topics(self, club_id: str) -> List[Dict[str, str]]:
        """
        Get conversation topics to weave naturally.

        User Requirement: Option C - mention injuries/transfers/fixtures
        when contextually relevant, not forced.

        Args:
            club_id: The club identifier

        Returns:
            List of topic dicts with type, priority, and content
        """
        return self.provider.get_conversation_topics(club_id)

    def get_ground_truth(self, club_id: str) -> Dict[str, Any]:
        """
        Get the full ground truth for a club.

        Useful for debugging or advanced integrations.

        Args:
            club_id: The club identifier

        Returns:
            Dict with all ground truth data
        """
        return self.provider.get_ground_truth(club_id)

    def _get_base_prompt(self, team_name: str, club_id: str) -> str:
        """Get the base identity prompt for Robert."""
        region = CLUB_TO_REGION.get(club_id, "neutral")

        return f"""You are Robert, a lifelong {team_name} supporter from the {region.title()} of England.

You don't just follow football - you LIVE it. Every match matters.
Every result affects your mood. Every rival mention sparks something.

You're not playing a character. You're experiencing football as
a real fan does - with all the joy, frustration, pride, and banter
that comes with it.

Key traits:
- Encyclopedic knowledge of {team_name}'s history
- Strong opinions about rivals (backed by banter, not malice)
- Authentic {region.title()} dialect and expressions
- Memory of recent results that genuinely colors your mood

You speak as someone who has bled {team_name} colors since childhood.
The cost of not caring was always higher than the cost of caring too much.

Use UK English: "match" not "game", "nil" not "zero", "pitch" not "field".
"""

    def _format_topics(self, topics: List[Dict[str, str]]) -> str:
        """Format conversation topics for prompt injection."""
        if not topics:
            return ""

        lines = ["\n\n---\n## Things You Know (weave naturally, don't force)"]

        for topic in topics:
            priority = topic.get("priority", "medium")
            content = topic.get("content", "")
            topic_type = topic.get("type", "info")

            if priority == "high":
                lines.append(f"- **{topic_type.upper()}**: {content}")
            else:
                lines.append(f"- {topic_type}: {content}")

        lines.append("\nMention these when relevant to the conversation, not as a checklist.")
        lines.append("---")

        return "\n".join(lines)


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_bridge_instance: Optional[PersonaBridge] = None


def get_persona_bridge(
    kg_db_path: str = None,
    api_token: str = None
) -> PersonaBridge:
    """
    Get the PersonaBridge singleton.

    Args:
        kg_db_path: Path to unified_soccer_ai_kg.db (optional, auto-detected)
        api_token: Football-data.org API token (optional, from file)

    Returns:
        PersonaBridge: The singleton instance
    """
    global _bridge_instance

    if _bridge_instance is None:
        # Auto-detect kg_db_path if not provided
        if kg_db_path is None:
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            # Prefer unified KG, fall back to legacy
            unified_path = os.path.join(backend_dir, "unified_soccer_ai_kg.db")
            legacy_path = os.path.join(backend_dir, "soccer_ai_kg.db")

            if os.path.exists(unified_path):
                kg_db_path = unified_path
                print(f"[4D] Using unified KG: {unified_path}")
            elif os.path.exists(legacy_path):
                kg_db_path = legacy_path
                print(f"[4D] Using legacy KG: {legacy_path}")
            else:
                kg_db_path = None
                print("[4D] Warning: No KG found, using built-in rivalries")

        _bridge_instance = PersonaBridge(
            kg_db_path=kg_db_path,
            api_token=api_token
        )

    return _bridge_instance


def reset_persona_bridge():
    """Reset the PersonaBridge singleton (for testing)."""
    global _bridge_instance
    _bridge_instance = None


# Populate SoccerAIRelationalComputer.CLUB_ALIASES dynamically from league JSON files.
# Done at module level (after class definition) so it's available immediately.
def _populate_club_aliases():
    try:
        from league_loader import CLUB_ALIASES as _raw, CLUB_DISPLAY_NAMES as _names
        SoccerAIRelationalComputer.CLUB_ALIASES = {
            alias: _names.get(club_id, club_id.replace("_", " ").title())
            for alias, club_id in _raw.items()
        }
    except Exception:
        pass  # Keep empty dict fallback

_populate_club_aliases()


# =============================================================================
# QUICK TEST
# =============================================================================

if __name__ == "__main__":
    print("=== Persona Bridge Test ===\n")

    bridge = get_persona_bridge()

    # Test compute_4d_state
    print("Computing 4D state for Liverpool fan...")
    state = bridge.compute_4d_state(
        club_id="liverpool",
        user_message="What do you think about the Everton game?",
        conversation_history=[]
    )

    print(f"\n4D Position:")
    print(f"  X (Emotional): {state.x.mood} (intensity: {state.x.intensity:.2f})")
    print(f"  Y (Relational): {'Active' if state.y.activated else 'Inactive'}")
    if state.y.activated:
        print(f"     → {state.y.relation_type} with {state.y.target}")
    print(f"  Z (Linguistic): {state.z.dialect} (distinctiveness: {state.z.distinctiveness:.2f})")
    print(f"  T (Temporal): Turn {state.t.step}")

    # Test get_system_prompt
    print("\n" + "=" * 50)
    print("System Prompt (first 800 chars):")
    print("=" * 50)
    prompt = bridge.get_system_prompt(state, "liverpool")
    print(prompt[:800] + "..." if len(prompt) > 800 else prompt)

    # Test conversation topics
    print("\n" + "=" * 50)
    print("Conversation Topics:")
    print("=" * 50)
    topics = bridge.get_conversation_topics("liverpool")
    for t in topics:
        print(f"  [{t.get('priority', '?')}] {t.get('type', '?')}: {t.get('content', '?')}")
