"""
NBA Knowledge Graph Migration

Proves domain-agnostic architecture by reusing Soccer-AI's NLKE schema.
Migrates nba_kg.json → SQLite with source_kg="nba".

This demonstrates the pattern:
1. Define domain-specific JSON (nba_kg.json)
2. Run migration with source_kg identifier
3. Query across domains using source_kg field

The ONLY differences from Soccer-AI migration:
- source_kg = "nba" instead of "soccer-ai"/"predictor"
- NBA-specific node types (player, game, etc.)
- NBA-specific edge types (plays_for, competed_in, etc.)
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List
from contextlib import contextmanager
from datetime import datetime


# Paths
NBA_KG_JSON = Path(__file__).parent.parent.parent / "nba_kg.json"
NBA_DB_PATH = Path(__file__).parent.parent / "nba_ai_kg.db"


# Reuse the same schema from Soccer-AI (proving domain-agnostic)
NLKE_SCHEMA = """
-- ===========================================
-- NBA-AI NLKE-Compliant Knowledge Graph Schema
-- Identical to Soccer-AI (proving domain-agnostic)
-- ===========================================

-- Core Tables
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    original_id TEXT,
    name TEXT NOT NULL,
    type TEXT,
    description TEXT,
    metadata TEXT,
    source_kg TEXT NOT NULL DEFAULT 'nba',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_node TEXT NOT NULL,
    to_node TEXT NOT NULL,
    type TEXT,
    weight REAL DEFAULT 1.0,
    metadata TEXT,
    source_kg TEXT NOT NULL DEFAULT 'nba',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_node) REFERENCES nodes(id),
    FOREIGN KEY (to_node) REFERENCES nodes(id),
    UNIQUE(from_node, to_node, type)
);

CREATE TABLE IF NOT EXISTS embeddings (
    node_id TEXT PRIMARY KEY,
    dimensions TEXT NOT NULL,
    num_dimensions INTEGER,
    method TEXT,
    generated_date TEXT,
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);

-- Learning Tables (same structure)
CREATE TABLE IF NOT EXISTS interaction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT,
    matched_nodes TEXT,
    result_count INTEGER,
    search_mode TEXT,
    source_kg TEXT,
    cross_dimensional INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FTS5 for hybrid search
CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    name, description, metadata, content='nodes', content_rowid='rowid'
);

-- FTS5 triggers
CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
    INSERT INTO nodes_fts(rowid, name, description, metadata)
    VALUES (NEW.rowid, NEW.name, NEW.description, NEW.metadata);
END;

CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, description, metadata)
    VALUES ('delete', OLD.rowid, OLD.name, OLD.description, OLD.metadata);
END;

CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, description, metadata)
    VALUES ('delete', OLD.rowid, OLD.name, OLD.description, OLD.metadata);
    INSERT INTO nodes_fts(rowid, name, description, metadata)
    VALUES (NEW.rowid, NEW.name, NEW.description, NEW.metadata);
