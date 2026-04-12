"""
League Match History Importer

Reads Club-Football-Match-Data-2000-2025-main/data/Matches.csv and imports
matches for a given league (by division_code) into the unified_soccer_ai_kg.db
match_history table.

Usage:
    python import_match_history.py --league la_liga
    python import_match_history.py --league premier_league
    python import_match_history.py --all
"""

import argparse
import csv
import json
import os
import sqlite3
import sys
from pathlib import Path
from datetime import datetime


# ============================================================================
# PATH SETUP
# ============================================================================

REPO_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
LEAGUES_DIR = REPO_ROOT / "Leagues"
CSV_DIR = REPO_ROOT / "Club-Football-Match-Data-2000-2025-main" / "data"
MATCHES_CSV = CSV_DIR / "Matches.csv"
ELO_CSV = CSV_DIR / "EloRatings.csv"
KG_DB = BACKEND_DIR / "unified_soccer_ai_kg.db"

# Add backend to path for league_loader
sys.path.insert(0, str(BACKEND_DIR))


def get_league_config(league_id: str) -> dict:
    """Load league config from Leagues/{league}/league_config.json."""
    league_dir = LEAGUES_DIR / _league_dir_name(league_id)
    config_path = league_dir / "league_config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"No league config found at {config_path}")
    return json.loads(config_path.read_text())


def _league_dir_name(league_id: str) -> str:
    """Convert league_id to directory name (e.g. la_liga → La_Liga)."""
    return "_".join(w.capitalize() for w in league_id.split("_"))


def ensure_match_history_schema(conn: sqlite3.Connection) -> None:
    """Create match_history and elo_history tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS match_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            division    TEXT NOT NULL,
            match_date  TEXT,
            home_team   TEXT,
            away_team   TEXT,
            ft_home     REAL,
            ft_away     REAL,
            ft_result   TEXT,
            home_elo    REAL,
            away_elo    REAL,
            UNIQUE(division, match_date, home_team, away_team)
        );

        CREATE TABLE IF NOT EXISTS elo_history (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            date    TEXT,
            club    TEXT,
            country TEXT,
            elo     REAL,
            UNIQUE(date, club)
        );

        CREATE INDEX IF NOT EXISTS idx_mh_division   ON match_history(division);
        CREATE INDEX IF NOT EXISTS idx_mh_home_team  ON match_history(home_team);
        CREATE INDEX IF NOT EXISTS idx_mh_away_team  ON match_history(away_team);
        CREATE INDEX IF NOT EXISTS idx_mh_match_date ON match_history(match_date);
        CREATE INDEX IF NOT EXISTS idx_elo_club      ON elo_history(club);
    """)
    conn.commit()


