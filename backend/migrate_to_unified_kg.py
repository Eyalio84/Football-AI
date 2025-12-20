"""
Unified Knowledge Graph Migration Script

Merges all three Soccer-AI KG databases into a single unified KG:
- soccer_ai_architecture_kg.db (608 nodes) - Architecture, persons, stadiums
- soccer_ai_kg.db (75 nodes) - Predictor patterns, modules
- soccer_ai.db kg_nodes/kg_edges (62 nodes) - Teams, legends, rivalries

The unified KG provides:
- X (Emotional): Match results, form data
- Y (Relational): Rivalries, legend associations
- Z (Linguistic): Regional context
- T (Temporal): Historical moments, seasons
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any


# Database paths
BACKEND_DIR = Path(__file__).parent
PROJECT_DIR = BACKEND_DIR.parent

# Source databases
ARCHITECTURE_KG_PATH = PROJECT_DIR / "soccer_ai_architecture_kg.db"
PREDICTOR_KG_PATH = BACKEND_DIR / "soccer_ai_kg.db"
MAIN_DB_PATH = BACKEND_DIR / "soccer_ai.db"

# Target database
UNIFIED_KG_PATH = BACKEND_DIR / "unified_soccer_ai_kg.db"


def create_unified_schema(conn: sqlite3.Connection):
    """Create the unified KG schema."""
    cursor = conn.cursor()

    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS nodes_fts")
    cursor.execute("DROP TABLE IF EXISTS edges")
    cursor.execute("DROP TABLE IF EXISTS nodes")
    cursor.execute("DROP TABLE IF EXISTS migration_log")

    # Nodes table
    cursor.execute("""
        CREATE TABLE nodes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            node_type TEXT NOT NULL,
            description TEXT,
            properties TEXT,
            source_db TEXT NOT NULL,
            original_id TEXT
        )
    """)

    # Edges table
    cursor.execute("""
        CREATE TABLE edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            relationship TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            properties TEXT,
            source_db TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES nodes(id),
            FOREIGN KEY (target_id) REFERENCES nodes(id)
        )
    """)

    # FTS5 for search
    cursor.execute("""
        CREATE VIRTUAL TABLE nodes_fts USING fts5(
            id, name, description,
            content='nodes',
            content_rowid='rowid'
        )
    """)

    # Triggers to keep FTS in sync
    cursor.execute("""
        CREATE TRIGGER nodes_ai AFTER INSERT ON nodes BEGIN
            INSERT INTO nodes_fts(rowid, id, name, description)
            VALUES (new.rowid, new.id, new.name, new.description);
        END
    """)

    cursor.execute("""
        CREATE TRIGGER nodes_ad AFTER DELETE ON nodes BEGIN
            INSERT INTO nodes_fts(nodes_fts, rowid, id, name, description)
            VALUES('delete', old.rowid, old.id, old.name, old.description);
        END
    """)

    cursor.execute("""
        CREATE TRIGGER nodes_au AFTER UPDATE ON nodes BEGIN
            INSERT INTO nodes_fts(nodes_fts, rowid, id, name, description)
            VALUES('delete', old.rowid, old.id, old.name, old.description);
            INSERT INTO nodes_fts(rowid, id, name, description)
            VALUES (new.rowid, new.id, new.name, new.description);
        END
    """)

    # Migration log
    cursor.execute("""
        CREATE TABLE migration_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_db TEXT,
            operation TEXT,
            count INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Indices for performance
    cursor.execute("CREATE INDEX idx_nodes_type ON nodes(node_type)")
    cursor.execute("CREATE INDEX idx_nodes_source ON nodes(source_db)")
    cursor.execute("CREATE INDEX idx_edges_source_id ON edges(source_id)")
    cursor.execute("CREATE INDEX idx_edges_target_id ON edges(target_id)")
    cursor.execute("CREATE INDEX idx_edges_relationship ON edges(relationship)")

    conn.commit()
    print("[UNIFIED KG] Schema created successfully")