END;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_source_kg ON nodes(source_kg);
CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_node);
CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_node);
CREATE INDEX IF NOT EXISTS idx_edges_source_kg ON edges(source_kg);
"""


@contextmanager
def get_connection(db_path: Path = NBA_DB_PATH):
    """Context manager for database connections."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    """Initialize the NLKE schema."""
    conn.executescript(NLKE_SCHEMA)
    conn.commit()


def migrate_nba_kg(conn: sqlite3.Connection, kg_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Migrate NBA KG JSON to SQLite.

    Two-pass migration:
    1. Create ALL nodes first
    2. Create ALL edges second (foreign keys now valid)

    Returns counts of migrated entities.
    """
    counts = {
        'modules': 0,
        'endpoints': 0,
        'personas': 0,
        'legends': 0,
        'rivalries': 0,
        'predictor_factors_a': 0,
        'predictor_factors_b': 0,
        'predictor_patterns': 0,
        'edges': 0
    }

    # Collect edges for second pass
    pending_edges = []

    source_kg = "nba"

    # ===========================================
    # PASS 1: CREATE ALL NODES
    # ===========================================

    # 1. Migrate Modules
    modules = kg_data.get('modules', {})
    for module_id, module_data in modules.items():
        node_id = f"{source_kg}_module_{module_id}"

        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            module_id,
            module_data.get('file', module_id),
            'module',
            module_data.get('what', ''),
            json.dumps(module_data),
            source_kg
        ))
        counts['modules'] += 1

        # Queue depends_on edges
        for dep in module_data.get('depends_on', []):
            dep_node_id = f"{source_kg}_module_{dep}"
            pending_edges.append((node_id, dep_node_id, 'depends_on', 1.0, source_kg))

    # 2. Migrate Endpoints
    endpoints = kg_data.get('endpoints', {})
    for endpoint_id, endpoint_data in endpoints.items():
        node_id = f"{source_kg}_endpoint_{endpoint_id}"

        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            endpoint_id,
            endpoint_data.get('path', endpoint_id),
            'endpoint',
            endpoint_data.get('what', ''),
            json.dumps(endpoint_data),
            source_kg
        ))
        counts['endpoints'] += 1

        # Queue routes_to edges
        for module in endpoint_data.get('modules', []):
            module_node_id = f"{source_kg}_module_{module}"
            pending_edges.append((node_id, module_node_id, 'routes_to', 1.0, source_kg))

    # 3. Migrate Personas (Teams)
    personas = kg_data.get('personas', {})
    for persona_id, persona_data in personas.items():
        node_id = f"{source_kg}_persona_{persona_id}"

        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            persona_id,
            persona_data.get('team', persona_id),
            'persona',
            persona_data.get('snap_back', ''),
            json.dumps(persona_data),
            source_kg
        ))
        counts['personas'] += 1

    # 4. Migrate Legends (Players)
    legends = kg_data.get('legends', {})
    for legend_id, legend_data in legends.items():
        node_id = f"{source_kg}_legend_{legend_id}"

        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            legend_id,
            legend_data.get('name', legend_id),
            'legend',
            legend_data.get('achievements', ''),
            json.dumps(legend_data),
            source_kg
        ))
        counts['legends'] += 1

        # Queue plays_for edge to team
        team_id = legend_data.get('team', '')
        if team_id:
            team_node_id = f"{source_kg}_persona_{team_id}"
            pending_edges.append((node_id, team_node_id, 'plays_for', 1.0, source_kg))

    # 5. Migrate Rivalries
    rivalries = kg_data.get('rivalries', {})
    for rivalry_id, rivalry_data in rivalries.items():
        node_id = f"{source_kg}_rivalry_{rivalry_id}"

        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            rivalry_id,
            ' vs '.join(rivalry_data.get('teams', [])),
            'rivalry',
            rivalry_data.get('description', ''),
            json.dumps(rivalry_data),
            source_kg
        ))
        counts['rivalries'] += 1

        # Queue rivalry edges between teams
        teams = rivalry_data.get('teams', [])
        if len(teams) >= 2:
            team1_node = f"{source_kg}_persona_{teams[0].lower()}"
            team2_node = f"{source_kg}_persona_{teams[1].lower()}"
            pending_edges.append((team1_node, team2_node, 'rivals_with', rivalry_data.get('intensity', 5) / 10.0, source_kg))

    # 6. Migrate Predictor (Side A Factors)
    predictor = kg_data.get('predictor', {})
    factors_a = predictor.get('factors_a', {})
    for factor_id, factor_data in factors_a.items():
        node_id = f"{source_kg}_factor_a_{factor_id.lower()}"

        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            factor_id,
            factor_data.get('name', factor_id),
            'factor_a',
            factor_data.get('description', ''),
            json.dumps(factor_data),
            source_kg
        ))
        counts['predictor_factors_a'] += 1

    # 7. Migrate Predictor (Side B Factors)
    factors_b = predictor.get('factors_b', {})
    for factor_id, factor_data in factors_b.items():
        node_id = f"{source_kg}_factor_b_{factor_id.lower()}"

        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            factor_id,
            factor_data.get('name', factor_id),
            'factor_b',
            factor_data.get('description', ''),
            json.dumps(factor_data),
            source_kg
        ))
        counts['predictor_factors_b'] += 1

    # 8. Migrate Predictor Patterns
    patterns = predictor.get('patterns', {})
    for pattern_id, pattern_data in patterns.items():
        node_id = f"{source_kg}_pattern_{pattern_id}"

        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            pattern_id,
            pattern_id.replace('_', ' ').title(),
            'pattern',
            pattern_data.get('description', ''),
            json.dumps(pattern_data),
            source_kg
        ))
        counts['predictor_patterns'] += 1

        # Queue combines_with edges to factors
        for trigger in pattern_data.get('trigger', []):
            factor_node_id = f"{source_kg}_factor_a_{trigger.lower()}"
            pending_edges.append((node_id, factor_node_id, 'combines_with', 1.0, source_kg))

    # Commit nodes
    conn.commit()

    # ===========================================
    # PASS 2: CREATE ALL EDGES
    # ===========================================
    for from_node, to_node, edge_type, weight, src_kg in pending_edges:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO edges (from_node, to_node, type, weight, source_kg)
                VALUES (?, ?, ?, ?, ?)
            """, (from_node, to_node, edge_type, weight, src_kg))
            counts['edges'] += 1
        except sqlite3.IntegrityError:
            # Skip edges with missing nodes (might be optional dependencies)
            pass

    conn.commit()
    return counts


def run_nba_migration(db_path: Path = NBA_DB_PATH) -> Dict[str, Any]:
    """
    Run complete NBA KG migration.

    Returns migration results with counts.
    """
    # Load JSON
    with open(NBA_KG_JSON, 'r') as f:
        kg_data = json.load(f)

    # Initialize database
    with get_connection(db_path) as conn:
        # Create schema
        init_schema(conn)

        # Run migration
        counts = migrate_nba_kg(conn, kg_data)

        # Get total counts
        total_nodes = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        total_edges = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

    return {
        'success': True,
        'db_path': str(db_path),
        'source_json': str(NBA_KG_JSON),
        'counts': counts,
        'totals': {
            'nodes': total_nodes,
            'edges': total_edges
        },
        'migrated_at': datetime.now().isoformat()
    }


def get_nba_stats(db_path: Path = NBA_DB_PATH) -> Dict[str, Any]:
    """Get NBA KG statistics."""
    with get_connection(db_path) as conn:
        stats = {
            'total_nodes': conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0],
            'total_edges': conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0],
            'by_type': {},
            'edge_types': {}
        }

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


def search_nba(query: str, limit: int = 10, db_path: Path = NBA_DB_PATH) -> List[Dict[str, Any]]:
    """Search NBA KG using FTS5."""
    with get_connection(db_path) as conn:
        safe_query = query.replace('"', '""')

        try:
            cursor = conn.execute("""
                SELECT n.*, bm25(nodes_fts) as rank
                FROM nodes n
                JOIN nodes_fts fts ON n.rowid = fts.rowid
                WHERE nodes_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (safe_query, limit))
        except sqlite3.OperationalError:
            # Fallback to LIKE
            like_query = f"%{query}%"
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


