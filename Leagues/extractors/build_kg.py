"""
League Knowledge Graph Builder

Reads Leagues/{League}/league_config.json and clubs/*.json and populates
the unified_soccer_ai_kg.db with:
  - Team nodes (node_type='team')
  - Legend nodes (node_type='legend') + legendary_at edges
  - Moment nodes (node_type='moment') + iconic_match_for edges
  - Stadium nodes (node_type='stadium') + home_ground edges
  - Rivalry edges (relationship='rival_of', weight=intensity)

Idempotent: uses INSERT OR IGNORE / INSERT OR REPLACE so it's safe to re-run.

Usage:
    python build_kg.py --league la_liga
    python build_kg.py --league premier_league
    python build_kg.py --all
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path


# ============================================================================
# PATHS
# ============================================================================

REPO_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
LEAGUES_DIR = REPO_ROOT / "Leagues"
KG_DB = BACKEND_DIR / "unified_soccer_ai_kg.db"

sys.path.insert(0, str(BACKEND_DIR))


# ============================================================================
# HELPERS
# ============================================================================

def slugify(text: str) -> str:
    """Convert text to a safe node ID component."""
    return re.sub(r"[^a-z0-9_]", "_", text.lower().strip()).strip("_")


def get_or_create_node(conn: sqlite3.Connection, node_id: str, node_type: str,
                        name: str, description: str = "", properties: dict = None) -> str:
    """Insert a KG node if it doesn't exist, return node_id."""
    props_json = json.dumps(properties or {})
    conn.execute(
        """INSERT OR IGNORE INTO nodes (id, node_type, name, description, properties, source_db)
           VALUES (?, ?, ?, ?, ?, 'ufle_builder')""",
        (node_id, node_type, name, description, props_json)
    )
    return node_id


def get_or_create_edge(conn: sqlite3.Connection, source_id: str, target_id: str,
                        relationship: str, weight: float = 1.0, properties: dict = None) -> None:
    """Insert a KG edge if it doesn't exist."""
    props_json = json.dumps(properties or {})
    conn.execute(
        """INSERT OR IGNORE INTO edges (source_id, target_id, relationship, weight, properties, source_db)
           VALUES (?, ?, ?, ?, ?, 'ufle_builder')""",
        (source_id, target_id, relationship, weight, props_json)
    )


def ensure_fts_sync(conn: sqlite3.Connection) -> None:
    """Sync FTS5 index if it exists."""
    try:
        conn.execute("INSERT INTO nodes_fts(nodes_fts) VALUES('rebuild')")
    except sqlite3.OperationalError:
        pass  # FTS table may not exist or have different name


# ============================================================================
# MAIN BUILDER
# ============================================================================

