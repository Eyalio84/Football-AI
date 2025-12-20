#!/usr/bin/env python3
"""
Soccer-AI Architectural KG Query Interface

Query the architectural knowledge graph with semantic search and structural queries.
Supports finding endpoints, personas, dependencies, and architectural patterns.

Usage:
  python3 query_architectural_kg.py "how does chat work"           # Semantic search
  python3 query_architectural_kg.py --endpoints                    # List all API endpoints
  python3 query_architectural_kg.py --personas                     # List all fan personas
  python3 query_architectural_kg.py --trace "api_chat" "database" # Find path
  python3 query_architectural_kg.py --depends-on "rag_engine"     # Find dependencies
  python3 query_architectural_kg.py --stats                        # Show statistics
"""

import sqlite3
import numpy as np
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json

# Paths
BASE_DIR = Path(__file__).parent
KG_DB = BASE_DIR / "soccer_ai_architecture_kg.db"
EMBEDDINGS_FILE = BASE_DIR / "architectural_embeddings.npz"


class ArchitecturalKGQuery:
    """Query interface for Soccer-AI architectural knowledge graph"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.conn = sqlite3.connect(KG_DB)
        self.cursor = self.conn.cursor()

        # Load embeddings
        if EMBEDDINGS_FILE.exists():
            self._load_embeddings()
        else:
            self.embeddings = None
            if verbose:
                print("⚠️  Embeddings not found. Semantic search disabled.")
                print(f"   Run: python3 train_architectural_embeddings.py")

    def _load_embeddings(self):
        """Load pre-trained embeddings"""
        data = np.load(EMBEDDINGS_FILE)
        self.node_ids = data['node_ids']
        self.embeddings_matrix = data['embeddings']
        self.node_names = data['node_names']
        self.node_types = data['node_types']

        # Create lookup dict
        self.embeddings = {
            int(node_id): self.embeddings_matrix[i]
            for i, node_id in enumerate(self.node_ids)
        }

        if self.verbose:
            print(f"✓ Loaded embeddings for {len(self.embeddings)} nodes")

    def semantic_search(self, query: str, k: int = 5, node_type: Optional[str] = None) -> List[Dict]:
        """
        Semantic search using embeddings

        Args:
            query: Search query
            k: Number of results
            node_type: Filter by node type (api_endpoint, persona, table, etc.)

        Returns:
            List of results with scores
        """
        if self.embeddings is None:
            print("❌ Embeddings not loaded. Cannot perform semantic search.")
            return []

        # Embed query (simple bag-of-words approximation)
        query_embedding = self._embed_query(query)

        # Compute similarities
        results = []
        for i, node_id in enumerate(self.node_ids):
            node_id = int(node_id)
            node_type_actual = str(self.node_types[i])

            # Filter by type if requested
            if node_type and node_type != node_type_actual:
                continue

            # Cosine similarity
            node_emb = self.embeddings[node_id]
            similarity = np.dot(query_embedding, node_emb)

            # Get node details
            self.cursor.execute("""
                SELECT node_id, name, type, description, properties
                FROM kg_nodes
                WHERE node_id = ?
            """, (node_id,))

            row = self.cursor.fetchone()
            if row:
                results.append({
                    'node_id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'description': row[3] or '',
                    'properties': json.loads(row[4]) if row[4] else {},
                    'score': float(similarity)
                })

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:k]

    def _embed_query(self, query: str) -> np.ndarray:
        """Simple query embedding (bag of words with node embeddings)"""
        query_lower = query.lower()
        tokens = query_lower.split()

        # Find matching node names and average their embeddings
        matching_embeddings = []
        for token in tokens:
            for i, name in enumerate(self.node_names):
                if token in str(name).lower():
                    node_id = int(self.node_ids[i])
                    matching_embeddings.append(self.embeddings[node_id])

        if matching_embeddings:
            query_emb = np.mean(matching_embeddings, axis=0)
        else:
            # Fallback: random embedding
            query_emb = np.random.randn(256)

        # Normalize
        query_emb /= np.linalg.norm(query_emb)
        return query_emb

    def list_endpoints(self, method: Optional[str] = None) -> List[Dict]:
        """
        List all API endpoints

        Args:
            method: Filter by HTTP method (GET, POST, etc.)
        """
        query = """
            SELECT node_id, name, description, properties
            FROM kg_nodes
            WHERE type = 'api_endpoint'
        """

        if method:
            query += f" AND json_extract(properties, '$.method') = '{method.upper()}'"

        query += " ORDER BY name"

        self.cursor.execute(query)
        results = []
        for row in self.cursor.fetchall():
            props = json.loads(row[3]) if row[3] else {}
            results.append({
                'node_id': row[0],
                'name': row[1],
                'description': row[2] or '',
                'method': props.get('method', ''),
                'path': props.get('path', ''),
                'function': props.get('function_name', '')
            })

        return results

    def list_personas(self) -> List[Dict]:
        """List all fan personas"""
        self.cursor.execute("""
            SELECT node_id, name, description, properties
            FROM kg_nodes
            WHERE type = 'persona'
            ORDER BY name
        """)

        results = []
        for row in self.cursor.fetchall():
            props = json.loads(row[3]) if row[3] else {}
            results.append({
                'node_id': row[0],
                'name': row[1],
                'description': row[2] or '',
                'club_key': props.get('club_key', ''),
                'display_name': props.get('display_name', ''),
                'nickname': props.get('nickname', ''),
                'colors': props.get('colors', '')
            })

        return results

    def find_dependencies(self, component_name: str, direction: str = 'both') -> Dict:
        """
        Find what a component depends on (incoming) or what depends on it (outgoing)

        Args:
            component_name: Name or identifier of component
            direction: 'incoming', 'outgoing', or 'both'
        """
        # Find node
        self.cursor.execute("""
            SELECT node_id, name, type
            FROM kg_nodes
            WHERE name LIKE ? OR node_id LIKE ?
        """, (f"%{component_name}%", f"%{component_name}%"))

        node = self.cursor.fetchone()
        if not node:
            return {'error': f"Component '{component_name}' not found"}

        node_id, name, node_type = node
        result = {
            'component': name,
            'type': node_type,
            'node_id': node_id
        }

        # Get incoming dependencies (what this component depends on)
        if direction in ['incoming', 'both']:
            self.cursor.execute("""
                SELECT n.node_id, n.name, n.type, e.relationship, e.weight
                FROM kg_edges e
                JOIN kg_nodes n ON e.from_node = n.node_id
                WHERE e.to_node = ?
                ORDER BY e.weight DESC, n.name
            """, (node_id,))

            result['depends_on'] = [
                {
                    'name': row[1],
                    'type': row[2],
                    'relationship': row[3],
                    'weight': row[4]
                }
                for row in self.cursor.fetchall()
            ]

        # Get outgoing dependencies (what depends on this component)
        if direction in ['outgoing', 'both']:
            self.cursor.execute("""
                SELECT n.node_id, n.name, n.type, e.relationship, e.weight
                FROM kg_edges e
                JOIN kg_nodes n ON e.to_node = n.node_id
                WHERE e.from_node = ?
                ORDER BY e.weight DESC, n.name
            """, (node_id,))

            result['dependents'] = [
                {
                    'name': row[1],
                    'type': row[2],
                    'relationship': row[3],
                    'weight': row[4]
                }
                for row in self.cursor.fetchall()
            ]

        return result

    def trace_path(self, from_component: str, to_component: str, max_depth: int = 5) -> Dict:
        """
        Find path between two components using BFS

        Args:
            from_component: Starting component name
            to_component: Target component name
            max_depth: Maximum path length
        """
        # Find nodes
        self.cursor.execute("""
            SELECT node_id, name FROM kg_nodes
            WHERE name LIKE ? OR node_id LIKE ?
        """, (f"%{from_component}%", f"%{from_component}%"))
        start = self.cursor.fetchone()

        self.cursor.execute("""
            SELECT node_id, name FROM kg_nodes
            WHERE name LIKE ? OR node_id LIKE ?
        """, (f"%{to_component}%", f"%{to_component}%"))
        end = self.cursor.fetchone()

        if not start:
            return {'error': f"Component '{from_component}' not found"}
        if not end:
            return {'error': f"Component '{to_component}' not found"}

        start_id, start_name = start
        end_id, end_name = end

        # BFS to find shortest path
        from collections import deque
        queue = deque([(start_id, [start_id])])
        visited = {start_id}

        while queue:
            current_id, path = queue.popleft()

            if len(path) > max_depth:
                continue

            if current_id == end_id:
                # Found path! Get details
                path_details = []
                for i, node_id in enumerate(path):
                    self.cursor.execute("""
                        SELECT name, type FROM kg_nodes WHERE node_id = ?
                    """, (node_id,))
                    node = self.cursor.fetchone()

                    step = {
                        'node_id': node_id,
                        'name': node[0],
                        'type': node[1]
                    }

                    # Get relationship to next node
                    if i < len(path) - 1:
                        next_id = path[i + 1]
                        self.cursor.execute("""
                            SELECT relationship FROM kg_edges
                            WHERE from_node = ? AND to_node = ?
                        """, (node_id, next_id))
                        rel = self.cursor.fetchone()
                        step['relationship'] = rel[0] if rel else 'unknown'

                    path_details.append(step)

                return {
                    'from': start_name,
                    'to': end_name,
                    'path_length': len(path) - 1,
                    'path': path_details
                }

            # Explore neighbors
            self.cursor.execute("""
                SELECT to_node FROM kg_edges WHERE from_node = ?
            """, (current_id,))

            for (neighbor_id,) in self.cursor.fetchall():
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return {
            'from': start_name,
            'to': end_name,
            'path': None,
            'message': f"No path found within {max_depth} steps"
        }

    def get_statistics(self) -> Dict:
        """Get KG statistics"""
        stats = {}

        # Total nodes/edges
        self.cursor.execute("SELECT COUNT(*) FROM kg_nodes")
        stats['total_nodes'] = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM kg_edges")
        stats['total_edges'] = self.cursor.fetchone()[0]

        # Nodes by type
        self.cursor.execute("""
            SELECT type, COUNT(*) FROM kg_nodes GROUP BY type ORDER BY COUNT(*) DESC
        """)
        stats['nodes_by_type'] = {row[0]: row[1] for row in self.cursor.fetchall()}

        # Edges by relationship
        self.cursor.execute("""
            SELECT relationship, COUNT(*) FROM kg_edges GROUP BY relationship ORDER BY COUNT(*) DESC
        """)
        stats['edges_by_relationship'] = {row[0]: row[1] for row in self.cursor.fetchall()}

        # Most connected nodes
        self.cursor.execute("""
            SELECT n.name, n.type, COUNT(e.from_node) as connections
            FROM kg_nodes n
            LEFT JOIN kg_edges e ON n.node_id = e.from_node OR n.node_id = e.to_node
            GROUP BY n.node_id
            ORDER BY connections DESC
            LIMIT 10
        """)
        stats['most_connected'] = [
            {'name': row[0], 'type': row[1], 'connections': row[2]}
            for row in self.cursor.fetchall()
        ]

        return stats

    def find_rivalries(self) -> List[Dict]:
        """Find persona rivalries"""
        self.cursor.execute("""
            SELECT
                n1.name as persona1,
                n2.name as persona2,
                e.weight
            FROM kg_edges e
            JOIN kg_nodes n1 ON e.from_node = n1.node_id
            JOIN kg_nodes n2 ON e.to_node = n2.node_id
            WHERE e.relationship = 'rival_of'
            ORDER BY e.weight DESC, n1.name
        """)

        return [
            {
                'persona1': row[0],
                'persona2': row[1],
                'intensity': row[2]
            }
            for row in self.cursor.fetchall()
        ]

    def close(self):
        """Close database connection"""
        self.conn.close()


def print_results(results: List[Dict], result_type: str = "search"):
    """Pretty print results"""
    if not results:
        print("No results found.")
        return

    if result_type == "search":
        print(f"\n{'Score':<8} {'Name':<40} {'Type':<15}")
        print("=" * 70)
        for r in results:
            score = f"{r['score']:.3f}"
            name = r['name'][:38]
            node_type = r['type']
            print(f"{score:<8} {name:<40} {node_type:<15}")
            if r['description']:
                desc = r['description'][:65]
                print(f"         → {desc}")

    elif result_type == "endpoints":
        print(f"\n{'Method':<8} {'Path':<35} {'Function':<25}")
        print("=" * 70)
        for r in results:
            method = r['method']
            path = r['path'][:33]
            function = r['function'][:23]
            print(f"{method:<8} {path:<35} {function:<25}")

    elif result_type == "personas":
        print(f"\n{'Club':<25} {'Nickname':<20} {'Colors':<25}")
        print("=" * 70)
        for r in results:
            display = r['display_name'][:23]
            nickname = r['nickname'][:18]
            colors = r['colors'][:23]
            print(f"{display:<25} {nickname:<20} {colors:<25}")

    elif result_type == "rivalries":
        print(f"\n{'Persona 1':<25} {'Persona 2':<25} {'Intensity':<10}")
        print("=" * 60)
        for r in results:
            p1 = r['persona1'][:23]
            p2 = r['persona2'][:23]
            intensity = f"{r['intensity']:.1f}"
            print(f"{p1:<25} {p2:<25} {intensity:<10}")


def main():
    parser = argparse.ArgumentParser(
        description="Query the Soccer-AI Architectural Knowledge Graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 query_architectural_kg.py "how does the chat endpoint work"
  python3 query_architectural_kg.py --endpoints
  python3 query_architectural_kg.py --endpoints --method POST
  python3 query_architectural_kg.py --personas
  python3 query_architectural_kg.py --rivalries
  python3 query_architectural_kg.py --depends-on "rag_engine"
  python3 query_architectural_kg.py --trace "api_chat" "haiku_api"
  python3 query_architectural_kg.py --stats
        """
    )

    # Main query
    parser.add_argument('query', nargs='?', help='Semantic search query')

    # Listing commands
    parser.add_argument('--endpoints', action='store_true', help='List all API endpoints')
    parser.add_argument('--method', help='Filter endpoints by HTTP method')
    parser.add_argument('--personas', action='store_true', help='List all fan personas')
    parser.add_argument('--rivalries', action='store_true', help='Show persona rivalries')

    # Dependency commands
    parser.add_argument('--depends-on', metavar='COMPONENT', help='Find what depends on component')
    parser.add_argument('--trace', nargs=2, metavar=('FROM', 'TO'), help='Find path between components')

    # Info commands
    parser.add_argument('--stats', action='store_true', help='Show KG statistics')

    # Options
    parser.add_argument('-k', type=int, default=5, help='Number of results (default: 5)')
    parser.add_argument('--type', help='Filter by node type')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')

    args = parser.parse_args()

    # Check if KG exists
    if not KG_DB.exists():
        print(f"❌ Knowledge graph not found: {KG_DB}")
        print(f"   Run: python3 build_architectural_kg.py")
        return 1

    # Initialize query system
    kg = ArchitecturalKGQuery(verbose=not args.quiet)

    try:
        # Handle different query types
        if args.stats:
            stats = kg.get_statistics()
            print("\n" + "="*60)
            print("SOCCER-AI ARCHITECTURAL KG STATISTICS")
            print("="*60)
            print(f"\nTotal Nodes: {stats['total_nodes']}")
            print(f"Total Edges: {stats['total_edges']}")

            print(f"\nNodes by Type:")
            for node_type, count in stats['nodes_by_type'].items():
                print(f"  {node_type:<20} {count:>4}")

            print(f"\nEdges by Relationship:")
            for rel, count in stats['edges_by_relationship'].items():
                print(f"  {rel:<20} {count:>4}")

            print(f"\nMost Connected Components:")
            for comp in stats['most_connected']:
                print(f"  {comp['name']:<30} ({comp['type']:<15}) {comp['connections']:>3} connections")

        elif args.endpoints:
            results = kg.list_endpoints(method=args.method)
            print(f"\nFound {len(results)} API endpoints")
            print_results(results, result_type="endpoints")

        elif args.personas:
            results = kg.list_personas()
            print(f"\nFound {len(results)} fan personas")
            print_results(results, result_type="personas")

        elif args.rivalries:
            results = kg.find_rivalries()
            print(f"\nFound {len(results)} rivalries")
            print_results(results, result_type="rivalries")

        elif args.depends_on:
            result = kg.find_dependencies(args.depends_on, direction='both')
            if 'error' in result:
                print(f"❌ {result['error']}")
            else:
                print(f"\n{'='*60}")
                print(f"DEPENDENCIES FOR: {result['component']} ({result['type']})")
                print(f"{'='*60}")

                if 'depends_on' in result:
                    print(f"\n✓ Depends on ({len(result['depends_on'])} components):")
                    for dep in result['depends_on']:
                        print(f"  • {dep['name']} ({dep['type']}) - {dep['relationship']}")

                if 'dependents' in result:
                    print(f"\n✓ Dependents ({len(result['dependents'])} components):")
                    for dep in result['dependents']:
                        print(f"  • {dep['name']} ({dep['type']}) - {dep['relationship']}")

        elif args.trace:
            result = kg.trace_path(args.trace[0], args.trace[1])
            if 'error' in result:
                print(f"❌ {result['error']}")
            elif result['path'] is None:
                print(f"\n❌ {result['message']}")
            else:
                print(f"\n{'='*60}")
                print(f"PATH: {result['from']} → {result['to']}")
                print(f"Length: {result['path_length']} steps")
                print(f"{'='*60}\n")

                for i, step in enumerate(result['path']):
                    print(f"{i+1}. {step['name']} ({step['type']})")
                    if 'relationship' in step:
                        print(f"   └─ {step['relationship']} ─→")

        elif args.query:
            results = kg.semantic_search(args.query, k=args.k, node_type=args.type)
            print(f"\nFound {len(results)} results for: '{args.query}'")
            print_results(results, result_type="search")

        else:
            parser.print_help()
            return 0

    finally:
        kg.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
