"""
Migration Script: Convert JSON Knowledge Graphs to NLKE-Compliant SQLite

Migrates:
- soccer_ai_kg.json → nodes + edges (source_kg = "soccer-ai")
- predictor_kg.json → nodes + edges (source_kg = "predictor")

Run: python -m kg.kg_migration

Idempotent: Uses INSERT OR REPLACE for safe re-runs.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

from .kg_types import create_node_id, NodeType, EdgeType


# Paths
BACKEND_PATH = Path(__file__).parent.parent
SOCCER_AI_KG_JSON = BACKEND_PATH.parent / "soccer_ai_kg.json"
PREDICTOR_KG_JSON = BACKEND_PATH / "predictor" / "predictor_kg.json"
KG_DB_PATH = BACKEND_PATH / "soccer_ai_kg.db"
SCHEMA_PATH = BACKEND_PATH / "migrations" / "001_create_nlke_kg.sql"


def init_database(db_path: Path = KG_DB_PATH) -> sqlite3.Connection:
    """Initialize database with NLKE schema."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Load and execute schema
    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)
    conn.commit()

    return conn


def migrate_soccer_ai_kg(conn: sqlite3.Connection) -> Tuple[int, int]:
    """
    Migrate soccer_ai_kg.json to NLKE nodes and edges.

    Creates:
    - 8 module nodes
    - 25 endpoint nodes (if present)
    - 19 persona nodes
    - 5 security_state nodes
    - depends_on edges
    - routes_to edges
    - transitions_to / escalates_from edges
    """
    if not SOCCER_AI_KG_JSON.exists():
        print(f"Warning: {SOCCER_AI_KG_JSON} not found")
        return 0, 0

    with open(SOCCER_AI_KG_JSON, 'r') as f:
        kg_data = json.load(f)

    source_kg = "soccer-ai"
    nodes_created = 0
    edges_created = 0

    # 1. Migrate MODULES → nodes
    for module_id, module_data in kg_data.get("modules", {}).items():
        node_id = create_node_id(source_kg, "module", module_id)
        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            module_id,
            module_id,
            "module",
            module_data.get("what", ""),
            json.dumps({
                "file": module_data.get("file"),
                "how": module_data.get("how"),
                "when": module_data.get("when"),
                "capabilities": module_data.get("capabilities", []),
                "endpoints_count": module_data.get("endpoints"),
                "tables": module_data.get("tables", [])
            }),
            source_kg
        ))
        nodes_created += 1

        # Create depends_on edges
        for dep in module_data.get("depends_on", []):
            dep_node_id = create_node_id(source_kg, "module", dep)
            conn.execute("""
                INSERT OR IGNORE INTO edges (from_node, to_node, type, source_kg)
                VALUES (?, ?, ?, ?)
            """, (node_id, dep_node_id, "depends_on", source_kg))
            edges_created += 1

    # 2. Migrate ENDPOINTS → nodes
    for endpoint_id, endpoint_data in kg_data.get("endpoints", {}).items():
        node_id = create_node_id(source_kg, "endpoint", endpoint_id)
        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            endpoint_id,
            f"{endpoint_data.get('method', 'GET')} {endpoint_data.get('path', endpoint_id)}",
            "endpoint",
            endpoint_data.get("what", ""),
            json.dumps({
                "method": endpoint_data.get("method"),
                "path": endpoint_data.get("path"),
                "params": endpoint_data.get("params", [])
            }),
            source_kg
        ))
        nodes_created += 1

        # Create routes_to edges (endpoint → modules)
        for module in endpoint_data.get("modules", []):
            module_node_id = create_node_id(source_kg, "module", module)
            conn.execute("""
                INSERT OR IGNORE INTO edges (from_node, to_node, type, source_kg)
                VALUES (?, ?, ?, ?)
            """, (node_id, module_node_id, "routes_to", source_kg))
            edges_created += 1

    # 3. Migrate PERSONAS → nodes
    for persona_id, persona_data in kg_data.get("personas", {}).items():
        node_id = create_node_id(source_kg, "persona", persona_id)
        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            persona_id,
            persona_id.replace("_", " ").title(),
            "persona",
            f"Fan persona: {persona_id}",
            json.dumps({
                "snap_back": persona_data.get("snap_back"),
                "mood_influence": persona_data.get("mood_influence")
            }),
            source_kg
        ))
        nodes_created += 1

    # 4. Migrate SECURITY STATES → nodes with transitions
    security_data = kg_data.get("security", {})
    for state_id, state_data in security_data.get("states", {}).items():
        node_id = create_node_id(source_kg, "security_state", state_id)
        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            state_id,
            state_id.title(),
            "security_state",
            f"Security state: {state_id}",
            json.dumps(state_data),
            source_kg
        ))
        nodes_created += 1

    # Create security transition edges
    for transition_type, transitions in security_data.get("transitions", {}).items():
        for transition in transitions:
            # Parse "normal→warned" or "probation→normal(5)" format
            sep = "→" if "→" in transition else "->"
            if sep in transition:
                parts = transition.replace("->", "→").split("→")
                if len(parts) == 2:
                    from_state = parts[0].strip().split("(")[0]
                    to_state = parts[1].strip().split("(")[0]
                    from_node_id = create_node_id(source_kg, "security_state", from_state)
                    to_node_id = create_node_id(source_kg, "security_state", to_state)
                    edge_type = "escalates_from" if transition_type == "injection" else "transitions_to"

                    conn.execute("""
                        INSERT OR IGNORE INTO edges (from_node, to_node, type, metadata, source_kg)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        from_node_id,
                        to_node_id,
                        edge_type,
                        json.dumps({"trigger": transition_type}),
                        source_kg
                    ))
                    edges_created += 1

    conn.commit()
    return nodes_created, edges_created


def migrate_predictor_kg(conn: sqlite3.Connection) -> Tuple[int, int]:
    """
    Migrate predictor_kg.json to NLKE nodes and edges.

    Creates:
    - 7 module nodes
    - 12 factor_a nodes (Side A weakness factors)
    - 10 factor_b nodes (Side B strength factors)
    - 5 pattern nodes (Third Knowledge)
    - 4 equation nodes
    - depends_on edges
    - triggers / combines_with edges
    """
    if not PREDICTOR_KG_JSON.exists():
        print(f"Warning: {PREDICTOR_KG_JSON} not found")
        return 0, 0

    with open(PREDICTOR_KG_JSON, 'r') as f:
        kg_data = json.load(f)

    source_kg = "predictor"
    nodes_created = 0
    edges_created = 0

    # 1. Migrate MODULES → nodes
    for module_id, module_data in kg_data.get("modules", {}).items():
        node_id = create_node_id(source_kg, "module", module_id)
        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            module_id,
            module_id,
            "module",
            module_data.get("what", ""),
            json.dumps({
                "file": module_data.get("file"),
                "how": module_data.get("how"),
                "when": module_data.get("when"),
                "capabilities": module_data.get("capabilities", []),
                "factors": module_data.get("factors"),
                "tables": module_data.get("tables", []),
                "external_apis": module_data.get("external_apis", [])
            }),
            source_kg
        ))
        nodes_created += 1

        # Create depends_on edges
        for dep in module_data.get("depends_on", []):
            dep_node_id = create_node_id(source_kg, "module", dep)
            conn.execute("""
                INSERT OR IGNORE INTO edges (from_node, to_node, type, source_kg)
                VALUES (?, ?, ?, ?)
            """, (node_id, dep_node_id, "depends_on", source_kg))
            edges_created += 1

    # 2. Migrate SIDE A FACTORS → nodes
    for factor_id, factor_data in kg_data.get("factors", {}).get("side_a", {}).items():
        code = factor_data.get("code", factor_id)
        node_id = create_node_id(source_kg, "factor_a", code.lower())
        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            factor_id,
            factor_id.replace("_", " ").title(),
            "factor_a",
            factor_data.get("description", ""),
            json.dumps({
                "code": code,
                "inputs": factor_data.get("inputs", []),
                "weight": factor_data.get("weight")
            }),
            source_kg
        ))
        nodes_created += 1

    # 3. Migrate SIDE B FACTORS → nodes
    for factor_id, factor_data in kg_data.get("factors", {}).get("side_b", {}).items():
        code = factor_data.get("code", factor_id)
        node_id = create_node_id(source_kg, "factor_b", code.lower())
        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            factor_id,
            factor_id.replace("_", " ").title(),
            "factor_b",
            factor_data.get("description", ""),
            json.dumps({
                "code": code,
                "inputs": factor_data.get("inputs", []),
                "weight": factor_data.get("weight")
            }),
            source_kg
        ))
        nodes_created += 1

    # 4. Migrate THIRD KNOWLEDGE PATTERNS → nodes + edges
    for pattern_id, pattern_data in kg_data.get("third_knowledge_patterns", {}).items():
        node_id = create_node_id(source_kg, "pattern", pattern_id)
        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            pattern_id,
            pattern_id.replace("_", " ").title(),
            "pattern",
            pattern_data.get("description", ""),
            json.dumps({
                "factor_a_code": pattern_data.get("factor_a_code"),
                "factor_b_code": pattern_data.get("factor_b_code"),
                "interaction_type": pattern_data.get("interaction_type"),
                "multiplier_range": pattern_data.get("multiplier_range"),
                "confidence": pattern_data.get("confidence"),
                "trigger": pattern_data.get("trigger")
            }),
            source_kg
        ))
        nodes_created += 1

        # Create combines_with edges (pattern → factors)
        factor_a_code = pattern_data.get("factor_a_code")
        factor_b_code = pattern_data.get("factor_b_code")

        if factor_a_code:
            factor_a_node_id = create_node_id(source_kg, "factor_a", factor_a_code.lower())
            conn.execute("""
                INSERT OR IGNORE INTO edges (from_node, to_node, type, weight, source_kg)
                VALUES (?, ?, ?, ?, ?)
            """, (
                node_id,
                factor_a_node_id,
                "combines_with",
                pattern_data.get("confidence", 0.5),
                source_kg
            ))
            edges_created += 1

        if factor_b_code:
            factor_b_node_id = create_node_id(source_kg, "factor_b", factor_b_code.lower())
            conn.execute("""
                INSERT OR IGNORE INTO edges (from_node, to_node, type, weight, source_kg)
                VALUES (?, ?, ?, ?, ?)
            """, (
                node_id,
                factor_b_node_id,
                "combines_with",
                pattern_data.get("confidence", 0.5),
                source_kg
            ))
            edges_created += 1

    # 5. Migrate EQUATIONS → nodes
    for equation_id, equation_data in kg_data.get("equations", {}).items():
        node_id = create_node_id(source_kg, "equation", equation_id)
        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            equation_id,
            equation_id.replace("_", " ").title(),
            "equation",
            equation_data.get("description", ""),
            json.dumps({
                "formula": equation_data.get("formula"),
                "range": equation_data.get("range"),
                "clamped": equation_data.get("clamped")
            }),
            source_kg
        ))
        nodes_created += 1

    # 6. Migrate CONFIDENCE LEVELS → nodes
    for level_id, level_data in kg_data.get("confidence_levels", {}).items():
        node_id = create_node_id(source_kg, "confidence_level", level_id)
        conn.execute("""
            INSERT OR REPLACE INTO nodes (id, original_id, name, type, description, metadata, source_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            level_id,
            level_id.title(),
            "confidence_level",
            level_data.get("meaning", ""),
            json.dumps({
                "range": level_data.get("range")
            }),
            source_kg
        ))
        nodes_created += 1

    conn.commit()
    return nodes_created, edges_created


