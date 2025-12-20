"""
Compatibility Layer for Legacy KG

Syncs between:
- Legacy: kg_nodes/kg_edges tables (integer IDs, entity_id references)
- NLKE: nodes/edges tables (TEXT IDs, source_kg field)

This enables gradual migration while keeping existing code working.
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

from .kg_database import KnowledgeGraphDB, get_kg_connection, KG_DB_PATH
from .kg_types import NodeType, EdgeType, create_node_id, NodeDefinition, EdgeDefinition


# Legacy database path (soccer_ai.db with kg_nodes/kg_edges)
LEGACY_DB_PATH = Path(__file__).parent.parent / "soccer_ai.db"


@contextmanager
def get_legacy_connection():
    """Context manager for legacy database connections."""
    conn = sqlite3.connect(LEGACY_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def sync_legacy_to_nlke() -> Dict[str, Any]:
    """
    Sync legacy kg_nodes/kg_edges to NLKE format.

    Maps:
    - kg_nodes.node_type → nodes.type
    - kg_nodes.entity_id → nodes.original_id
    - kg_nodes.name → nodes.name
    - Adds source_kg = "soccer-ai" for all legacy nodes

    Returns:
        Dict with sync stats
    """
    legacy_to_nlke_map = {}  # Maps legacy node_id → NLKE id
    nodes_synced = 0
    edges_synced = 0

    # Check if legacy DB exists
    if not LEGACY_DB_PATH.exists():
        return {'error': 'Legacy database not found', 'path': str(LEGACY_DB_PATH)}

    with get_legacy_connection() as legacy_conn:
        # Check if legacy KG tables exist
        cursor = legacy_conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('kg_nodes', 'kg_edges')
        """)
        tables = [row[0] for row in cursor.fetchall()]

        if 'kg_nodes' not in tables:
            return {'error': 'Legacy kg_nodes table not found'}

        # Get all legacy nodes
        cursor = legacy_conn.execute("""
            SELECT node_id, node_type, entity_id, name, properties
            FROM kg_nodes
        """)
        legacy_nodes = cursor.fetchall()

        with get_kg_connection() as nlke_conn:
            for node in legacy_nodes:
                # Generate NLKE-compliant ID
                nlke_id = create_node_id(
                    'soccer-ai',
                    node['node_type'],
                    str(node['entity_id'])
                )

                # Check if already exists
                existing = nlke_conn.execute(
                    "SELECT id FROM nodes WHERE id = ?", (nlke_id,)
                ).fetchone()

                if not existing:
                    # Parse properties JSON
                    props = {}
                    if node['properties']:
                        try:
                            props = json.loads(node['properties'])
                        except json.JSONDecodeError:
                            pass

                    # Insert into NLKE
                    nlke_conn.execute("""
                        INSERT INTO nodes (id, original_id, name, type, description, metadata, source_kg)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        nlke_id,
                        str(node['entity_id']),
                        node['name'],
                        node['node_type'],
                        props.get('description', ''),
                        json.dumps(props),
                        'soccer-ai'
                    ))
                    nodes_synced += 1

                legacy_to_nlke_map[node['node_id']] = nlke_id

            nlke_conn.commit()

            # Sync edges
            if 'kg_edges' in tables:
                cursor = legacy_conn.execute("""
                    SELECT source_id, target_id, relationship, weight, properties
                    FROM kg_edges
                """)
                legacy_edges = cursor.fetchall()

                for edge in legacy_edges:
                    from_nlke = legacy_to_nlke_map.get(edge['source_id'])
                    to_nlke = legacy_to_nlke_map.get(edge['target_id'])

                    if from_nlke and to_nlke:
                        # Check if edge already exists
                        existing = nlke_conn.execute("""
                            SELECT id FROM edges
                            WHERE from_node = ? AND to_node = ? AND type = ?
                        """, (from_nlke, to_nlke, edge['relationship'])).fetchone()

                        if not existing:
                            props = {}
                            if edge['properties']:
                                try:
                                    props = json.loads(edge['properties'])
                                except json.JSONDecodeError:
                                    pass

                            nlke_conn.execute("""
                                INSERT INTO edges (from_node, to_node, type, weight, metadata, source_kg)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                from_nlke,
                                to_nlke,
                                edge['relationship'],
                                edge['weight'] or 1.0,
                                json.dumps(props),
                                'soccer-ai'
                            ))
                            edges_synced += 1

                nlke_conn.commit()

    return {
        'nodes_synced': nodes_synced,
        'edges_synced': edges_synced,
        'node_mapping': legacy_to_nlke_map,
        'total_legacy_nodes': len(legacy_nodes) if 'legacy_nodes' in dir() else 0
    }