def import_matches(league_id: str, verbose: bool = False) -> dict:
    """Import match history for a league from the CSV file."""
    config = get_league_config(league_id)
    division_code = config.get("division_code")
    display_name = config.get("display_name", league_id)

    if not division_code:
        raise ValueError(f"No division_code in league config for {league_id}")

    if not MATCHES_CSV.exists():
        raise FileNotFoundError(f"Matches CSV not found at {MATCHES_CSV}")

    if not KG_DB.exists():
        raise FileNotFoundError(f"KG database not found at {KG_DB}")

    conn = sqlite3.connect(str(KG_DB))
    ensure_match_history_schema(conn)

    inserted = 0
    skipped = 0
    errors = 0

    print(f"[import] Importing {display_name} (division={division_code}) match history...")

    with open(MATCHES_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        batch = []

        for row in reader:
            if row.get("Division") != division_code:
                continue

            try:
                home_score = float(row["FTHome"]) if row.get("FTHome") else None
                away_score = float(row["FTAway"]) if row.get("FTAway") else None
                home_elo = float(row["HomeElo"]) if row.get("HomeElo") else None
                away_elo = float(row["AwayElo"]) if row.get("AwayElo") else None

                # Normalize result
                result = row.get("FTResult", "").strip()
                if result not in ("H", "D", "A"):
                    result = None

                batch.append((
                    division_code,
                    row.get("MatchDate", "").strip() or None,
                    row.get("HomeTeam", "").strip() or None,
                    row.get("AwayTeam", "").strip() or None,
                    home_score,
                    away_score,
                    result,
                    home_elo,
                    away_elo,
                ))
            except (ValueError, KeyError) as e:
                errors += 1
                if verbose:
                    print(f"  [warn] Row parse error: {e}")

        # Check how many rows already exist for this division to detect re-runs
        existing = conn.execute(
            "SELECT COUNT(*) FROM match_history WHERE division=?", (division_code,)
        ).fetchone()[0]

        # Bulk insert — skip if row already exists (manual dedup since UNIQUE may not exist)
        if existing > 0:
            # Filter out rows that already exist
            existing_keys = set(
                conn.execute(
                    "SELECT match_date, home_team, away_team FROM match_history WHERE division=?",
                    (division_code,)
                ).fetchall()
            )
            batch = [row for row in batch if (row[1], row[2], row[3]) not in existing_keys]
            print(f"[import] {existing} rows already in DB — importing only {len(batch)} new rows")

        try:
            conn.executemany(
                """INSERT OR IGNORE INTO match_history
                   (division, match_date, home_team, away_team, ft_home, ft_away, ft_result, home_elo, away_elo)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                batch
            )
            inserted = conn.total_changes
            skipped = len(batch) - inserted
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Database insert failed: {e}")

    conn.close()

    result = {
        "league_id": league_id,
        "division_code": division_code,
        "rows_in_csv": len(batch),
        "inserted": inserted,
        "skipped_duplicates": skipped,
        "errors": errors,
    }
    print(f"[import] Done: {inserted} new rows inserted, {skipped} duplicates skipped, {errors} errors")
    return result


def import_elo_ratings(verbose: bool = False) -> dict:
    """Import all ELO ratings from EloRatings.csv (league-agnostic)."""
    if not ELO_CSV.exists():
        print(f"[elo] EloRatings.csv not found at {ELO_CSV}, skipping")
        return {"status": "skipped"}

    conn = sqlite3.connect(str(KG_DB))
    ensure_match_history_schema(conn)

    batch = []
    errors = 0

    with open(ELO_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                batch.append((
                    row.get("date", "").strip() or None,
                    row.get("club", "").strip() or None,
                    row.get("country", "").strip() or None,
                    float(row["elo"]) if row.get("elo") else None,
                ))
            except (ValueError, KeyError) as e:
                errors += 1
                if verbose:
                    print(f"  [elo warn] {e}")

    conn.executemany(
        "INSERT OR IGNORE INTO elo_history (date, club, country, elo) VALUES (?,?,?,?)",
        batch
    )
    inserted = conn.total_changes
    conn.commit()
    conn.close()

    result = {"total_elo_rows": len(batch), "inserted": inserted, "errors": errors}
    print(f"[elo] ELO ratings: {inserted} new rows inserted")
    return result


def verify_import(league_id: str) -> dict:
    """Verify match history import for a league."""
    config = get_league_config(league_id)
    division_code = config.get("division_code")

    conn = sqlite3.connect(str(KG_DB))
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT COUNT(*), MIN(match_date), MAX(match_date) FROM match_history WHERE division=?",
            (division_code,)
        )
        row = cursor.fetchone()
        count, min_date, max_date = row if row else (0, None, None)

        cursor.execute(
            "SELECT home_team, COUNT(*) as c FROM match_history WHERE division=? GROUP BY home_team ORDER BY c DESC LIMIT 5",
            (division_code,)
        )
        top_teams = cursor.fetchall()

    finally:
        conn.close()

    return {
        "league_id": league_id,
        "division_code": division_code,
        "total_matches": count,
        "date_range": f"{min_date} → {max_date}",
        "top_5_teams_by_home_games": top_teams,
    }


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Import league match history into Soccer-AI KG database")
    parser.add_argument("--league", help="League ID (e.g. la_liga, premier_league)")
    parser.add_argument("--all", action="store_true", help="Import all registered leagues")
    parser.add_argument("--elo", action="store_true", help="Also import ELO ratings")
    parser.add_argument("--verify", action="store_true", help="Verify import results")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not args.league and not args.all:
        parser.print_help()
        sys.exit(1)

    leagues_to_import = []
    if args.all:
        from league_loader import ALL_LEAGUES
        leagues_to_import = list(ALL_LEAGUES.keys())
    else:
        leagues_to_import = [args.league]

    for league_id in leagues_to_import:
        try:
            result = import_matches(league_id, verbose=args.verbose)
            if args.verify:
                stats = verify_import(league_id)
                print(f"[verify] {league_id}: {stats['total_matches']:,} total matches ({stats['date_range']})")
                for team, count in stats["top_5_teams_by_home_games"]:
                    print(f"  {team}: {count} home games")
        except Exception as e:
            print(f"[error] Failed to import {league_id}: {e}", file=sys.stderr)

    if args.elo:
        import_elo_ratings(verbose=args.verbose)

    print("\n[done] Import complete.")


if __name__ == "__main__":
    main()
