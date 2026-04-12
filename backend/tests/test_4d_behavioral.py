"""
4D Persona Behavioral Test Suite
=================================

Tests the BEHAVIORAL correctness of the 4D persona implementation:
- Identity: Does Robert answer as the correct fan?
- Mood Grounding: Is mood derived from REAL results?
- Team Switching: Do dialect/mood/topics change with club?
- Rivalry Activation: Does mentioning rivals trigger Y-axis?
- Anti-Gaslighting: Does Robert resist false claims about results?

Run with: pytest tests/test_4d_behavioral.py -v
"""

import pytest
import sqlite3
import os
import sys
from datetime import datetime, timedelta

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import USE_4D_PERSONA, CLUB_TO_REGION, DIALECT_REGIONS
from persona_bridge import get_persona_bridge, reset_persona_bridge, PersonaBridge
from live_football_provider import get_live_football_provider, LiveFootballProvider


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singletons before each test."""
    reset_persona_bridge()
    yield


@pytest.fixture
def bridge():
    """Get a fresh PersonaBridge instance."""
    return get_persona_bridge()


@pytest.fixture
def provider():
    """Get a fresh LiveFootballProvider instance."""
    return LiveFootballProvider()


@pytest.fixture
def unified_db():
    """Connect to unified KG for verification."""
    # Try multiple paths
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "unified_soccer_ai_kg.db"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "unified_soccer_ai_kg.db"),
        "/storage/emulated/0/Download/synthesis-rules/soccer-AI/backend/unified_soccer_ai_kg.db"
    ]

    db_path = None
    for p in possible_paths:
        if os.path.exists(p):
            db_path = p
            break

    if db_path:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        yield conn
        conn.close()
    else:
        pytest.skip(f"Unified DB not found in: {possible_paths}")


# =============================================================================
# TEST: IDENTITY - Robert answers as correct fan
# =============================================================================

class TestIdentity:
    """Test that Robert's identity matches the selected club."""

    def test_man_utd_prompt_mentions_club(self, bridge):
        """System prompt should mention Manchester United."""
        state = bridge.compute_4d_state("manchester_united", "Hello", [])
        prompt = bridge.get_system_prompt(state, "manchester_united")

        assert "Manchester United" in prompt or "Man United" in prompt
        assert "supporter" in prompt.lower() or "fan" in prompt.lower()

    def test_liverpool_prompt_mentions_club(self, bridge):
        """System prompt should mention Liverpool."""
        state = bridge.compute_4d_state("liverpool", "Hello", [])
        prompt = bridge.get_system_prompt(state, "liverpool")

        assert "Liverpool" in prompt

    def test_different_clubs_different_prompts(self, bridge):
        """Different clubs should produce different prompts."""
        man_utd_state = bridge.compute_4d_state("manchester_united", "Hello", [])
        liverpool_state = bridge.compute_4d_state("liverpool", "Hello", [])

        man_utd_prompt = bridge.get_system_prompt(man_utd_state, "manchester_united")
        liverpool_prompt = bridge.get_system_prompt(liverpool_state, "liverpool")

        # Prompts should be different
        assert man_utd_prompt != liverpool_prompt

        # Each should mention their club
        assert "Manchester United" in man_utd_prompt or "United" in man_utd_prompt
        assert "Liverpool" in liverpool_prompt


# =============================================================================
# TEST: MOOD GROUNDING - Mood from real results
# =============================================================================

class TestMoodGrounding:
    """Test that mood is derived from actual match results."""

    def test_mood_has_reason(self, bridge):
        """Mood should have a reason explaining why."""
        state = bridge.compute_4d_state("manchester_united", "How are you?", [])

        # X-axis should have mood and reason
        assert hasattr(state.x, 'mood')
        assert hasattr(state.x, 'reason')
        # Reason should not be empty
        assert state.x.reason is not None

    def test_ground_truth_has_form_string(self, bridge):
        """Ground truth should include form string (WWDLL etc)."""
        ground_truth = bridge.get_ground_truth("manchester_united")

        # Should have form_string key
        assert "form_string" in ground_truth
        # Form string should only contain W, D, L
        form = ground_truth.get("form_string", "")
        if form:
            assert all(c in "WDL" for c in form)

    def test_mood_reason_mentions_results(self, bridge):
        """Mood reason should reference actual results."""
        ground_truth = bridge.get_ground_truth("manchester_united")
        mood_reason = ground_truth.get("mood_reason", "")

        # Should mention wins, losses, or form
        result_keywords = ["win", "loss", "draw", "beat", "lost", "form", "W", "L", "D"]
        has_result_mention = any(kw.lower() in mood_reason.lower() for kw in result_keywords)

        # Allow empty mood_reason if no recent results
        if mood_reason:
            assert has_result_mention or "No recent" in mood_reason

    def test_match_history_exists_in_unified_db(self, unified_db):
        """Unified DB should have match history for mood fallback."""
        cursor = unified_db.cursor()

        # Check Man Utd matches exist (DB uses "Man United" not "Manchester United")
        cursor.execute("""
            SELECT COUNT(*) FROM match_history
            WHERE home_team LIKE '%Man United%' OR away_team LIKE '%Man United%'
        """)
        count = cursor.fetchone()[0]

        assert count > 0, "No Manchester United matches in unified DB"

    def test_recent_man_utd_results(self, unified_db):
        """Check actual recent Man Utd results for mood verification."""
        cursor = unified_db.cursor()

        # Get last 5 Man Utd matches (DB uses "Man United")
        cursor.execute("""
            SELECT match_date, home_team, away_team, ft_home, ft_away, ft_result
            FROM match_history
            WHERE home_team LIKE '%Man United%' OR away_team LIKE '%Man United%'
            ORDER BY match_date DESC
            LIMIT 5
        """)
        results = cursor.fetchall()

        print("\n=== Recent Man Utd Results (for mood verification) ===")
        for r in results:
            print(f"  {r['match_date']}: {r['home_team']} {r['ft_home']}-{r['ft_away']} {r['away_team']} ({r['ft_result']})")

        assert len(results) > 0


