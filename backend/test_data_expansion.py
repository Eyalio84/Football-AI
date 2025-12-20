"""
Data Expansion Test Suite for Soccer-AI
Tests CP4: All Top 6 Premier League clubs with legends, moments, rivalries
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import database
import rag


# Top 6 clubs with their IDs
TOP_6_CLUBS = {
    1: "Manchester City",
    2: "Liverpool",
    3: "Arsenal",
    4: "Chelsea",
    5: "Manchester United",
    6: "Tottenham"
}

# Expected legends per club
EXPECTED_LEGENDS = {
    "Manchester City": ["Sergio Aguero", "Vincent Kompany", "David Silva"],
    "Liverpool": ["Steven Gerrard", "Kenny Dalglish", "Ian Rush"],
    "Arsenal": ["Thierry Henry", "Dennis Bergkamp", "Patrick Vieira"],
    "Chelsea": ["Didier Drogba", "John Terry", "Frank Lampard"],
    "Manchester United": ["Eric Cantona", "Ryan Giggs", "Wayne Rooney"],
    "Tottenham": ["Harry Kane", "Jimmy Greaves", "Glenn Hoddle"]
}

# Key rivalry pairs (both directions should exist)
KEY_RIVALRIES = [
    ("Arsenal", "Tottenham", 10),       # North London Derby
    ("Manchester City", "Manchester United", 10),  # Manchester Derby
    ("Liverpool", "Manchester United", 10),  # Northwest Derby
    ("Arsenal", "Manchester United", 8),  # Historical
    ("Chelsea", "Tottenham", 8),         # London derby
]


def test_top_6_clubs_exist():
    """Test 1: All Top 6 clubs exist in database."""
    print("\n[TEST 1] Top 6 Clubs Exist")
    print("-" * 40)

    for club_name in TOP_6_CLUBS.values():
        team = database.get_team_by_name(club_name)
        assert team is not None, f"Missing team: {club_name}"
        print(f"  [OK] {club_name} (ID: {team['id']})")

    print("  Top 6 clubs exist: PASSED")
    return True


def test_kg_node_counts():
    """Test 2: KG has minimum expected counts."""
    print("\n[TEST 2] KG Node Counts")
    print("-" * 40)

    stats = database.get_kg_stats()

    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Total edges: {stats['total_edges']}")
    print(f"  By type: {stats['by_type']}")

    # Minimum expected counts after expansion
    assert stats['total_nodes'] >= 50, f"Expected 50+ nodes, got {stats['total_nodes']}"
    assert stats['total_edges'] >= 50, f"Expected 50+ edges, got {stats['total_edges']}"
    assert stats['by_type'].get('legend', 0) >= 18, "Expected 18+ legends (3 per Top 6)"
    assert stats['by_type'].get('team', 0) >= 6, "Expected 6+ team nodes"

    print("  KG node counts: PASSED")
    return True


def test_all_legends_in_kg():
    """Test 3: All expected legends are in KG."""
    print("\n[TEST 3] All Legends in KG")
    print("-" * 40)

    missing = []
    found = 0

    for club, legends in EXPECTED_LEGENDS.items():
        for legend_name in legends:
            node = database.find_kg_node_by_name(legend_name)
            if node:
                found += 1
                print(f"  [OK] {legend_name} ({club})")
            else:
                missing.append(f"{legend_name} ({club})")
                print(f"  [FAIL] {legend_name} ({club}) - NOT FOUND")

    assert len(missing) == 0, f"Missing legends: {missing}"
    print(f"\n  All {found} legends in KG: PASSED")
    return True


def test_club_moments_exist():
    """Test 4: Each Top 6 club has moments."""
    print("\n[TEST 4] Club Moments")
    print("-" * 40)

    for team_id, club_name in TOP_6_CLUBS.items():
        moments = database.get_club_moments(team_id)
        assert len(moments) >= 3, f"{club_name} should have 3+ moments, got {len(moments)}"
        print(f"  [OK] {club_name}: {len(moments)} moments")
        for m in moments[:2]:
            print(f"       - {m['title']} ({m.get('emotion', 'n/a')})")

    print("\n  All clubs have moments: PASSED")
    return True


def test_key_rivalries_exist():
    """Test 5: Key rivalries are in database."""
    print("\n[TEST 5] Key Rivalries")
    print("-" * 40)

    for team1, team2, expected_intensity in KEY_RIVALRIES:
        team1_obj = database.get_team_by_name(team1)
        rivalries = database.get_club_rivalries(team1_obj['id'])

        team2_obj = database.get_team_by_name(team2)
        found = False
        actual_intensity = None

        for r in rivalries:
            if r['rival_team_id'] == team2_obj['id']:
                found = True
                actual_intensity = r['intensity']
                break

        assert found, f"Missing rivalry: {team1} -> {team2}"
        assert actual_intensity == expected_intensity, \
            f"{team1} vs {team2}: expected intensity {expected_intensity}, got {actual_intensity}"

        print(f"  [OK] {team1} -> {team2} (intensity: {actual_intensity})")

    print("\n  Key rivalries exist: PASSED")
    return True


def test_kg_rivalry_edges():
    """Test 6: Rivalry edges exist in KG."""
    print("\n[TEST 6] KG Rivalry Edges")
    print("-" * 40)

    for team_name in ["Arsenal", "Liverpool", "Manchester City"]:
        node = database.find_kg_node_by_name(team_name)
        assert node is not None, f"No KG node for {team_name}"

        edges = database.get_kg_edges_from(node['node_id'], 'rival_of')
        print(f"  {team_name} rivalries: {len(edges)}")

        for edge in edges:
            target = database.get_kg_node(edge['target_id'])
            print(f"    -> {target['name']} (weight: {edge['weight']:.2f})")

        assert len(edges) >= 1, f"{team_name} should have rivalry edges"

    print("\n  KG rivalry edges: PASSED")
    return True


def test_hybrid_retrieval_expanded():
    """Test 7: Hybrid retrieval works for new clubs."""
    print("\n[TEST 7] Hybrid Retrieval - Expanded Clubs")
    print("-" * 40)

    test_queries = [
        ("Tell me about Liverpool's legends", "Liverpool"),
        ("Man City's biggest moment", "Manchester City"),
        ("Tottenham rivalry with Arsenal", "Tottenham"),
        ("Steven Gerrard at Liverpool", "Liverpool"),
        ("Sergio Aguero Manchester City legend", "Manchester City"),
    ]

    for query, expected_club in test_queries:
        context, sources, metadata = rag.retrieve_hybrid(query)

        print(f"  Query: \"{query[:40]}...\"")
        print(f"  Sources: {len(sources)}, Intent: {metadata.get('kg_intent')}")

        # Should have found relevant context
        assert len(context) > 100, f"Context too short for: {query}"
        assert expected_club.lower() in context.lower() or any(
            expected_club.lower() in str(s).lower() for s in sources
        ), f"Expected {expected_club} in results"

    print("\n  Hybrid retrieval expanded: PASSED")
    return True


def test_multi_hop_new_clubs():
    """Test 8: Multi-hop traversal works for new clubs."""
    print("\n[TEST 8] Multi-Hop - New Clubs")
    print("-" * 40)

    # Test: Aguero -> Man City -> rivals
    aguero = database.find_kg_node_by_name("Aguero")
    assert aguero is not None, "Aguero node not found"

    traversal = database.traverse_kg(aguero['node_id'], depth=2)

    print(f"  Starting from: {aguero['name']}")
    print(f"  Multi-hop found: {len(traversal)} connections")

    for item in traversal:
        indent = "  " * item['depth']
        print(f"    {indent}-> {item['node']['name']} ({item['edge']['relationship']})")

    # Should find Man City at depth 1
    depth_1 = [t for t in traversal if t['depth'] == 1]
    found_city = any('City' in t['node']['name'] for t in depth_1)
    assert found_city, "Should find Man City from Aguero"

    # Should find rivals at depth 2
    depth_2 = [t for t in traversal if t['depth'] == 2]
    assert len(depth_2) >= 1, "Should find rivals at depth 2"

    print("\n  Multi-hop new clubs: PASSED")
    return True


def run_all_tests():
    """Run all data expansion tests."""
    print("=" * 50)
    print("SOCCER-AI DATA EXPANSION TEST SUITE")
    print("CP4: Top 6 Premier League Clubs")
    print("=" * 50)

    tests = [
        ("Top 6 Clubs Exist", test_top_6_clubs_exist),
        ("KG Node Counts", test_kg_node_counts),
        ("All Legends in KG", test_all_legends_in_kg),
        ("Club Moments", test_club_moments_exist),
        ("Key Rivalries", test_key_rivalries_exist),
        ("KG Rivalry Edges", test_kg_rivalry_edges),
        ("Hybrid Retrieval Expanded", test_hybrid_retrieval_expanded),
        ("Multi-Hop New Clubs", test_multi_hop_new_clubs),
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
        print("\n  ALL TESTS PASSED - Data Expansion Complete!")
        print("  CP4 VERIFIED:")
        print("    - 6 Top clubs with full data")
        print("    - 18 legends in KG")
        print("    - All major rivalries tracked")
        print("    - Hybrid retrieval works for all clubs")
        print("    - Multi-hop traversal verified")
    else:
        print(f"\n  {failed} tests need review")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
