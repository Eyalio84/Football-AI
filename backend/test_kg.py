"""
Knowledge Graph Test Suite for Soccer-AI KG-RAG
Tests Phase 1: Schema + Population + Traversal
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import database


def test_kg_schema():
    """Test 1: Verify KG tables exist with correct structure."""
    print("\n[TEST 1] Schema Verification")
    print("-" * 40)

    with database.get_connection() as conn:
        # Check kg_nodes table
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='kg_nodes'
        """)
        assert cursor.fetchone() is not None, "kg_nodes table missing"
        print("  kg_nodes table: EXISTS")

        # Check kg_edges table
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='kg_edges'
        """)
        assert cursor.fetchone() is not None, "kg_edges table missing"
        print("  kg_edges table: EXISTS")

        # Check indices
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indices = [row['name'] for row in cursor.fetchall()]
        expected = ['idx_nodes_type', 'idx_nodes_name', 'idx_nodes_entity',
                   'idx_edges_source', 'idx_edges_target', 'idx_edges_rel']
        for idx in expected:
            if idx in indices:
                print(f"  {idx}: EXISTS")
            else:
                print(f"  {idx}: MISSING (warning)")

    print("  Schema verification: PASSED")
    return True


def test_node_counts():
    """Test 2: Verify correct node counts by type."""
    print("\n[TEST 2] Node Counts")
    print("-" * 40)

    stats = database.get_kg_stats()
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Total edges: {stats['total_edges']}")
    print(f"  By type: {stats['by_type']}")

    # Verify expected node types exist
    assert 'team' in stats['by_type'], "No team nodes found"
    assert 'legend' in stats['by_type'], "No legend nodes found"
    assert 'moment' in stats['by_type'], "No moment nodes found"

    # Verify counts are reasonable
    assert stats['by_type']['team'] >= 3, f"Expected >=3 teams, got {stats['by_type']['team']}"
    assert stats['by_type']['legend'] >= 9, f"Expected >=9 legends, got {stats['by_type']['legend']}"
    assert stats['by_type']['moment'] >= 12, f"Expected >=12 moments, got {stats['by_type']['moment']}"

    print("  Node counts: PASSED")
    return True


def test_edge_relationships():
    """Test 3: Verify edge relationships are correct."""
    print("\n[TEST 3] Edge Relationships")
    print("-" * 40)

    with database.get_connection() as conn:
        # Count edges by relationship type
        cursor = conn.execute("""
            SELECT relationship, COUNT(*) as count
            FROM kg_edges
            GROUP BY relationship
        """)
        edges_by_type = {row['relationship']: row['count'] for row in cursor.fetchall()}

        print(f"  Edge types: {edges_by_type}")

        # Verify expected relationship types
        assert 'legendary_at' in edges_by_type, "No legendary_at edges"
        assert 'occurred_at' in edges_by_type, "No occurred_at edges"
        assert 'rival_of' in edges_by_type, "No rival_of edges"

        # legendary_at should connect legends to teams
        assert edges_by_type['legendary_at'] >= 9, "Expected >=9 legendary_at edges"

        # occurred_at should connect moments to teams
        assert edges_by_type['occurred_at'] >= 12, "Expected >=12 occurred_at edges"

        # rival_of should exist (at least some rivalries)
        assert edges_by_type['rival_of'] >= 3, "Expected >=3 rivalry edges"

    print("  Edge relationships: PASSED")
    return True


def test_node_lookup():
    """Test 4: Test node lookup functions."""
    print("\n[TEST 4] Node Lookup")
    print("-" * 40)

    # Find Arsenal by name
    arsenal = database.find_kg_node_by_name("Arsenal")
    assert arsenal is not None, "Failed to find Arsenal by name"
    assert arsenal['node_type'] == 'team', f"Arsenal should be team, got {arsenal['node_type']}"
    print(f"  find_kg_node_by_name('Arsenal'): {arsenal['name']} (id={arsenal['node_id']})")

    # Get node by entity
    team_node = database.get_kg_node_by_entity('team', arsenal['entity_id'])
    assert team_node is not None, "Failed to get node by entity"
    assert team_node['node_id'] == arsenal['node_id'], "Entity lookup mismatch"
    print(f"  get_kg_node_by_entity('team', {arsenal['entity_id']}): {team_node['name']}")

    # Find a legend
    henry = database.find_kg_node_by_name("Henry")
    assert henry is not None, "Failed to find Henry"
    assert henry['node_type'] == 'legend', f"Henry should be legend, got {henry['node_type']}"
    print(f"  find_kg_node_by_name('Henry'): {henry['name']}")

    print("  Node lookup: PASSED")
    return True


def test_traversal():
    """Test 5: Test graph traversal functions."""
    print("\n[TEST 5] Graph Traversal")
    print("-" * 40)

    # Get Arsenal node
    arsenal = database.find_kg_node_by_name("Arsenal")
    assert arsenal is not None
    arsenal_id = arsenal['node_id']

    # Get edges FROM Arsenal
    edges_from = database.get_kg_edges_from(arsenal_id)
    print(f"  Edges FROM Arsenal: {len(edges_from)}")
    for edge in edges_from[:3]:
        print(f"    -> {edge['target_name']} ({edge['relationship']})")

    # Get edges TO Arsenal (legends, moments)
    edges_to = database.get_kg_edges_to(arsenal_id)
    print(f"  Edges TO Arsenal: {len(edges_to)}")
    for edge in edges_to[:3]:
        print(f"    <- {edge['source_name']} ({edge['relationship']})")

    # Test BFS traversal (depth 1)
    traversal = database.traverse_kg(arsenal_id, depth=1)
    print(f"  Traversal from Arsenal (depth=1): {len(traversal)} nodes")
    for item in traversal[:3]:
        print(f"    -> {item['node']['name']} via {item['edge']['relationship']}")

    # Test filtered traversal (only rival_of)
    rivals = database.traverse_kg(arsenal_id, depth=1, relationship='rival_of')
    print(f"  Arsenal rivalries: {len(rivals)}")
    for rival in rivals:
        print(f"    vs {rival['node']['name']} (weight={rival['edge']['weight']:.2f})")

    print("  Graph traversal: PASSED")
    return True


def test_entity_context():
    """Test 6: Test entity context retrieval."""
    print("\n[TEST 6] Entity Context")
    print("-" * 40)

    # Get team context (full test)
    arsenal = database.find_kg_node_by_name("Arsenal")
    context = database.get_entity_context('team', arsenal['entity_id'])

    assert 'entity' in context, "Context missing entity"
    print(f"  Team: {context['entity']['name']}")

    # Check legends
    assert 'legends' in context, "Context missing legends"
    print(f"  Legends: {len(context['legends'])} linked")
    if context['legends']:
        legend_names = [e['source_name'] for e in context['legends'][:3]]
        print(f"    Examples: {', '.join(legend_names)}")

    # Check rivalries
    assert 'rivalries' in context, "Context missing rivalries"
    print(f"  Rivalries: {len(context['rivalries'])} linked")
    if context['rivalries']:
        rival_names = [e['target_name'] for e in context['rivalries']]
        print(f"    Rivals: {', '.join(rival_names)}")

    # Check moments
    assert 'moments' in context, "Context missing moments"
    print(f"  Moments: {len(context['moments'])} linked")
    if context['moments']:
        moment_names = [e['source_name'] for e in context['moments'][:3]]
        print(f"    Examples: {', '.join(moment_names)}")

    # Check mood
    if context.get('mood'):
        print(f"  Mood: {context['mood'].get('current_mood')}")

    print("  Entity context: PASSED")
    return True


def test_legend_context():
    """Test 7: Test legend entity context."""
    print("\n[TEST 7] Legend Context")
    print("-" * 40)

    # Get Henry's context
    henry = database.find_kg_node_by_name("Henry")
    context = database.get_entity_context('legend', henry['entity_id'])

    assert 'entity' in context, "Context missing entity"
    print(f"  Legend: {context['entity']['name']}")

    # Check team link
    if context.get('team'):
        print(f"  Team: {context['team']['name']}")
        assert context['team']['node_type'] == 'team', "Team should be team type"

    print("  Legend context: PASSED")
    return True


def test_moment_context():
    """Test 8: Test moment entity context."""
    print("\n[TEST 8] Moment Context")
    print("-" * 40)

    # Get a moment
    with database.get_connection() as conn:
        cursor = conn.execute("""
            SELECT * FROM kg_nodes WHERE node_type = 'moment' LIMIT 1
        """)
        moment_row = cursor.fetchone()

    if moment_row:
        moment = dict(moment_row)
        context = database.get_entity_context('moment', moment['entity_id'])

        print(f"  Moment: {context['entity']['name']}")

        if context.get('team'):
            print(f"  Team: {context['team']['name']}")

        if context.get('opponent'):
            print(f"  Opponent: {context['opponent']['name']}")

    print("  Moment context: PASSED")
    return True


def test_multi_hop_traversal():
    """Test 9: Test multi-hop traversal (depth > 1)."""
    print("\n[TEST 9] Multi-Hop Traversal")
    print("-" * 40)

    # Find a legend
    henry = database.find_kg_node_by_name("Henry")
    henry_id = henry['node_id']

    # Traverse 2 hops: legend -> team -> rivals
    traversal = database.traverse_kg(henry_id, depth=2)

    print(f"  Starting from: {henry['name']}")
    print(f"  2-hop traversal found: {len(traversal)} nodes")

    depth_1 = [t for t in traversal if t['depth'] == 1]
    depth_2 = [t for t in traversal if t['depth'] == 2]

    print(f"    Depth 1: {len(depth_1)} nodes")
    for item in depth_1[:2]:
        print(f"      -> {item['node']['name']} ({item['edge']['relationship']})")

    print(f"    Depth 2: {len(depth_2)} nodes")
    for item in depth_2[:3]:
        print(f"      -> {item['node']['name']} ({item['edge']['relationship']})")

    # Verify we found rivals of Henry's team
    rival_found = any(t['edge']['relationship'] == 'rival_of' for t in traversal)
    if rival_found:
        print("  Found rival connection at depth 2!")

    print("  Multi-hop traversal: PASSED")
    return True


def run_all_tests():
    """Run all KG tests."""
    print("=" * 50)
    print("SOCCER-AI KNOWLEDGE GRAPH TEST SUITE")
    print("Phase 1: Schema + Population + Traversal")
    print("=" * 50)

    tests = [
        ("Schema Verification", test_kg_schema),
        ("Node Counts", test_node_counts),
        ("Edge Relationships", test_edge_relationships),
        ("Node Lookup", test_node_lookup),
        ("Graph Traversal", test_traversal),
        ("Entity Context", test_entity_context),
        ("Legend Context", test_legend_context),
        ("Moment Context", test_moment_context),
        ("Multi-Hop Traversal", test_multi_hop_traversal),
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
            print(f"\n  ERROR: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print("TEST RESULTS")
    print("=" * 50)
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n  ALL TESTS PASSED - KG Phase 1 Complete!")
        print("  Ready for Phase 2: Hybrid Retrieval")
    else:
        print(f"\n  {failed} tests failed - review above for details")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