def migrate_architecture_kg(target_conn: sqlite3.Connection) -> Tuple[int, int]:
    """
    Migrate from soccer_ai_architecture_kg.db

    Schema: kg_nodes(node_id INTEGER, name, type, description, properties)
            kg_edges(from_node INTEGER, to_node INTEGER, relationship, weight, properties)
    """
    if not ARCHITECTURE_KG_PATH.exists():
        print(f"[SKIP] Architecture KG not found: {ARCHITECTURE_KG_PATH}")
        return 0, 0

    source_conn = sqlite3.connect(ARCHITECTURE_KG_PATH)
    source_conn.row_factory = sqlite3.Row

    cursor = target_conn.cursor()

    # Build ID mapping: old INTEGER -> new TEXT ID
    id_map: Dict[int, str] = {}

    # Migrate nodes
    nodes = source_conn.execute("""
        SELECT node_id, name, type, description, properties
        FROM kg_nodes
    """).fetchall()

    node_count = 0
    for row in nodes:
        # Create prefixed ID to avoid conflicts
        new_id = f"arch_{row['node_id']}"
        id_map[row['node_id']] = new_id

        try:
            cursor.execute("""
                INSERT INTO nodes (id, name, node_type, description, properties, source_db, original_id)
                VALUES (?, ?, ?, ?, ?, 'architecture', ?)
            """, (
                new_id,
                row['name'],
                row['type'] or 'unknown',
                row['description'],
                row['properties'],
                str(row['node_id'])
            ))
            node_count += 1
        except sqlite3.IntegrityError as e:
            print(f"  [WARN] Duplicate node: {new_id} - {e}")

    # Migrate edges
    edges = source_conn.execute("""
        SELECT from_node, to_node, relationship, weight, properties
        FROM kg_edges
    """).fetchall()

    edge_count = 0
    for row in edges:
        source_id = id_map.get(row['from_node'])
        target_id = id_map.get(row['to_node'])

        if source_id and target_id:
            try:
                cursor.execute("""
                    INSERT INTO edges (source_id, target_id, relationship, weight, properties, source_db)
                    VALUES (?, ?, ?, ?, ?, 'architecture')
                """, (
                    source_id,
                    target_id,
                    row['relationship'] or 'related_to',
                    row['weight'] or 1.0,
                    row['properties']
                ))
                edge_count += 1
            except Exception as e:
                print(f"  [WARN] Edge failed: {source_id} -> {target_id}: {e}")

    # Log migration
    cursor.execute("""
        INSERT INTO migration_log (source_db, operation, count)
        VALUES ('architecture', 'nodes', ?)
    """, (node_count,))
    cursor.execute("""
        INSERT INTO migration_log (source_db, operation, count)
        VALUES ('architecture', 'edges', ?)
    """, (edge_count,))

    target_conn.commit()
    source_conn.close()

    print(f"[ARCHITECTURE KG] Migrated {node_count} nodes, {edge_count} edges")
    return node_count, edge_count


def migrate_predictor_kg(target_conn: sqlite3.Connection) -> Tuple[int, int]:
    """
    Migrate from soccer_ai_kg.db (predictor/module patterns)

    Schema: nodes(id TEXT, original_id, name, type, description, metadata, source_kg)
            edges(from_node TEXT, to_node TEXT, type, weight, metadata, source_kg)
    """
    if not PREDICTOR_KG_PATH.exists():
        print(f"[SKIP] Predictor KG not found: {PREDICTOR_KG_PATH}")
        return 0, 0

    source_conn = sqlite3.connect(PREDICTOR_KG_PATH)
    source_conn.row_factory = sqlite3.Row

    cursor = target_conn.cursor()

    # Build ID mapping: old TEXT -> new TEXT ID (prefix to avoid conflicts)
    id_map: Dict[str, str] = {}

    # Migrate nodes
    nodes = source_conn.execute("""
        SELECT id, original_id, name, type, description, metadata, source_kg
        FROM nodes
    """).fetchall()

    node_count = 0
    for row in nodes:
        # Create prefixed ID
        new_id = f"pred_{row['id']}"
        id_map[row['id']] = new_id

        # Combine metadata with source_kg info
        props = row['metadata'] or '{}'
        if row['source_kg']:
            try:
                props_dict = json.loads(props) if props else {}
                props_dict['source_kg'] = row['source_kg']
                props = json.dumps(props_dict)
            except:
                pass

        try:
            cursor.execute("""
                INSERT INTO nodes (id, name, node_type, description, properties, source_db, original_id)
                VALUES (?, ?, ?, ?, ?, 'predictor', ?)
            """, (
                new_id,
                row['name'],
                row['type'] or 'unknown',
                row['description'],
                props,
                row['id']
            ))
            node_count += 1
        except sqlite3.IntegrityError as e:
            print(f"  [WARN] Duplicate node: {new_id} - {e}")

    # Migrate edges
    edges = source_conn.execute("""
        SELECT from_node, to_node, type, weight, metadata, source_kg
        FROM edges
    """).fetchall()

    edge_count = 0
    for row in edges:
        source_id = id_map.get(row['from_node'])
        target_id = id_map.get(row['to_node'])

        if source_id and target_id:
            # Combine metadata with source_kg
            props = row['metadata'] or '{}'
            if row['source_kg']:
                try:
                    props_dict = json.loads(props) if props else {}
                    props_dict['source_kg'] = row['source_kg']
                    props = json.dumps(props_dict)
                except:
                    pass

            try:
                cursor.execute("""
                    INSERT INTO edges (source_id, target_id, relationship, weight, properties, source_db)
                    VALUES (?, ?, ?, ?, ?, 'predictor')
                """, (
                    source_id,
                    target_id,
                    row['type'] or 'related_to',
                    row['weight'] or 1.0,
                    props
                ))
                edge_count += 1
            except Exception as e:
                print(f"  [WARN] Edge failed: {source_id} -> {target_id}: {e}")

    # Log migration
    cursor.execute("""
        INSERT INTO migration_log (source_db, operation, count)
        VALUES ('predictor', 'nodes', ?)
    """, (node_count,))
    cursor.execute("""
        INSERT INTO migration_log (source_db, operation, count)
        VALUES ('predictor', 'edges', ?)
    """, (edge_count,))

    target_conn.commit()
    source_conn.close()

    print(f"[PREDICTOR KG] Migrated {node_count} nodes, {edge_count} edges")
    return node_count, edge_count