def create_cross_domain_edges(conn: sqlite3.Connection) -> int:
    """Create edges connecting soccer-ai and predictor domains."""
    edges_created = 0

    # Integration edge: predictor → soccer-ai (analyst persona)
    conn.execute("""
        INSERT OR IGNORE INTO edges (from_node, to_node, type, metadata, source_kg)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "predictor_module_api",
        "soccer-ai_persona_analyst",
        "routes_to",
        json.dumps({"integration_type": "persona_bridge"}),
        "cross-domain"
    ))
    edges_created += 1

    # Integration: predictor_api depends on prediction_engine
    conn.execute("""
        INSERT OR IGNORE INTO edges (from_node, to_node, type, source_kg)
        VALUES (?, ?, ?, ?)
    """, (
        "soccer-ai_module_predictor_api",
        "predictor_module_prediction_engine",
        "calls",
        "cross-domain"
    ))
    edges_created += 1

    conn.commit()
    return edges_created


def run_migration(db_path: Path = KG_DB_PATH) -> Dict[str, Any]:
    """
    Execute full migration.

    Returns summary with node/edge counts by domain.
    """
    print(f"Initializing database at {db_path}")
    conn = init_database(db_path)

    print(f"\nMigrating Soccer-AI KG from {SOCCER_AI_KG_JSON}")
    soccer_nodes, soccer_edges = migrate_soccer_ai_kg(conn)
    print(f"  → {soccer_nodes} nodes, {soccer_edges} edges")

    print(f"\nMigrating Predictor KG from {PREDICTOR_KG_JSON}")
    predictor_nodes, predictor_edges = migrate_predictor_kg(conn)
    print(f"  → {predictor_nodes} nodes, {predictor_edges} edges")

    print("\nCreating cross-domain edges...")
    cross_edges = create_cross_domain_edges(conn)
    print(f"  → {cross_edges} edges")

    # Get final totals
    total_nodes = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    total_edges = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

    # Get breakdown by domain
    domain_stats = {}
    for row in conn.execute("SELECT source_kg, COUNT(*) as count FROM nodes GROUP BY source_kg"):
        domain_stats[row[0]] = {"nodes": row[1]}
    for row in conn.execute("SELECT source_kg, COUNT(*) as count FROM edges GROUP BY source_kg"):
        if row[0] in domain_stats:
            domain_stats[row[0]]["edges"] = row[1]
        else:
            domain_stats[row[0]] = {"edges": row[1]}

    # Get breakdown by type
    type_stats = {}
    for row in conn.execute("SELECT type, COUNT(*) as count FROM nodes GROUP BY type"):
        type_stats[row[0]] = row[1]

    conn.close()

    summary = {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "by_domain": domain_stats,
        "by_type": type_stats,
        "database_path": str(db_path)
    }

    print(f"\n{'='*50}")
    print(f"MIGRATION COMPLETE")
    print(f"{'='*50}")
    print(f"Total: {total_nodes} nodes, {total_edges} edges")
    print(f"\nBy Domain:")
    for domain, stats in domain_stats.items():
        print(f"  {domain}: {stats.get('nodes', 0)} nodes, {stats.get('edges', 0)} edges")
    print(f"\nBy Type:")
    for node_type, count in sorted(type_stats.items()):
        print(f"  {node_type}: {count}")
    print(f"\nDatabase: {db_path}")

    return summary


if __name__ == "__main__":
    run_migration()