# =============================================================================
# TEST: TEAM SWITCHING - Dialect, mood, topics change
# =============================================================================

class TestTeamSwitching:
    """Test that switching clubs changes dialect, mood, and topics."""

    def test_dialect_changes_with_club(self, bridge):
        """Different regions should have different dialects."""
        # Man Utd = North (Mancunian)
        man_utd_state = bridge.compute_4d_state("manchester_united", "Hello", [])

        # Arsenal = London (Cockney)
        arsenal_state = bridge.compute_4d_state("arsenal", "Hello", [])

        # Aston Villa = Midlands
        villa_state = bridge.compute_4d_state("aston_villa", "Hello", [])

        # Dialects should differ
        assert man_utd_state.z.dialect != arsenal_state.z.dialect
        assert arsenal_state.z.dialect != villa_state.z.dialect

        # Verify expected dialects
        assert man_utd_state.z.dialect == "mancunian"
        assert arsenal_state.z.dialect == "cockney"
        assert villa_state.z.dialect == "midlands"

    def test_liverpool_everton_same_dialect(self, bridge):
        """Liverpool and Everton should both be Scouse (same city)."""
        liverpool_state = bridge.compute_4d_state("liverpool", "Hello", [])
        everton_state = bridge.compute_4d_state("everton", "Hello", [])

        assert liverpool_state.z.dialect == everton_state.z.dialect == "scouse"

    def test_man_utd_man_city_same_dialect(self, bridge):
        """Man Utd and Man City should both be Mancunian (same city)."""
        man_utd_state = bridge.compute_4d_state("manchester_united", "Hello", [])
        man_city_state = bridge.compute_4d_state("manchester_city", "Hello", [])

        assert man_utd_state.z.dialect == man_city_state.z.dialect == "mancunian"

    def test_region_mapping_complete(self):
        """Every club in CLUB_TO_REGION should have a non-empty region."""
        # Premier League regions (original)
        PL_REGIONS = {"north", "midlands", "london", "south", "east"}
        # La Liga regions (added with UFLE-B)
        LA_LIGA_REGIONS = {"castilian", "catalan", "basque", "andalusian", "valencian",
                           "galician", "balearic", "canarian"}
        VALID_REGIONS = PL_REGIONS | LA_LIGA_REGIONS
        for club, region in CLUB_TO_REGION.items():
            assert region in VALID_REGIONS, \
                f"Club {club} has invalid region: {region}"


# =============================================================================
# TEST: RIVALRY ACTIVATION - Y-axis triggers
# =============================================================================