def migrate_main_db_kg(target_conn: sqlite3.Connection) -> Tuple[int, int]:
    """
    Migrate from soccer_ai.db kg_nodes/kg_edges (CRITICAL: Has rivalries!)

    Schema: kg_nodes(node_id INTEGER, node_type, entity_id, name, properties)
            kg_edges(source_id INTEGER, target_id INTEGER, relationship, weight, properties)

    This contains the RIVALRY data essential for 4D Y-axis!
    """
    if not MAIN_DB_PATH.exists():
        print(f"[SKIP] Main DB not found: {MAIN_DB_PATH}")
        return 0, 0

    source_conn = sqlite3.connect(MAIN_DB_PATH)
    source_conn.row_factory = sqlite3.Row

    cursor = target_conn.cursor()

    # Build ID mapping: old INTEGER -> new TEXT ID
    id_map: Dict[int, str] = {}

    # Migrate nodes
    nodes = source_conn.execute("""
        SELECT node_id, node_type, entity_id, name, properties
        FROM kg_nodes
    """).fetchall()

    node_count = 0
    for row in nodes:
        # Use meaningful prefix based on type
        node_type = row['node_type'] or 'unknown'
        name_slug = (row['name'] or '').lower().replace(' ', '_').replace("'", "")[:20]
        new_id = f"main_{node_type}_{row['node_id']}"

        # For teams, also create a friendly alias
        if node_type == 'team':
            new_id = f"team_{name_slug}"

        id_map[row['node_id']] = new_id

        # Add entity_id to properties
        props = row['properties'] or '{}'
        if row['entity_id']:
            try:
                props_dict = json.loads(props) if props else {}
                props_dict['entity_id'] = row['entity_id']
                props = json.dumps(props_dict)
            except:
                pass

        try:
            cursor.execute("""
                INSERT INTO nodes (id, name, node_type, description, properties, source_db, original_id)
                VALUES (?, ?, ?, ?, ?, 'main', ?)
            """, (
                new_id,
                row['name'],
                node_type,
                None,  # Main DB doesn't have descriptions
                props,
                str(row['node_id'])
            ))
            node_count += 1
        except sqlite3.IntegrityError as e:
            print(f"  [WARN] Duplicate node: {new_id} - {e}")

    # Migrate edges (CRITICAL: includes rival_of!)
    edges = source_conn.execute("""
        SELECT source_id, target_id, relationship, weight, properties
        FROM kg_edges
    """).fetchall()

    edge_count = 0
    rivalry_count = 0
    for row in edges:
        source_id = id_map.get(row['source_id'])
        target_id = id_map.get(row['target_id'])
        relationship = row['relationship'] or 'related_to'

        if relationship == 'rival_of':
            rivalry_count += 1

        if source_id and target_id:
            try:
                cursor.execute("""
                    INSERT INTO edges (source_id, target_id, relationship, weight, properties, source_db)
                    VALUES (?, ?, ?, ?, ?, 'main')
                """, (
                    source_id,
                    target_id,
                    relationship,
                    row['weight'] or 1.0,
                    row['properties']
                ))
                edge_count += 1
            except Exception as e:
                print(f"  [WARN] Edge failed: {source_id} -> {target_id}: {e}")

    # Log migration
    cursor.execute("""
        INSERT INTO migration_log (source_db, operation, count)
        VALUES ('main', 'nodes', ?)
    """, (node_count,))
    cursor.execute("""
        INSERT INTO migration_log (source_db, operation, count)
        VALUES ('main', 'edges', ?)
    """, (edge_count,))
    cursor.execute("""
        INSERT INTO migration_log (source_db, operation, count)
        VALUES ('main', 'rivalries', ?)
    """, (rivalry_count,))

    target_conn.commit()
    source_conn.close()

    print(f"[MAIN DB KG] Migrated {node_count} nodes, {edge_count} edges ({rivalry_count} rivalries)")
    return node_count, edge_count