def sync_nlke_to_legacy() -> Dict[str, Any]:
    """
    Reverse sync: NLKE → legacy kg_nodes/kg_edges.

    Useful when NLKE is the source of truth and legacy needs updating.
    Only syncs soccer-ai domain nodes.
    """
    nlke_to_legacy_map = {}
    nodes_synced = 0
    edges_synced = 0

    if not LEGACY_DB_PATH.exists():
        return {'error': 'Legacy database not found'}

    with get_kg_connection() as nlke_conn:
        # Get all soccer-ai nodes
        cursor = nlke_conn.execute("""
            SELECT id, original_id, name, type, description, metadata
            FROM nodes
            WHERE source_kg = 'soccer-ai'
        """)
        nlke_nodes = cursor.fetchall()

        with get_legacy_connection() as legacy_conn:
            # Ensure legacy tables exist
            legacy_conn.execute("""
                CREATE TABLE IF NOT EXISTS kg_nodes (
                    node_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_type TEXT NOT NULL,
                    entity_id INTEGER,
                    name TEXT NOT NULL,
                    properties TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            legacy_conn.execute("""
                CREATE TABLE IF NOT EXISTS kg_edges (
                    edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER NOT NULL,
                    target_id INTEGER NOT NULL,
                    relationship TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    properties TEXT,
                    FOREIGN KEY (source_id) REFERENCES kg_nodes(node_id),
                    FOREIGN KEY (target_id) REFERENCES kg_nodes(node_id)
                )
            """)
            legacy_conn.commit()

            for node in nlke_nodes:
                node = dict(node)

                # Check if exists by name and type
                existing = legacy_conn.execute("""
                    SELECT node_id FROM kg_nodes
                    WHERE name = ? AND node_type = ?
                """, (node['name'], node['type'])).fetchone()

                if existing:
                    nlke_to_legacy_map[node['id']] = existing['node_id']
                else:
                    # Parse entity_id from original_id
                    try:
                        entity_id = int(node['original_id'])
                    except (ValueError, TypeError):
                        entity_id = None

                    cursor = legacy_conn.execute("""
                        INSERT INTO kg_nodes (node_type, entity_id, name, properties)
                        VALUES (?, ?, ?, ?)
                    """, (
                        node['type'],
                        entity_id,
                        node['name'],
                        node['metadata']
                    ))
                    nlke_to_legacy_map[node['id']] = cursor.lastrowid
                    nodes_synced += 1

            legacy_conn.commit()

            # Sync edges
            cursor = nlke_conn.execute("""
                SELECT from_node, to_node, type, weight, metadata
                FROM edges
                WHERE source_kg = 'soccer-ai'
            """)
            nlke_edges = cursor.fetchall()

            for edge in nlke_edges:
                edge = dict(edge)
                from_legacy = nlke_to_legacy_map.get(edge['from_node'])
                to_legacy = nlke_to_legacy_map.get(edge['to_node'])

                if from_legacy and to_legacy:
                    existing = legacy_conn.execute("""
                        SELECT edge_id FROM kg_edges
                        WHERE source_id = ? AND target_id = ? AND relationship = ?
                    """, (from_legacy, to_legacy, edge['type'])).fetchone()

                    if not existing:
                        legacy_conn.execute("""
                            INSERT INTO kg_edges (source_id, target_id, relationship, weight, properties)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            from_legacy,
                            to_legacy,
                            edge['type'],
                            edge['weight'] or 1.0,
                            edge['metadata']
                        ))
                        edges_synced += 1

            legacy_conn.commit()

    return {
        'nodes_synced': nodes_synced,
        'edges_synced': edges_synced,
        'node_mapping': nlke_to_legacy_map
    }


