"""
KG Visualization Test Suite for Soccer-AI
Tests CP7: Knowledge Graph export and visualization
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import database
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_export_kg_to_vis_json():
    """Test 1: Export full KG to vis.js format."""
    print("\n[TEST 1] Export KG to vis.js")
    print("-" * 40)

    graph = database.export_kg_to_vis_json()

    assert "nodes" in graph, "Missing nodes"
    assert "edges" in graph, "Missing edges"
    assert "stats" in graph, "Missing stats"

    assert len(graph["nodes"]) >= 50, f"Expected 50+ nodes, got {len(graph['nodes'])}"
    assert len(graph["edges"]) >= 50, f"Expected 50+ edges, got {len(graph['edges'])}"

    # Check node structure
    node = graph["nodes"][0]
    assert "id" in node, "Node missing id"
    assert "label" in node, "Node missing label"
    assert "group" in node, "Node missing group"
    assert "color" in node, "Node missing color"

    # Check edge structure
    edge = graph["edges"][0]
    assert "from" in edge, "Edge missing from"
    assert "to" in edge, "Edge missing to"
    assert "label" in edge, "Edge missing label"

    print(f"  Nodes: {len(graph['nodes'])}")
    print(f"  Edges: {len(graph['edges'])}")
    print(f"  Node types: {graph['stats']['by_type']}")
    print("  Export KG: PASSED")
    return True


def test_export_subgraph():
    """Test 2: Export subgraph centered on node."""
    print("\n[TEST 2] Export Subgraph")
    print("-" * 40)

    # Get Arsenal's node ID
    node = database.find_kg_node_by_name("Arsenal")
    assert node is not None, "Arsenal node not found"

    # Depth 1
    subgraph = database.export_kg_subgraph(node["node_id"], depth=1)
    assert len(subgraph["nodes"]) > 0, "Subgraph has no nodes"
    assert len(subgraph["nodes"]) < 62, "Subgraph should be smaller than full graph"

    print(f"  Arsenal depth=1: {subgraph['stats']['total_nodes']} nodes")

    # Depth 2
    subgraph2 = database.export_kg_subgraph(node["node_id"], depth=2)
    assert len(subgraph2["nodes"]) >= len(subgraph["nodes"]), "Depth 2 should have >= depth 1 nodes"

    print(f"  Arsenal depth=2: {subgraph2['stats']['total_nodes']} nodes")
    print("  Export subgraph: PASSED")
    return True


def test_graph_endpoint():
    """Test 3: GET /api/v1/graph endpoint."""
    print("\n[TEST 3] Graph API Endpoint")
    print("-" * 40)

    response = client.get("/api/v1/graph")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "nodes" in data["data"]
    assert "edges" in data["data"]
    assert "stats" in data["data"]

    print(f"  Status: {response.status_code}")
    print(f"  Nodes: {len(data['data']['nodes'])}")
    print(f"  Edges: {len(data['data']['edges'])}")
    print("  Graph endpoint: PASSED")
    return True


def test_subgraph_endpoint():
    """Test 4: GET /api/v1/graph/subgraph/{id} endpoint."""
    print("\n[TEST 4] Subgraph API Endpoint")
    print("-" * 40)

    # Get Arsenal's node ID
    node = database.find_kg_node_by_name("Arsenal")

    response = client.get(f"/api/v1/graph/subgraph/{node['node_id']}?depth=1")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "nodes" in data["data"]

    print(f"  Status: {response.status_code}")
    print(f"  Nodes: {data['data']['stats']['total_nodes']}")
    print("  Subgraph endpoint: PASSED")
    return True


def test_team_graph_endpoint():
    """Test 5: GET /api/v1/graph/team/{id} endpoint."""
    print("\n[TEST 5] Team Graph API Endpoint")
    print("-" * 40)

    # Test Arsenal (team_id=3)
    response = client.get("/api/v1/graph/team/3?depth=1")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "team" in data["data"]
    assert data["data"]["team"]["name"] == "Arsenal"

    print(f"  Team: {data['data']['team']['name']}")
    print(f"  Nodes: {data['data']['stats']['total_nodes']}")

    # Test Liverpool
    response = client.get("/api/v1/graph/team/2?depth=2")
    data = response.json()
    print(f"  Liverpool depth=2: {data['data']['stats']['total_nodes']} nodes")

    print("  Team graph endpoint: PASSED")
    return True


def test_kg_viewer_page():
    """Test 6: GET /kg-viewer static page."""
    print("\n[TEST 6] KG Viewer Page")
    print("-" * 40)

    response = client.get("/kg-viewer")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

    # Check for key elements in the HTML
    content = response.text
    assert "Soccer-AI Knowledge Graph" in content
    assert "vis-network" in content
    assert "graph-container" in content

    print(f"  Status: {response.status_code}")
    print(f"  Content length: {len(content)} bytes")
    print(f"  Has vis.js: {'vis-network' in content}")
    print("  KG Viewer page: PASSED")
    return True


def test_node_colors():
    """Test 7: Nodes have correct colors by type."""
    print("\n[TEST 7] Node Colors")
    print("-" * 40)

    graph = database.export_kg_to_vis_json()

    expected_colors = {
        "team": "#e74c3c",
        "legend": "#f39c12",
        "moment": "#3498db"
    }

    for node_type, expected_color in expected_colors.items():
        nodes_of_type = [n for n in graph["nodes"] if n["group"] == node_type]
        if nodes_of_type:
            assert nodes_of_type[0]["color"] == expected_color, \
                f"{node_type} should be {expected_color}"
            print(f"  {node_type}: {expected_color} [OK]")

    print("  Node colors: PASSED")
    return True


def run_all_tests():
    """Run all KG visualization tests."""
    print("=" * 50)
    print("SOCCER-AI KG VISUALIZATION TEST SUITE")
    print("CP7: Knowledge Graph Export & Visualization")
    print("=" * 50)

    tests = [
        ("Export KG to vis.js", test_export_kg_to_vis_json),
        ("Export Subgraph", test_export_subgraph),
        ("Graph API Endpoint", test_graph_endpoint),
        ("Subgraph API Endpoint", test_subgraph_endpoint),
        ("Team Graph Endpoint", test_team_graph_endpoint),
        ("KG Viewer Page", test_kg_viewer_page),
        ("Node Colors", test_node_colors),
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
        print("\n  ALL TESTS PASSED - Visualization Complete!")
        print("  CP7 VERIFIED:")
        print("    - KG export to vis.js format")
        print("    - Subgraph extraction working")
        print("    - API endpoints operational")
        print("    - Static HTML viewer serving")
        print("    - Color coding by node type")
    else:
        print(f"\n  {failed} tests need review")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