class TestRivalryActivation:
    """Test that mentioning rivals activates the Y-axis."""

    def test_liverpool_mention_activates_man_utd_rivalry(self, bridge):
        """Mentioning Liverpool to Man Utd fan should activate rivalry."""
        state = bridge.compute_4d_state(
            "manchester_united",
            "What do you think about Liverpool?",
            []
        )

        # Y-axis should be activated
        assert state.y.activated == True
        assert state.y.relation_type == "rival"

    def test_man_utd_mention_activates_liverpool_rivalry(self, bridge):
        """Mentioning Man Utd to Liverpool fan should activate rivalry."""
        state = bridge.compute_4d_state(
            "liverpool",
            "How about Manchester United?",
            []
        )

        assert state.y.activated == True

    def test_everton_mention_activates_liverpool_rivalry(self, bridge):
        """Mentioning Everton to Liverpool fan should activate rivalry."""
        state = bridge.compute_4d_state(
            "liverpool",
            "The Everton game was intense",
            []
        )

        assert state.y.activated == True

    def test_neutral_message_no_rivalry(self, bridge):
        """Neutral message should not activate rivalry."""
        state = bridge.compute_4d_state(
            "manchester_united",
            "Nice weather today",
            []
        )

        assert state.y.activated == False

    def test_rivalries_exist_in_unified_kg(self, unified_db):
        """Unified KG should have rivalry edges."""
        cursor = unified_db.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM edges WHERE relationship = 'rival_of'
        """)
        count = cursor.fetchone()[0]

        assert count >= 15, f"Expected at least 15 rivalries, found {count}"

    def test_man_utd_rivalries_in_kg(self, unified_db):
        """Man Utd should have rivalries in KG."""
        cursor = unified_db.cursor()

        cursor.execute("""
            SELECT n1.name as club1, n2.name as club2, e.weight
            FROM edges e
            JOIN nodes n1 ON e.source_id = n1.id
            JOIN nodes n2 ON e.target_id = n2.id
            WHERE e.relationship = 'rival_of'
            AND (n1.name LIKE '%Manchester United%' OR n2.name LIKE '%Manchester United%')
        """)
        rivalries = cursor.fetchall()

        print("\n=== Man Utd Rivalries in KG ===")
        for r in rivalries:
            print(f"  {r['club1']} <-> {r['club2']} (weight: {r['weight']})")

        assert len(rivalries) > 0


# =============================================================================
# TEST: ANTI-GASLIGHTING - Mood has provenance
# =============================================================================

class TestAntiGaslighting:
    """Test that Robert's mood is grounded in reality, not easily manipulated."""

    def test_mood_has_provenance(self, bridge):
        """Mood should come with reason (provenance)."""
        state = bridge.compute_4d_state("manchester_united", "You seem sad today", [])

        # Mood should have reason regardless of what user says
        assert state.x.reason is not None
        assert len(state.x.reason) > 0

    def test_ground_truth_has_timestamp(self, bridge):
        """Ground truth should have timestamp for verification."""
        ground_truth = bridge.get_ground_truth("manchester_united")

        assert "timestamp" in ground_truth
        # Timestamp should be recent (within last hour)
        timestamp = ground_truth.get("timestamp", "")
        if timestamp:
            # Just verify it's a valid ISO timestamp
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {timestamp}")

    def test_mood_not_changed_by_user_claim(self, bridge):
        """User claiming a result shouldn't override computed mood."""
        # First, get the actual mood
        actual_state = bridge.compute_4d_state("manchester_united", "Hello", [])
        actual_mood = actual_state.x.mood
        actual_reason = actual_state.x.reason

        # Now user claims something different
        claimed_state = bridge.compute_4d_state(
            "manchester_united",
            "Man Utd just won 10-0! You must be so happy!",
            []
        )

        # Mood should remain computed from actual data, not claim
        # (The reason should still reference real results)
        assert claimed_state.x.reason == actual_reason


# =============================================================================
# TEST: CONVERSATION TOPICS
# =============================================================================

class TestConversationTopics:
    """Test that conversation topics are generated correctly."""

    def test_topics_returned(self, bridge):
        """Should return conversation topics."""
        topics = bridge.get_conversation_topics("manchester_united")

        # Topics should be a list
        assert isinstance(topics, list)

    def test_topics_have_structure(self, bridge):
        """Topics should have type, priority, content."""
        topics = bridge.get_conversation_topics("manchester_united")

        for topic in topics:
            assert "type" in topic
            assert "priority" in topic
            assert "content" in topic

    def test_topics_included_in_prompt(self, bridge):
        """Topics should be woven into system prompt."""
        state = bridge.compute_4d_state("manchester_united", "Hello", [])
        prompt = bridge.get_system_prompt(state, "manchester_united", include_topics=True)

        # If topics exist, they should appear in prompt
        topics = bridge.get_conversation_topics("manchester_united")
        if topics:
            # Check for topic section marker
            assert "weave naturally" in prompt.lower() or "Things You Know" in prompt


# =============================================================================
# TEST: FACTS AND KNOWLEDGE
# =============================================================================