# ===========================================
# CLI Entry Point
# ===========================================
if __name__ == "__main__":
    print("=" * 60)
    print("NBA-AI Knowledge Graph Migration")
    print("Proving Domain-Agnostic Architecture")
    print("=" * 60)

    # Run migration
    result = run_nba_migration()

    print(f"\nMigration: {'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"Database: {result['db_path']}")
    print(f"\nCounts:")
    for key, value in result['counts'].items():
        if value > 0:
            print(f"  {key}: {value}")

    print(f"\nTotals:")
    print(f"  Nodes: {result['totals']['nodes']}")
    print(f"  Edges: {result['totals']['edges']}")

    # Test search
    print(f"\n{'=' * 60}")
    print("Testing FTS5 Search...")
    print("=" * 60)

    test_queries = ["Lakers", "Curry", "fatigue", "rivalry"]
    for q in test_queries:
        results = search_nba(q, limit=3)
        print(f"\nSearch '{q}': {len(results)} results")
        for r in results:
            print(f"  - {r['name']} ({r['type']})")

    print(f"\n{'=' * 60}")
    print("NBA Stats:")
    print("=" * 60)
    stats = get_nba_stats()
    print(f"Total nodes: {stats['total_nodes']}")
    print(f"Total edges: {stats['total_edges']}")
    print("\nBy type:")
    for t, c in stats['by_type'].items():
        print(f"  {t}: {c}")