def build_league_kg(league_id: str, verbose: bool = False) -> dict:
    """Build KG nodes and edges for a league from its JSON files."""
    league_dir_name = "_".join(w.capitalize() for w in league_id.split("_"))
    league_dir = LEAGUES_DIR / league_dir_name
    config_path = league_dir / "league_config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"No league config at {config_path}")

    config = json.loads(config_path.read_text())
    display_name = config.get("display_name", league_id)
    sport = config.get("sport", "football")

    if not KG_DB.exists():
        raise FileNotFoundError(f"KG database not found at {KG_DB}")

    conn = sqlite3.connect(str(KG_DB))

    stats = {
        "league_id": league_id,
        "team_nodes": 0,
        "legend_nodes": 0,
        "moment_nodes": 0,
        "stadium_nodes": 0,
        "rivalry_edges": 0,
        "legendary_at_edges": 0,
        "iconic_match_edges": 0,
    }

    print(f"[build_kg] Building KG for {display_name}...")

    # Create league node
    league_node_id = f"league_{league_id}"
    get_or_create_node(conn, league_node_id, "league", display_name,
                       f"{display_name} professional football league",
                       {"sport": sport, "country": config.get("country")})

    # Process each club in the config
    for club_entry in config.get("clubs", []):
        club_id = club_entry["id"]
        club_name = club_entry["display_name"]
        team_node_id = f"team_{club_id}"

        # Create team node
        get_or_create_node(conn, team_node_id, "team", club_name,
                           f"{club_name} — {display_name} football club",
                           {
                               "league": league_id,
                               "sport": sport,
                               "api_id": club_entry.get("api_id"),
                               "founded": club_entry.get("founded"),
                               "stadium": club_entry.get("stadium"),
                               "dialect_region": club_entry.get("dialect_region"),
                           })
        stats["team_nodes"] += 1

        # Edge: team member_of league
        get_or_create_edge(conn, team_node_id, league_node_id, "member_of", 1.0)

        # Stadium node
        stadium_name = club_entry.get("stadium")
        if stadium_name:
            stadium_node_id = f"stadium_{slugify(stadium_name)}"
            get_or_create_node(conn, stadium_node_id, "stadium", stadium_name,
                               f"Home stadium of {club_name}",
                               {"club": club_id, "league": league_id})
            get_or_create_edge(conn, team_node_id, stadium_node_id, "home_ground", 1.0)
            stats["stadium_nodes"] += 1

        # Load club knowledge file
        club_file = league_dir / "clubs" / f"{club_id}.json"
        if not club_file.exists():
            if verbose:
                print(f"  [skip] No knowledge file for {club_id}")
            continue

        club_data = json.loads(club_file.read_text())

        # Legends
        for legend in club_data.get("legends", []):
            legend_name = legend.get("name", "")
            if not legend_name:
                continue
            legend_node_id = f"legend_{slugify(legend_name)}_{club_id}"
            get_or_create_node(
                conn, legend_node_id, "legend", legend_name,
                legend.get("story", ""),
                {
                    "era": legend.get("era"),
                    "achievements": legend.get("achievements", []),
                    "fan_nickname": legend.get("fan_nickname"),
                    "club": club_id,
                    "league": league_id,
                    "sport": sport,
                }
            )
            get_or_create_edge(conn, legend_node_id, team_node_id, "legendary_at", 1.0)
            stats["legend_nodes"] += 1
            stats["legendary_at_edges"] += 1

        # Iconic moments
        for moment in club_data.get("iconic_moments", []):
            title = moment.get("title", "")
            if not title:
                continue
            moment_node_id = f"moment_{slugify(title)}_{club_id}"
            get_or_create_node(
                conn, moment_node_id, "moment", title,
                moment.get("significance", ""),
                {
                    "date": moment.get("date"),
                    "opponent": moment.get("opponent"),
                    "score": moment.get("score"),
                    "emotion": moment.get("emotion"),
                    "club": club_id,
                    "league": league_id,
                    "sport": sport,
                }
            )
            get_or_create_edge(conn, moment_node_id, team_node_id, "iconic_match_for", 1.0)
            stats["moment_nodes"] += 1
            stats["iconic_match_edges"] += 1

        # Rivalries
        for rival_id, rivalry_data in club_data.get("rivalries", {}).items():
            intensity = float(rivalry_data.get("intensity", 0.5))
            rival_team_node_id = f"team_{rival_id}"
            # Ensure rival node exists (minimal stub — will be enriched if rival has a file)
            rival_display = rival_id.replace("_", " ").title()
            get_or_create_node(conn, rival_team_node_id, "team", rival_display,
                               f"Football club — rival of {club_name}",
                               {"league": league_id, "sport": sport})

            get_or_create_edge(
                conn, team_node_id, rival_team_node_id, "rival_of", intensity,
                {
                    "derby_name": rivalry_data.get("name"),
                    "intensity_raw": intensity,
                    "sport": sport,
                }
            )
            # Bidirectional
            get_or_create_edge(
                conn, rival_team_node_id, team_node_id, "rival_of", intensity,
                {
                    "derby_name": rivalry_data.get("name"),
                    "intensity_raw": intensity,
                    "sport": sport,
                }
            )
            stats["rivalry_edges"] += 1

        if verbose:
            print(f"  [ok] {club_name}: {len(club_data.get('legends',[]))} legends, "
                  f"{len(club_data.get('iconic_moments',[]))} moments, "
                  f"{len(club_data.get('rivalries',{}))} rivalries")

    conn.commit()

    # Rebuild FTS index
    ensure_fts_sync(conn)
    conn.commit()
    conn.close()

    print(f"[build_kg] Complete: {stats['team_nodes']} teams, {stats['legend_nodes']} legends, "
          f"{stats['moment_nodes']} moments, {stats['rivalry_edges']} rivalry pairs, "
          f"{stats['stadium_nodes']} stadiums")
    return stats


def verify_kg(league_id: str) -> dict:
    """Verify KG nodes and edges were created for a league."""
    conn = sqlite3.connect(str(KG_DB))
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM nodes WHERE node_type='team' AND json_extract(properties,'$.league')=?",
        (league_id,)
    )
    team_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM nodes WHERE node_type='legend' AND json_extract(properties,'$.league')=?",
        (league_id,)
    )
    legend_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM edges WHERE relationship='rival_of' AND json_extract(properties,'$.sport')='football'"
    )
    rivalry_count = cursor.fetchone()[0]

    conn.close()
    return {
        "league_id": league_id,
        "team_nodes": team_count,
        "legend_nodes": legend_count,
        "rivalry_edges": rivalry_count,
    }


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Build KG nodes and edges for a league")
    parser.add_argument("--league", help="League ID (e.g. la_liga, premier_league)")
    parser.add_argument("--all", action="store_true", help="Build KG for all registered leagues")
    parser.add_argument("--verify", action="store_true", help="Verify results after building")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not args.league and not args.all:
        parser.print_help()
        sys.exit(1)

    if args.all:
        from league_loader import ALL_LEAGUES
        leagues = list(ALL_LEAGUES.keys())
    else:
        leagues = [args.league]

    for league_id in leagues:
        try:
            stats = build_league_kg(league_id, verbose=args.verbose)
            if args.verify:
                v = verify_kg(league_id)
                print(f"[verify] {league_id}: {v['team_nodes']} teams, "
                      f"{v['legend_nodes']} legends, {v['rivalry_edges']} rivalry edges in KG")
        except Exception as e:
            print(f"[error] Failed for {league_id}: {e}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()

    print("\n[done]")


if __name__ == "__main__":
    main()
