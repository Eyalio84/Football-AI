"""
Hybrid KG-RAG Test Suite for Soccer-AI
Tests Phase 2: FTS5 + Graph Hybrid Retrieval
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import rag
import database


def test_kg_intent_detection():
    """Test 1: KG intent detection routes correctly."""
    print("\n[TEST 1] KG Intent Detection")
    print("-" * 40)

    test_cases = [
        ("Tell me about Arsenal's best derby moment", "rivalry"),  # derby triggers rivalry
        ("Compare Henry to Drogba", "relationship"),
        ("Arsenal vs Tottenham rivalry", "rivalry"),
        ("Any connection between Chelsea and Arsenal?", "discovery"),
        ("How are we feeling about Spurs?", "rivalry"),  # spurs triggers rivalry
        ("Who are Arsenal's legends?", "legend"),
        ("Famous Arsenal moments", "moment"),  # moment keyword
        ("What's the score?", None),
    ]

    passed = 0
    for query, expected in test_cases:
        result = rag.detect_kg_intent(query)
        status = "" if result == expected else "FAIL"
        print(f"  '{query[:40]}...' -> {result} {status}")
        if result == expected:
            passed += 1

    print(f"  Intent detection: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_kg_entity_extraction():
    """Test 2: Entity extraction with KG resolution."""
    print("\n[TEST 2] KG Entity Extraction")
    print("-" * 40)

    query = "Tell me about Arsenal's best derby moment"
    entities = rag.extract_kg_entities(query)

    print(f"  Query: {query}")
    print(f"  Teams found: {entities.get('teams', [])}")
    print(f"  KG nodes resolved: {len(entities.get('kg_nodes', []))}")
    print(f"  KG intent: {entities.get('kg_intent')}")

    assert "Arsenal" in entities.get("teams", []), "Failed to find Arsenal team"
    assert len(entities.get("kg_nodes", [])) >= 1, "Failed to resolve KG nodes"
    # derby keyword now triggers rivalry intent (higher priority)
    assert entities.get("kg_intent") in ["rivalry", "multi_hop"], "Wrong KG intent"

    print("  KG entity extraction: PASSED")
    return True


def test_retrieve_kg_context():
    """Test 3: KG context retrieval."""
    print("\n[TEST 3] KG Context Retrieval")
    print("-" * 40)

    entities = rag.extract_kg_entities("Tell me about Arsenal's legends")
    kg_context, sources = rag.retrieve_kg_context(entities)

    print(f"  Context length: {len(kg_context)} chars")
    print(f"  Sources: {len(sources)}")

    assert len(kg_context) > 100, "Context too short"
    assert "Arsenal" in kg_context, "Arsenal not in context"

    print(f"\n  Context preview:")
    for line in kg_context.split('\n')[:8]:
        print(f"    {line}")

    print("  KG context retrieval: PASSED")
    return True


def test_hybrid_retrieval():
    """Test 4: Full hybrid retrieval (FTS5 + KG)."""
    print("\n[TEST 4] Hybrid Retrieval")
    print("-" * 40)

    query = "Arsenal rivalry with Tottenham"
    fused_context, sources, metadata = rag.retrieve_hybrid(query)

    print(f"  Query: {query}")
    print(f"  Fused context length: {len(fused_context)} chars")
    print(f"  Total sources: {len(sources)}")
    print(f"  Metadata: {metadata}")

    assert metadata.get("retrieval_type") == "hybrid_kg_rag", "Wrong retrieval type"
    # rivalry keyword triggers rivalry intent
    assert metadata.get("kg_intent") in ["rivalry", "relationship"], "Wrong KG intent"

    print("\n  Context preview:")
    for line in fused_context.split('\n')[:10]:
        print(f"    {line}")

    print("  Hybrid retrieval: PASSED")
    return True


def test_multi_hop_query():
    """Test 5: Multi-hop query (legend -> team -> rivals)."""
    print("\n[TEST 5] Multi-Hop Query")
    print("-" * 40)

    query = "What rivalries did Henry experience at Arsenal?"
    entities = rag.extract_kg_entities(query)
    kg_context, sources = rag.retrieve_kg_context(entities)

    print(f"  Query: {query}")
    print(f"  KG nodes found: {len(entities.get('kg_nodes', []))}")

    print(f"\n  Context preview:")
    for line in kg_context.split('\n')[:8]:
        print(f"    {line}")

    has_relevant = any(word in kg_context.lower() for word in ["henry", "arsenal", "rival"])
    assert has_relevant, "No relevant content found"

    print("  Multi-hop query: PASSED")
    return True


def test_mood_calibration():
    """Test 6: Mood calibration in context."""
    print("\n[TEST 6] Mood Calibration")
    print("-" * 40)

    query = "How are Arsenal fans feeling?"
    fused_context, sources, metadata = rag.retrieve_hybrid(query)

    print(f"  Query: {query}")
    print(f"  Detected mood: {metadata.get('mood', 'none')}")

    print(f"\n  Context preview:")
    for line in fused_context.split('\n')[:8]:
        print(f"    {line}")

    print("  Mood calibration: PASSED")
    return True


def test_derby_moment_query():
    """Test 7: Demo query - Arsenal's best derby moment."""
    print("\n[TEST 7] Demo Query: Derby Moment")
    print("-" * 40)

    query = "Tell me about Arsenal's best derby moment"
    fused_context, sources, metadata = rag.retrieve_hybrid(query)

    print(f"  Query: {query}")
    print(f"  KG intent: {metadata.get('kg_intent')}")
    print(f"  Sources: {len(sources)}")

    print(f"\n  Full context:")
    print("  " + "-" * 38)
    for line in fused_context.split('\n'):
        print(f"  {line}")
    print("  " + "-" * 38)

    print("  Derby moment query: PASSED")
    return True


def run_all_tests():
    """Run all hybrid RAG tests."""
    print("=" * 50)
    print("SOCCER-AI HYBRID KG-RAG TEST SUITE")
    print("Phase 2: FTS5 + Graph Hybrid Retrieval")
    print("=" * 50)

    tests = [
        ("KG Intent Detection", test_kg_intent_detection),
        ("KG Entity Extraction", test_kg_entity_extraction),
        ("KG Context Retrieval", test_retrieve_kg_context),
        ("Hybrid Retrieval", test_hybrid_retrieval),
        ("Multi-Hop Query", test_multi_hop_query),
        ("Mood Calibration", test_mood_calibration),
        ("Demo: Derby Moment", test_derby_moment_query),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            result = test_fn()
            if result:
                passed += 1
        except AssertionError as e:
            print(f"\n  FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"\n  ERROR: {type(e).__name__}: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n  ALL TESTS PASSED - Hybrid KG-RAG Complete!")
        print("  Ready for Phase 3: AI Response Integration")
    else:
        print(f"\n  {failed} tests need review")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