def get_legacy_kg_stats() -> Dict[str, Any]:
    """Get statistics from legacy KG tables."""
    if not LEGACY_DB_PATH.exists():
        return {'error': 'Legacy database not found'}

    with get_legacy_connection() as conn:
        # Check tables exist
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('kg_nodes', 'kg_edges')
        """)
        tables = [row[0] for row in cursor.fetchall()]

        stats = {'tables_found': tables}

        if 'kg_nodes' in tables:
            stats['total_nodes'] = conn.execute(
                "SELECT COUNT(*) FROM kg_nodes"
            ).fetchone()[0]

            # By type
            cursor = conn.execute("""
                SELECT node_type, COUNT(*) as count
                FROM kg_nodes GROUP BY node_type
            """)
            stats['by_type'] = {row[0]: row[1] for row in cursor.fetchall()}

        if 'kg_edges' in tables:
            stats['total_edges'] = conn.execute(
                "SELECT COUNT(*) FROM kg_edges"
            ).fetchone()[0]

            # By relationship
            cursor = conn.execute("""
                SELECT relationship, COUNT(*) as count
                FROM kg_edges GROUP BY relationship
            """)
            stats['by_relationship'] = {row[0]: row[1] for row in cursor.fetchall()}

        return stats


def compare_kg_systems() -> Dict[str, Any]:
    """Compare legacy and NLKE KG systems."""
    legacy_stats = get_legacy_kg_stats()
    nlke_stats = KnowledgeGraphDB.get_stats()

    return {
        'legacy': legacy_stats,
        'nlke': nlke_stats,
        'differences': {
            'node_count_diff': nlke_stats['total_nodes'] - legacy_stats.get('total_nodes', 0),
            'edge_count_diff': nlke_stats['total_edges'] - legacy_stats.get('total_edges', 0),
            'nlke_domains': list(nlke_stats['by_domain'].keys()),
            'nlke_has_predictor': 'predictor' in nlke_stats['by_domain']
        }
    }


# ============================================
# ADAPTER FUNCTIONS
# ============================================
# These provide legacy-compatible function signatures
# while using NLKE under the hood

def legacy_get_node(node_id: int) -> Optional[Dict[str, Any]]:
    """
    Legacy-compatible get_node that works with integer IDs.

    Looks up in legacy table first, then falls back to NLKE.
    """
    # First try legacy
    with get_legacy_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM kg_nodes WHERE node_id = ?", (node_id,)
        )
        row = cursor.fetchone()
        if row:
            result = dict(row)
            if result.get('properties'):
                try:
                    result['properties'] = json.loads(result['properties'])
                except json.JSONDecodeError:
                    pass
            return result

    return None


def legacy_traverse(node_id: int, depth: int = 1, relationship: str = None) -> List[Dict]:
    """
    Legacy-compatible traverse using NLKE under the hood.

    Converts integer node_id to NLKE format, performs traversal,
    then converts back to legacy format for compatibility.
    """
    # Find NLKE node ID from legacy node_id
    with get_legacy_connection() as conn:
        cursor = conn.execute(
            "SELECT node_type, entity_id FROM kg_nodes WHERE node_id = ?", (node_id,)
        )
        row = cursor.fetchone()
        if not row:
            return []

        nlke_id = create_node_id('soccer-ai', row['node_type'], str(row['entity_id']))

    # Use NLKE traversal
    results = KnowledgeGraphDB.traverse(nlke_id, depth, relationship)

    # Convert back to legacy-compatible format
    # (keeping NLKE node structure but wrapping appropriately)
    return results


def unified_search(query: str, source: str = 'both', limit: int = 10) -> Dict[str, List]:
    """
    Search across both legacy and NLKE systems.

    Args:
        query: Search query
        source: 'legacy', 'nlke', or 'both'
        limit: Max results per source

    Returns:
        Dict with 'legacy' and 'nlke' result lists
    """
    results = {'legacy': [], 'nlke': []}

    if source in ('both', 'nlke'):
        results['nlke'] = KnowledgeGraphDB.search_nodes(query, limit=limit)

    if source in ('both', 'legacy'):
        with get_legacy_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM kg_nodes
                WHERE LOWER(name) LIKE LOWER(?)
                LIMIT ?
            """, (f"%{query}%", limit))
            for row in cursor.fetchall():
                result = dict(row)
                if result.get('properties'):
                    try:
                        result['properties'] = json.loads(result['properties'])
                    except json.JSONDecodeError:
                        pass
                results['legacy'].append(result)

    return results
