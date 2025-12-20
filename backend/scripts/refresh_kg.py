"""
Knowledge Graph Refresh Script
Updates unified_soccer_ai_kg.db with current season data.

Usage:
    cd backend && python scripts/refresh_kg.py
    cd backend && python scripts/refresh_kg.py --dry-run
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

BACKEND_DIR = Path(__file__).parent.parent
DB_PATH = BACKEND_DIR / "unified_soccer_ai_kg.db"
MAIN_DB = BACKEND_DIR / "soccer_ai.db"


def get_current_pl_teams():
    """Get current PL teams from main database standings."""
    if not MAIN_DB.exists():
        print("WARNING: soccer_ai.db not found, using hardcoded list")
        return []
    conn = sqlite3.connect(str(MAIN_DB))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, name, short_name FROM teams ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def ensure_team_nodes(kg_conn, teams, dry_run=False):
    """Ensure all current PL teams exist as nodes in the KG."""
    added = 0
    for team in teams:
        name = team["name"]
        node_id = f"team_{name.lower().replace(' ', '_')}"
        existing = kg_conn.execute(
            "SELECT id FROM nodes WHERE id = ? OR name = ?",
            (node_id, name)
        ).fetchone()
        if not existing:
            if dry_run:
                print(f"  [DRY RUN] Would add team node: {name}")
            else:
                kg_conn.execute(
                    "INSERT INTO nodes (id, name, node_type, description, properties) VALUES (?, ?, ?, ?, ?)",
                    (node_id, name, "team", f"Premier League club: {name}",
                     json.dumps({"source": "refresh_script", "added": datetime.now().isoformat()}))
                )
            added += 1
    return added


def ensure_rivalry_edges(kg_conn, dry_run=False):
    """Ensure key rivalries exist as edges."""
    rivalries = [
        ("ipswich_town", "norwich_city", "East Anglian Derby", 1.0),
        ("southampton", "portsmouth", "South Coast Derby", 1.0),
        ("southampton", "bournemouth", "South Coast Rivalry", 0.6),
    ]
    added = 0
    for src, tgt, name, weight in rivalries:
        src_id = f"team_{src}"
        tgt_id = f"team_{tgt}"
        existing = kg_conn.execute(
            "SELECT id FROM edges WHERE source_id = ? AND target_id = ? AND relationship = 'rival_of'",
            (src_id, tgt_id)
        ).fetchone()
        if not existing:
            if dry_run:
                print(f"  [DRY RUN] Would add rivalry: {name} ({src} <-> {tgt})")
            else:
                kg_conn.execute(
                    "INSERT INTO edges (source_id, target_id, relationship, weight, properties) VALUES (?, ?, ?, ?, ?)",
                    (src_id, tgt_id, "rival_of", weight,
                     json.dumps({"name": name, "source": "refresh_script"}))
                )
                kg_conn.execute(
                    "INSERT INTO edges (source_id, target_id, relationship, weight, properties) VALUES (?, ?, ?, ?, ?)",
                    (tgt_id, src_id, "rival_of", weight,
                     json.dumps({"name": name, "source": "refresh_script"}))
                )
            added += 1
    return added


def get_kg_stats(kg_conn):
    """Get current KG statistics."""
    nodes = kg_conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    edges = kg_conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    types = kg_conn.execute(
        "SELECT node_type, COUNT(*) as cnt FROM nodes GROUP BY node_type ORDER BY cnt DESC"
    ).fetchall()
    return nodes, edges, types


def main():
    dry_run = "--dry-run" in sys.argv

    if not DB_PATH.exists():
        print(f"ERROR: KG database not found at {DB_PATH}")
        sys.exit(1)

    print(f"{'[DRY RUN] ' if dry_run else ''}Knowledge Graph Refresh")
    print(f"Database: {DB_PATH}")
    print(f"Size: {DB_PATH.stat().st_size / 1024 / 1024:.1f} MB")
    print()

    kg_conn = sqlite3.connect(str(DB_PATH))
    kg_conn.row_factory = sqlite3.Row

    # Current stats
    nodes, edges, types = get_kg_stats(kg_conn)
    print(f"Current KG: {nodes} nodes, {edges} edges")
    for t in types:
        print(f"  {t[0]}: {t[1]}")
    print()

    # Ensure team nodes
    teams = get_current_pl_teams()
    if teams:
        added = ensure_team_nodes(kg_conn, teams, dry_run)
        print(f"Team nodes: {added} added")

    # Ensure rivalry edges
    added = ensure_rivalry_edges(kg_conn, dry_run)
    print(f"Rivalry edges: {added} added")

    if not dry_run:
        kg_conn.commit()
        nodes_after, edges_after, _ = get_kg_stats(kg_conn)
        print(f"\nUpdated KG: {nodes_after} nodes, {edges_after} edges")
    else:
        print("\n[DRY RUN] No changes written")

    kg_conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
