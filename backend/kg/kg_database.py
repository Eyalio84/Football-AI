"""
NLKE-Compliant Knowledge Graph Database Layer

Provides unified access to Soccer-AI and Predictor knowledge graphs
with FTS5 search, BFS traversal, and cross-domain queries.

Critical field: source_kg enables querying across domains.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator
from contextlib import contextmanager
from datetime import datetime


# Database path
KG_DB_PATH = Path(__file__).parent.parent / "soccer_ai_kg.db"


@contextmanager
def get_kg_connection(db_path: Path = KG_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for KG database connections."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


class KnowledgeGraphDB:
    """
    Unified Knowledge Graph database with NLKE compliance.

    Supports cross-domain queries via source_kg field.
    Implements FTS5 hybrid search and BFS traversal.
    """

    # ============================================
    # NODE OPERATIONS
    # ============================================

    @staticmethod
    def get_node(node_id: str) -> Optional[Dict[str, Any]]:
        """Get node by ID."""
        with get_kg_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM nodes WHERE id = ?", (node_id,)
            )
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('metadata'):
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except json.JSONDecodeError:
                        pass
                return result
            return None

    @staticmethod
    def get_nodes_by_type(node_type: str, source_kg: str = None) -> List[Dict[str, Any]]:
        """Get all nodes of a specific type, optionally filtered by domain."""
        with get_kg_connection() as conn:
            if source_kg:
                cursor = conn.execute(
                    "SELECT * FROM nodes WHERE type = ? AND source_kg = ? ORDER BY name",
                    (node_type, source_kg)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM nodes WHERE type = ? ORDER BY name",
                    (node_type,)
                )
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('metadata'):
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except json.JSONDecodeError:
                        pass
                results.append(result)
            return results

    @staticmethod
    def search_nodes(query: str, source_kg: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Full-text search across nodes using FTS5.

        Searches name, description, and metadata fields.
        """
        with get_kg_connection() as conn:
            # Escape special FTS5 characters
            safe_query = query.replace('"', '""')

            try:
                if source_kg:
                    cursor = conn.execute("""
                        SELECT n.*, bm25(nodes_fts) as rank
                        FROM nodes n
                        JOIN nodes_fts fts ON n.rowid = fts.rowid
                        WHERE nodes_fts MATCH ? AND n.source_kg = ?
                        ORDER BY rank
                        LIMIT ?
                    """, (safe_query, source_kg, limit))
                else:
                    cursor = conn.execute("""
                        SELECT n.*, bm25(nodes_fts) as rank
                        FROM nodes n
                        JOIN nodes_fts fts ON n.rowid = fts.rowid
                        WHERE nodes_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                    """, (safe_query, limit))
            except sqlite3.OperationalError:
                # Fallback to LIKE search if FTS fails
                like_query = f"%{query}%"
                if source_kg:
                    cursor = conn.execute("""
                        SELECT * FROM nodes
                        WHERE (name LIKE ? OR description LIKE ?) AND source_kg = ?
                        LIMIT ?
                    """, (like_query, like_query, source_kg, limit))
                else:
                    cursor = conn.execute("""
                        SELECT * FROM nodes
                        WHERE name LIKE ? OR description LIKE ?
                        LIMIT ?
                    """, (like_query, like_query, limit))

            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('metadata'):
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except json.JSONDecodeError:
                        pass
                results.append(result)
            return results

    @staticmethod
    def find_node_by_name(name: str, source_kg: str = None) -> Optional[Dict[str, Any]]:
        """Find node by exact name match."""
        with get_kg_connection() as conn:
            if source_kg:
                cursor = conn.execute(
                    "SELECT * FROM nodes WHERE name = ? AND source_kg = ?",
                    (name, source_kg)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM nodes WHERE name = ?",
                    (name,)
                )
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get('metadata'):
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except json.JSONDecodeError:
                        pass
                return result
            return None

    # ============================================
    # EDGE OPERATIONS
    # ============================================

    @staticmethod
    def get_edges_from(node_id: str, edge_type: str = None) -> List[Dict[str, Any]]:
        """Get all outgoing edges from a node."""
        with get_kg_connection() as conn:
            if edge_type:
                cursor = conn.execute("""
                    SELECT e.*, n.name as to_name, n.type as to_type, n.source_kg as to_source_kg
                    FROM edges e
                    JOIN nodes n ON e.to_node = n.id
                    WHERE e.from_node = ? AND e.type = ?
                    ORDER BY e.weight DESC
                """, (node_id, edge_type))
            else:
                cursor = conn.execute("""
                    SELECT e.*, n.name as to_name, n.type as to_type, n.source_kg as to_source_kg
                    FROM edges e
                    JOIN nodes n ON e.to_node = n.id
                    WHERE e.from_node = ?
                    ORDER BY e.weight DESC
                """, (node_id,))

            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('metadata'):
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except json.JSONDecodeError:
                        pass
                results.append(result)
            return results

    @staticmethod
    def get_edges_to(node_id: str, edge_type: str = None) -> List[Dict[str, Any]]:
        """Get all incoming edges to a node."""
        with get_kg_connection() as conn:
            if edge_type:
                cursor = conn.execute("""
                    SELECT e.*, n.name as from_name, n.type as from_type, n.source_kg as from_source_kg
                    FROM edges e
                    JOIN nodes n ON e.from_node = n.id
                    WHERE e.to_node = ? AND e.type = ?
                    ORDER BY e.weight DESC
                """, (node_id, edge_type))
            else:
                cursor = conn.execute("""
                    SELECT e.*, n.name as from_name, n.type as from_type, n.source_kg as from_source_kg
                    FROM edges e
                    JOIN nodes n ON e.from_node = n.id
                    WHERE e.to_node = ?
                    ORDER BY e.weight DESC
                """, (node_id,))

            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('metadata'):
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except json.JSONDecodeError:
                        pass
                results.append(result)
            return results

    @staticmethod
    def get_all_edges(source_kg: str = None) -> List[Dict[str, Any]]:
        """Get all edges, optionally filtered by domain."""
        with get_kg_connection() as conn:
            if source_kg:
                cursor = conn.execute("""
                    SELECT e.*,
                           n1.name as from_name, n1.type as from_type,
                           n2.name as to_name, n2.type as to_type
                    FROM edges e
                    JOIN nodes n1 ON e.from_node = n1.id
                    JOIN nodes n2 ON e.to_node = n2.id
                    WHERE e.source_kg = ?
                """, (source_kg,))
            else:
                cursor = conn.execute("""
                    SELECT e.*,
                           n1.name as from_name, n1.type as from_type,
                           n2.name as to_name, n2.type as to_type
                    FROM edges e
                    JOIN nodes n1 ON e.from_node = n1.id
                    JOIN nodes n2 ON e.to_node = n2.id
                """)
            return [dict(row) for row in cursor.fetchall()]

    # ============================================
    # TRAVERSAL OPERATIONS
    # ============================================

    @staticmethod
    def traverse(node_id: str, depth: int = 2, edge_type: str = None) -> List[Dict[str, Any]]:
        """
        BFS traversal from a node up to specified depth.

        Returns list of {node, edge, depth} objects.
        """
        visited = {node_id}
        current_level = [node_id]
        results = []

        for d in range(depth):
            next_level = []
            for nid in current_level:
                edges = KnowledgeGraphDB.get_edges_from(nid, edge_type)
                for edge in edges:
                    target_id = edge['to_node']
                    if target_id not in visited:
                        visited.add(target_id)
                        next_level.append(target_id)
                        target_node = KnowledgeGraphDB.get_node(target_id)
                        results.append({
                            'node': target_node,
                            'edge': edge,
                            'depth': d + 1
                        })
            current_level = next_level
            if not current_level:
                break

        return results

    @staticmethod
    def get_neighbors(node_id: str, direction: str = 'both') -> List[Dict[str, Any]]:
        """
        Get neighboring nodes.

        direction: 'out' (outgoing), 'in' (incoming), 'both'
        """
        neighbors = []

        if direction in ('out', 'both'):
            for edge in KnowledgeGraphDB.get_edges_from(node_id):
                node = KnowledgeGraphDB.get_node(edge['to_node'])
                if node:
                    neighbors.append({
                        'node': node,
                        'edge_type': edge['type'],
                        'direction': 'out',
                        'weight': edge.get('weight', 1.0)
                    })

        if direction in ('in', 'both'):
            for edge in KnowledgeGraphDB.get_edges_to(node_id):
                node = KnowledgeGraphDB.get_node(edge['from_node'])
                if node:
                    neighbors.append({
                        'node': node,
                        'edge_type': edge['type'],
                        'direction': 'in',
                        'weight': edge.get('weight', 1.0)
                    })

        return neighbors

    # ============================================
    # CROSS-DOMAIN QUERIES
    # ============================================

    @staticmethod
    def get_cross_domain_nodes(node_type: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get nodes by type, grouped by source domain."""
        with get_kg_connection() as conn:
            cursor = conn.execute("""
                SELECT source_kg, COUNT(*) as count
                FROM nodes
                WHERE type = ?
                GROUP BY source_kg
            """, (node_type,))

            result = {}
            for row in cursor.fetchall():
                domain = row['source_kg']
                nodes = KnowledgeGraphDB.get_nodes_by_type(node_type, domain)
                result[domain] = nodes
            return result

    @staticmethod
    def query_across_domains(
        query: str,
        domains: List[str] = None,
        node_types: List[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Query across multiple domains with optional type filtering.

        Enables unified search across soccer-ai and predictor.
        """
        with get_kg_connection() as conn:
            sql = "SELECT * FROM nodes WHERE 1=1"
            params = []

            if domains:
                placeholders = ','.join('?' * len(domains))
                sql += f" AND source_kg IN ({placeholders})"
                params.extend(domains)

            if node_types:
                placeholders = ','.join('?' * len(node_types))
                sql += f" AND type IN ({placeholders})"
                params.extend(node_types)

            if query:
                sql += " AND (name LIKE ? OR description LIKE ? OR type LIKE ?)"
                like_query = f"%{query}%"
                params.extend([like_query, like_query, like_query])

            sql += " ORDER BY source_kg, type, name LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('metadata'):
                    try:
                        result['metadata'] = json.loads(result['metadata'])
                    except json.JSONDecodeError:
                        pass
                results.append(result)
            return results

    # ============================================
    # STATISTICS
    # ============================================

    @staticmethod
    def get_stats() -> Dict[str, Any]:
        """Get KG statistics by domain and type."""
        with get_kg_connection() as conn:
            stats = {
                'total_nodes': 0,
                'total_edges': 0,
                'by_domain': {},
                'by_type': {},
                'edge_types': {}
            }

            # Total counts
            stats['total_nodes'] = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            stats['total_edges'] = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

            # By domain (nodes)
            cursor = conn.execute("""
                SELECT source_kg, COUNT(*) as count FROM nodes GROUP BY source_kg
            """)
            for row in cursor.fetchall():
                stats['by_domain'][row['source_kg']] = {'nodes': row['count']}

            # By domain (edges)
            cursor = conn.execute("""
                SELECT source_kg, COUNT(*) as count FROM edges GROUP BY source_kg
            """)
            for row in cursor.fetchall():
                if row['source_kg'] in stats['by_domain']:
                    stats['by_domain'][row['source_kg']]['edges'] = row['count']
                else:
                    stats['by_domain'][row['source_kg']] = {'edges': row['count']}

            # By node type
            cursor = conn.execute("""
                SELECT type, COUNT(*) as count FROM nodes GROUP BY type ORDER BY count DESC
            """)
            for row in cursor.fetchall():
                stats['by_type'][row['type']] = row['count']

            # By edge type
            cursor = conn.execute("""
                SELECT type, COUNT(*) as count FROM edges GROUP BY type ORDER BY count DESC
            """)
            for row in cursor.fetchall():
                stats['edge_types'][row['type']] = row['count']

            return stats

    # ============================================
    # LOGGING & LEARNING
    # ============================================

    @staticmethod
    def log_interaction(
        query: str,
        matched_nodes: List[str],
        search_mode: str = 'keyword',
        source_kg: str = None,
        response_time_ms: int = 0
    ) -> None:
        """Log query interaction for learning."""
        with get_kg_connection() as conn:
            cross_dimensional = len(set(
                conn.execute("SELECT source_kg FROM nodes WHERE id = ?", (nid,)).fetchone()[0]
                for nid in matched_nodes[:5] if matched_nodes
            )) > 1 if matched_nodes else False

            conn.execute("""
                INSERT INTO interaction_log
                (query, matched_nodes, result_count, search_mode, source_kg, cross_dimensional, response_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                query,
                json.dumps(matched_nodes[:10]),
                len(matched_nodes),
                search_mode,
                source_kg,
                1 if cross_dimensional else 0,
                response_time_ms
            ))
            conn.commit()


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def get_all_domains() -> List[str]:
    """Get list of all source_kg domains."""
    with get_kg_connection() as conn:
        cursor = conn.execute("SELECT DISTINCT source_kg FROM nodes ORDER BY source_kg")
        return [row[0] for row in cursor.fetchall()]


def get_all_node_types() -> List[str]:
    """Get list of all node types."""
    with get_kg_connection() as conn:
        cursor = conn.execute("SELECT DISTINCT type FROM nodes ORDER BY type")
        return [row[0] for row in cursor.fetchall()]


def get_all_edge_types() -> List[str]:
    """Get list of all edge types."""
    with get_kg_connection() as conn:
        cursor = conn.execute("SELECT DISTINCT type FROM edges ORDER BY type")
        return [row[0] for row in cursor.fetchall()]