class TestKnowledgeBase:
    """Test that Robert has access to facts and knowledge."""

    def test_facts_exist_for_man_utd(self, unified_db):
        """Should have facts about Manchester United."""
        cursor = unified_db.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM kb_facts
            WHERE content LIKE '%Manchester United%' OR content LIKE '%Man United%'
        """)
        count = cursor.fetchone()[0]

        assert count > 0, "No facts about Manchester United in KB"

    def test_legends_exist_in_kg(self, unified_db):
        """Should have legend edges for clubs."""
        cursor = unified_db.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM edges WHERE relationship = 'legendary_at'
        """)
        count = cursor.fetchone()[0]

        assert count > 0, "No legend edges in KG"

    def test_sample_facts(self, unified_db):
        """Print sample facts for manual verification."""
        cursor = unified_db.cursor()

        cursor.execute("""
            SELECT fact_id, substr(content, 1, 150) as preview, fact_type
            FROM kb_facts
            WHERE content LIKE '%Manchester United%' OR content LIKE '%United%'
            LIMIT 5
        """)
        facts = cursor.fetchall()

        print("\n=== Sample Man Utd Facts ===")
        for f in facts:
            print(f"  [{f['fact_type']}] {f['preview']}...")


# =============================================================================
# TEST: 4D STATE STRUCTURE
# =============================================================================

class Test4DStateStructure:
    """Test the structure of the 4D state object."""

    def test_4d_state_has_all_dimensions(self, bridge):
        """State should have X, Y, Z, T dimensions."""
        state = bridge.compute_4d_state("manchester_united", "Hello", [])

        assert hasattr(state, 'x'), "Missing X dimension (Emotional)"
        assert hasattr(state, 'y'), "Missing Y dimension (Relational)"
        assert hasattr(state, 'z'), "Missing Z dimension (Linguistic)"
        assert hasattr(state, 't'), "Missing T dimension (Temporal)"

    def test_x_dimension_structure(self, bridge):
        """X dimension should have mood and intensity."""
        state = bridge.compute_4d_state("manchester_united", "Hello", [])

        assert hasattr(state.x, 'mood')
        assert hasattr(state.x, 'intensity')
        assert 0 <= state.x.intensity <= 1

    def test_y_dimension_structure(self, bridge):
        """Y dimension should have activated and relation_type."""
        state = bridge.compute_4d_state("manchester_united", "Hello", [])

        assert hasattr(state.y, 'activated')
        assert isinstance(state.y.activated, bool)

    def test_z_dimension_structure(self, bridge):
        """Z dimension should have dialect and distinctiveness."""
        state = bridge.compute_4d_state("manchester_united", "Hello", [])

        assert hasattr(state.z, 'dialect')
        assert hasattr(state.z, 'distinctiveness')

    def test_t_dimension_structure(self, bridge):
        """T dimension should have step and momentum."""
        state = bridge.compute_4d_state("manchester_united", "Hello", [])

        assert hasattr(state.t, 'step')
        assert hasattr(state.t, 'momentum')


# =============================================================================
# INTEGRATION TEST: Full Flow
# =============================================================================

class TestFullFlow:
    """Test the complete 4D persona flow."""

    def test_complete_man_utd_flow(self, bridge):
        """Test complete flow for Man Utd fan."""
        print("\n" + "=" * 60)
        print("COMPLETE MAN UTD FAN FLOW")
        print("=" * 60)

        # 1. Compute state
        state = bridge.compute_4d_state(
            "manchester_united",
            "What do you think about Liverpool?",
            []
        )

        print(f"\n4D Position:")
        print(f"  X (Emotional): {state.x.mood} (intensity: {state.x.intensity:.2f})")
        print(f"  Y (Relational): {'ACTIVATED' if state.y.activated else 'inactive'}")
        print(f"  Z (Linguistic): {state.z.dialect}")
        print(f"  T (Temporal): Step {state.t.step}")

        # 2. Get ground truth
        ground_truth = bridge.get_ground_truth("manchester_united")
        print(f"\nGround Truth:")
        print(f"  Form: {ground_truth.get('form_string', 'N/A')}")
        print(f"  Mood Reason: {ground_truth.get('mood_reason', 'N/A')[:100]}")

        # 3. Generate prompt
        prompt = bridge.get_system_prompt(state, "manchester_united")
        print(f"\nSystem Prompt (first 500 chars):")
        print(f"  {prompt[:500]}...")

        # Assertions
        assert state.z.dialect == "mancunian"
        assert state.y.activated == True  # Liverpool mentioned
        assert "Manchester United" in prompt or "United" in prompt

    def test_complete_liverpool_flow(self, bridge):
        """Test complete flow for Liverpool fan."""
        state = bridge.compute_4d_state(
            "liverpool",
            "The Everton derby is coming up",
            []
        )

        assert state.z.dialect == "scouse"
        assert state.y.activated == True  # Everton mentioned

    def test_complete_arsenal_flow(self, bridge):
        """Test complete flow for Arsenal fan."""
        # Note: Use "Tottenham" not "Spurs" - KG uses full names
        state = bridge.compute_4d_state(
            "arsenal",
            "Tottenham are in trouble",
            []
        )

        assert state.z.dialect == "cockney"
        assert state.y.activated == True  # Tottenham mentioned


# =============================================================================
# RUN SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
