"""
Bridge to NLKE MCP Tools

This module enables Soccer-AI KG to be queried via NLKE MCP server tools.
Implements interfaces compatible with:
- mcp__nlke-ml__hybrid_search
- mcp__nlke-ml__semantic_similarity
- mcp__nlke-unified__unified_query
"""

from typing import List, Dict, Optional, Any
import json
import time
from pathlib import Path

from .kg_database import KnowledgeGraphDB, get_kg_connection


class NLKEBridge:
    """
    Bridge between Soccer-AI Knowledge Graph and NLKE MCP tools.

    Enables Soccer-AI and Predictor domains to be queryable
    alongside other NLKE knowledge graphs.
    """

    @staticmethod
    def hybrid_search(
        query: str,
        scope: str = "all",
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Hybrid search compatible with mcp__nlke-ml__hybrid_search.

        Combines:
        - FTS5 keyword matching (primary)
        - Node connectivity boosting
        - Cross-domain results

        Args:
            query: Search query
            scope: "all", "soccer-ai", or "predictor"
            k: Number of results

        Returns:
            Dict with query, results, and metadata
        """
        start_time = time.time()
        results = []

        # Determine source_kg filter
        source_kg = None if scope == "all" else scope

        with get_kg_connection() as conn:
            # 1. FTS5 search
            fts_results = KnowledgeGraphDB.search_nodes(query, source_kg, limit=k*2)

            # 2. Score and rank
            for node in fts_results:
                score = 0.5  # Base FTS score

                # Boost by edge connectivity (hub nodes are more important)
                edge_count = conn.execute("""
                    SELECT COUNT(*) FROM edges
                    WHERE from_node = ? OR to_node = ?
                """, (node['id'], node['id'])).fetchone()[0]
                score += min(edge_count * 0.05, 0.3)

                # Boost by description length (more detail = more relevant)
                if node.get('description'):
                    score += min(len(node['description']) / 500, 0.1)

                results.append({
                    'node_id': node['id'],
                    'name': node['name'],
                    'type': node['type'],
                    'source_kg': node['source_kg'],
                    'description': node.get('description', ''),
                    'score': round(score, 3)
                })

            # Sort by score and limit
            results.sort(key=lambda x: x['score'], reverse=True)
            results = results[:k]

        elapsed_ms = int((time.time() - start_time) * 1000)

        # Log interaction for learning
        matched_ids = [r['node_id'] for r in results]
        KnowledgeGraphDB.log_interaction(
            query=query,
            matched_nodes=matched_ids,
            search_mode='hybrid',
            source_kg=source_kg,
            response_time_ms=elapsed_ms
        )

        return {
            'query': query,
            'scope': scope,
            'results': results,
            'total_found': len(results),
            'elapsed_ms': elapsed_ms
        }

    @staticmethod
    def semantic_similarity(concept_a: str, concept_b: str) -> float:
        """
        Calculate semantic similarity between two concepts.

        Uses term overlap as baseline (embeddings would require ML model).
        Returns value 0.0 to 1.0.
        """
        # Tokenize and lowercase
        terms_a = set(concept_a.lower().split())
        terms_b = set(concept_b.lower().split())

        # Remove common stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'to', 'of', 'and', 'or', 'in', 'on', 'at', 'for', 'with'}
        terms_a = terms_a - stopwords
        terms_b = terms_b - stopwords

        if not terms_a or not terms_b:
            return 0.0

        # Jaccard similarity
        intersection = len(terms_a & terms_b)
        union = len(terms_a | terms_b)

        return round(intersection / union, 3) if union > 0 else 0.0

    @staticmethod
    def unified_query(
        query: str,
        mode: str = "auto",
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Query compatible with mcp__nlke-unified__unified_query.

        Args:
            query: Natural language query
            mode: "auto", "soccer-ai", "predictor", or "cross"
            k: Number of results

        Returns:
            Results with cross-domain links
        """
        # Auto-detect domain from query keywords
        if mode == "auto":
            query_lower = query.lower()
            if any(w in query_lower for w in ['prediction', 'upset', 'factor', 'pattern', 'side a', 'side b']):
                mode = "predictor"
            elif any(w in query_lower for w in ['fan', 'persona', 'security', 'chat', 'endpoint']):
                mode = "soccer-ai"
            else:
                mode = "cross"

        # Execute search
        scope = "all" if mode == "cross" else mode
        search_results = NLKEBridge.hybrid_search(query, scope=scope, k=k)

        # Add cross-domain links for cross queries
        if mode == "cross":
            # Find nodes that connect across domains
            cross_links = []
            with get_kg_connection() as conn:
                cursor = conn.execute("""
                    SELECT e.*, n1.source_kg as from_domain, n2.source_kg as to_domain
                    FROM edges e
                    JOIN nodes n1 ON e.from_node = n1.id
                    JOIN nodes n2 ON e.to_node = n2.id
                    WHERE n1.source_kg != n2.source_kg
                    LIMIT 10
                """)
                for row in cursor.fetchall():
                    cross_links.append({
                        'from': row['from_node'],
                        'to': row['to_node'],
                        'type': row['type'],
                        'from_domain': row['from_domain'],
                        'to_domain': row['to_domain']
                    })

            search_results['cross_domain_links'] = cross_links

        search_results['mode'] = mode
        return search_results

    @staticmethod
    def get_node_context(node_id: str, depth: int = 1) -> Dict[str, Any]:
        """
        Get full context for a node including neighbors and edges.

        Useful for building context windows for LLM prompts.
        """
        node = KnowledgeGraphDB.get_node(node_id)
        if not node:
            return {'error': f'Node {node_id} not found'}

        # Get neighbors
        neighbors = KnowledgeGraphDB.get_neighbors(node_id, direction='both')

        # Get traversal for deeper context
        traversal = []
        if depth > 1:
            traversal = KnowledgeGraphDB.traverse(node_id, depth=depth)

        return {
            'node': node,
            'neighbors': neighbors,
            'traversal': traversal,
            'neighbor_count': len(neighbors),
            'traversal_depth': depth
        }

    @staticmethod
    def register_with_mcp() -> Dict[str, Any]:
        """
        Register Soccer-AI KG as a data source for NLKE MCP server.

        Returns configuration that can be used to add Soccer-AI
        and Predictor as queryable domains in NLKE MCP.
        """
        stats = KnowledgeGraphDB.get_stats()

        return {
            'domains': ['soccer-ai', 'predictor'],
            'total_nodes': stats['total_nodes'],
            'total_edges': stats['total_edges'],
            'capabilities': [
                'hybrid_search',
                'traverse',
                'cross_domain_query',
                'semantic_similarity'
            ],
            'node_types': list(stats['by_type'].keys()),
            'edge_types': list(stats['edge_types'].keys()),
            'by_domain': stats['by_domain'],
            'integration_endpoint': '/api/v1/kg/query'
        }

    @staticmethod
    def export_for_nlke(output_path: Path = None) -> Dict[str, Any]:
        """
        Export KG in format compatible with NLKE unified-kg.db.

        Can be used to merge Soccer-AI/Predictor into a larger NLKE graph.
        """
        with get_kg_connection() as conn:
            # Export nodes
            nodes = []
            cursor = conn.execute("SELECT * FROM nodes")
            for row in cursor.fetchall():
                nodes.append(dict(row))

            # Export edges
            edges = []
            cursor = conn.execute("SELECT * FROM edges")
            for row in cursor.fetchall():
                edges.append(dict(row))

            export_data = {
                'metadata': {
                    'exported_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source': 'soccer-ai',
                    'version': '1.0'
                },
                'nodes': nodes,
                'edges': edges,
                'stats': KnowledgeGraphDB.get_stats()
            }

            if output_path:
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)

            return export_data


# ============================================
# CONVENIENCE FUNCTIONS FOR MCP INTEGRATION
# ============================================

def want_to(goal: str) -> Dict[str, Any]:
    """
    Goal-based tool discovery compatible with mcp__nlke-intent__want_to.

    Example: want_to("predict upset probability")
    """
    return NLKEBridge.unified_query(goal, mode="auto", k=5)


def can_it(capability: str) -> Dict[str, Any]:
    """
    Check if Soccer-AI KG can do something.

    Example: can_it("search across domains")
    """
    supported = {
        'search': True,
        'traverse': True,
        'cross_domain': True,
        'predict': True,  # Via predictor domain
        'chat': True,     # Via soccer-ai domain
        'embeddings': False,  # Not yet implemented
    }

    for key, value in supported.items():
        if key in capability.lower():
            return {
                'capability': capability,
                'supported': value,
                'domain': 'predictor' if 'predict' in capability.lower() else 'soccer-ai'
            }

    return {
        'capability': capability,
        'supported': False,
        'reason': 'Unknown capability'
    }