def verify_unified_kg(conn: sqlite3.Connection):
    """Verify the unified KG integrity and print statistics."""
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("UNIFIED KG VERIFICATION")
    print("=" * 60)

    # Total counts
    total_nodes = cursor.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    total_edges = cursor.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

    print(f"\nTotal: {total_nodes} nodes, {total_edges} edges")

    # By source
    print("\nBy Source Database:")
    sources = cursor.execute("""
        SELECT source_db, COUNT(*) as cnt
        FROM nodes
        GROUP BY source_db
        ORDER BY cnt DESC
    """).fetchall()
    for src, cnt in sources:
        print(f"  {src}: {cnt} nodes")

    # Node types
    print("\nNode Types:")
    types = cursor.execute("""
        SELECT node_type, COUNT(*) as cnt
        FROM nodes
        GROUP BY node_type
        ORDER BY cnt DESC
        LIMIT 15
    """).fetchall()
    for t, cnt in types:
        print(f"  {t}: {cnt}")

    # Edge relationships
    print("\nEdge Relationships:")
    rels = cursor.execute("""
        SELECT relationship, COUNT(*) as cnt
        FROM edges
        GROUP BY relationship
        ORDER BY cnt DESC
    """).fetchall()
    for rel, cnt in rels:
        print(f"  {rel}: {cnt}")

    # Critical: Rivalries
    rivalries = cursor.execute("""
        SELECT n1.name, n2.name, e.weight
        FROM edges e
        JOIN nodes n1 ON e.source_id = n1.id
        JOIN nodes n2 ON e.target_id = n2.id
        WHERE e.relationship = 'rival_of'
        ORDER BY e.weight DESC
    """).fetchall()

    print(f"\nRivalries ({len(rivalries)} total):")
    for src, tgt, weight in rivalries[:10]:
        print(f"  {src} <-> {tgt} (weight: {weight})")
    if len(rivalries) > 10:
        print(f"  ... and {len(rivalries) - 10} more")

    # FTS test
    print("\nFTS Test (searching 'Liverpool'):")
    fts_results = cursor.execute("""
        SELECT id, name, node_type
        FROM nodes
        WHERE id IN (SELECT id FROM nodes_fts WHERE nodes_fts MATCH 'Liverpool')
        LIMIT 5
    """).fetchall()
    for r in fts_results:
        print(f"  {r[0]}: {r[1]} ({r[2]})")

    print("\n" + "=" * 60)


def run_migration():
    """Execute the full migration."""
    print("=" * 60)
    print("UNIFIED KNOWLEDGE GRAPH MIGRATION")
    print("=" * 60)
    print(f"\nTarget: {UNIFIED_KG_PATH}")
    print(f"\nSources:")
    print(f"  1. Architecture KG: {ARCHITECTURE_KG_PATH}")
    print(f"  2. Predictor KG: {PREDICTOR_KG_PATH}")
    print(f"  3. Main DB KG: {MAIN_DB_PATH}")
    print()

    # Remove existing unified DB if it exists
    if UNIFIED_KG_PATH.exists():
        os.remove(UNIFIED_KG_PATH)
        print("[CLEAN] Removed existing unified KG")

    # Create new unified DB
    conn = sqlite3.connect(UNIFIED_KG_PATH)
    conn.row_factory = sqlite3.Row

    # Create schema
    create_unified_schema(conn)

    # Migrate from each source
    totals = {'nodes': 0, 'edges': 0}

    # 1. Architecture KG (biggest)
    n, e = migrate_architecture_kg(conn)
    totals['nodes'] += n
    totals['edges'] += e

    # 2. Predictor KG
    n, e = migrate_predictor_kg(conn)
    totals['nodes'] += n
    totals['edges'] += e

    # 3. Main DB KG (has rivalries!)
    n, e = migrate_main_db_kg(conn)
    totals['nodes'] += n
    totals['edges'] += e

    print(f"\n[TOTAL] {totals['nodes']} nodes, {totals['edges']} edges migrated")

    # Verify
    verify_unified_kg(conn)

    conn.close()

    print(f"\n✓ Unified KG created: {UNIFIED_KG_PATH}")
    print(f"  Size: {UNIFIED_KG_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    run_migration()
