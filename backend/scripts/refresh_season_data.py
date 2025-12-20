"""
Soccer-AI Season Data Refresh Script

Fetches current 2025-26 Premier League data from football-data.org
and updates the local SQLite database (standings, games, form).

Usage:
    cd backend && python scripts/refresh_season_data.py
    cd backend && python scripts/refresh_season_data.py --dry-run
    cd backend && python scripts/refresh_season_data.py --days-back 30 --days-ahead 21

API: football-data.org free tier (10 requests/minute)
"""

import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Resolve paths relative to this script's location (backend/scripts/)
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

# Add backend to path so we can import football_api
sys.path.insert(0, str(BACKEND_DIR))

from football_api import FootballDataAPI

DB_PATH = BACKEND_DIR / "soccer_ai.db"
SEASON = "2025-26"
LEAGUE = "Premier League"

# football-data.org uses different team names than our DB.
# Map their names to ours.
API_NAME_TO_DB_NAME = {
    "Manchester City FC": "Manchester City",
    "Liverpool FC": "Liverpool",
    "Arsenal FC": "Arsenal",
    "Chelsea FC": "Chelsea",
    "Manchester United FC": "Manchester United",
    "Tottenham Hotspur FC": "Tottenham",
    "Newcastle United FC": "Newcastle United",
    "Brighton & Hove Albion FC": "Brighton",
    "Aston Villa FC": "Aston Villa",
    "West Ham United FC": "West Ham",
    "Brentford FC": "Brentford",
    "Crystal Palace FC": "Crystal Palace",
    "Nottingham Forest FC": "Nottingham Forest",
    "Everton FC": "Everton",
    "Wolverhampton Wanderers FC": "Wolverhampton",
    "AFC Bournemouth": "Bournemouth",
    "Fulham FC": "Fulham",
    "Leicester City FC": "Leicester City",
    "Ipswich Town FC": "Ipswich Town",
    "Southampton FC": "Southampton",
    # Promoted clubs for 2025-26 (adjust if needed)
    "Burnley FC": "Burnley",
    "Leeds United FC": "Leeds United",
    "Sunderland AFC": "Sunderland",
    "Sheffield United FC": "Sheffield United",
    "Luton Town FC": "Luton Town",
}

# Rate limiter: free tier = 10 requests/minute
_last_request_times = []
RATE_LIMIT = 10
RATE_WINDOW = 60  # seconds


def rate_limit_wait():
    """Block if we're about to exceed 10 requests/minute."""
    now = time.time()
    # Purge old timestamps
    while _last_request_times and now - _last_request_times[0] > RATE_WINDOW:
        _last_request_times.pop(0)

    if len(_last_request_times) >= RATE_LIMIT:
        wait_until = _last_request_times[0] + RATE_WINDOW
        sleep_time = wait_until - now + 0.5  # small buffer
        if sleep_time > 0:
            print(f"  [rate-limit] Waiting {sleep_time:.1f}s to stay under 10 req/min...")
            time.sleep(sleep_time)

    _last_request_times.append(time.time())


def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Open a connection with row_factory."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def resolve_team_name(api_name: str) -> str:
    """Convert football-data.org team name to our DB name."""
    if api_name in API_NAME_TO_DB_NAME:
        return API_NAME_TO_DB_NAME[api_name]
    # Fallback: strip trailing "FC" / "AFC" and try
    cleaned = api_name.replace(" FC", "").replace("AFC ", "").strip()
    return cleaned


def load_team_id_map(conn: sqlite3.Connection) -> dict:
    """Load {team_name: team_id} from the teams table."""
    cursor = conn.execute("SELECT id, name FROM teams")
    return {row["name"]: row["id"] for row in cursor.fetchall()}


def ensure_team_exists(conn: sqlite3.Connection, team_name: str, team_map: dict) -> int:
    """Insert team if missing, return team_id."""
    if team_name in team_map:
        return team_map[team_name]

    cursor = conn.execute(
        "INSERT INTO teams (name, league, country) VALUES (?, ?, ?)",
        (team_name, LEAGUE, "England"),
    )
    team_id = cursor.lastrowid
    team_map[team_name] = team_id
    return team_id


# ─── Standings Update ────────────────────────────────────────────────

def fetch_and_update_standings(api: FootballDataAPI, conn: sqlite3.Connection,
                                team_map: dict, dry_run: bool) -> dict:
    """Fetch current PL standings and upsert into DB."""
    print("\n=== Fetching Standings ===")
    rate_limit_wait()
    standings_data = api.get_standings("PL")

    matchday = standings_data.get("matchday", "?")
    api_season = standings_data.get("season", "?")
    print(f"  Season: {api_season}, Matchday: {matchday}")

    updated = 0
    inserted = 0
    teams_seen = []

    for entry in standings_data.get("standings", []):
        api_team_name = entry["team"]
        db_team_name = resolve_team_name(api_team_name)
        team_id = ensure_team_exists(conn, db_team_name, team_map)

        row = {
            "team_id": team_id,
            "league": LEAGUE,
            "season": SEASON,
            "position": entry["position"],
            "played": entry["played"],
            "won": entry["won"],
            "drawn": entry["drawn"],
            "lost": entry["lost"],
            "goals_for": entry["goals_for"],
            "goals_against": entry["goals_against"],
            "goal_difference": entry["goal_diff"],
            "points": entry["points"],
            "form": entry.get("form", ""),
        }

        teams_seen.append(f"  {row['position']:>2}. {db_team_name:<25} {row['points']:>3} pts  "
                          f"({row['won']}W {row['drawn']}D {row['lost']}L)  "
                          f"Form: {row['form'] or 'N/A'}")

        if dry_run:
            continue

        # Upsert: the standings table has UNIQUE(team_id, league, season)
        existing = conn.execute(
            "SELECT id FROM standings WHERE team_id = ? AND league = ? AND season = ?",
            (team_id, LEAGUE, SEASON),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE standings SET position=?, played=?, won=?, drawn=?, lost=?,
                   goals_for=?, goals_against=?, goal_difference=?, points=?, form=?,
                   updated_at=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (row["position"], row["played"], row["won"], row["drawn"], row["lost"],
                 row["goals_for"], row["goals_against"], row["goal_difference"],
                 row["points"], row["form"], existing["id"]),
            )
            updated += 1
        else:
            conn.execute(
                """INSERT INTO standings (team_id, league, season, position, played, won,
                   drawn, lost, goals_for, goals_against, goal_difference, points, form)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (team_id, LEAGUE, SEASON, row["position"], row["played"], row["won"],
                 row["drawn"], row["lost"], row["goals_for"], row["goals_against"],
                 row["goal_difference"], row["points"], row["form"]),
            )
            inserted += 1

    for line in teams_seen:
        print(line)

    return {"updated": updated, "inserted": inserted, "total": len(teams_seen),
            "matchday": matchday}


# ─── Games/Fixtures Update ──────────────────────────────────────────

def fetch_and_update_games(api: FootballDataAPI, conn: sqlite3.Connection,
                            team_map: dict, dry_run: bool,
                            days_back: int, days_ahead: int) -> dict:
    """Fetch recent results + upcoming fixtures and upsert into games table."""
    print("\n=== Fetching Recent Results ===")
    rate_limit_wait()
    recent = api.get_recent_results(days_back=days_back)
    print(f"  Found {len(recent)} finished matches (last {days_back} days)")

    print("\n=== Fetching Upcoming Fixtures ===")
    rate_limit_wait()
    upcoming = api.get_upcoming_fixtures(days_ahead=days_ahead)
    print(f"  Found {len(upcoming)} scheduled matches (next {days_ahead} days)")

    all_matches = recent + upcoming
    inserted = 0
    updated = 0
    skipped = 0

    for match in all_matches:
        home_name = resolve_team_name(match["home_team"])
        away_name = resolve_team_name(match["away_team"])
        home_id = ensure_team_exists(conn, home_name, team_map)
        away_id = ensure_team_exists(conn, away_name, team_map)

        # Parse date from ISO format
        match_date_str = match["date"][:10] if match.get("date") else None
        match_time_str = match["date"][11:16] if match.get("date") and len(match["date"]) > 11 else None

        status_map = {
            "FINISHED": "finished",
            "SCHEDULED": "scheduled",
            "TIMED": "scheduled",
            "LIVE": "live",
            "IN_PLAY": "live",
            "PAUSED": "live",
            "POSTPONED": "postponed",
            "CANCELLED": "postponed",
        }
        status = status_map.get(match.get("status", ""), match.get("status", "scheduled").lower())

        if not match_date_str:
            skipped += 1
            continue

        if dry_run:
            label = f"  {'[RESULT]' if status == 'finished' else '[FIXTURE]'}"
            score = ""
            if match.get("home_score") is not None:
                score = f" {match['home_score']}-{match['away_score']}"
            print(f"{label} {match_date_str}  {home_name} vs {away_name}{score}")
            continue

        # Check if this exact match already exists (same date + teams)
        existing = conn.execute(
            """SELECT id FROM games
               WHERE date = ? AND home_team_id = ? AND away_team_id = ?""",
            (match_date_str, home_id, away_id),
        ).fetchone()

        if existing:
            # Update score/status if changed
            conn.execute(
                """UPDATE games SET home_score=?, away_score=?, status=?,
                   matchday=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (match.get("home_score"), match.get("away_score"),
                 status, match.get("matchday"), existing["id"]),
            )
            updated += 1
        else:
            conn.execute(
                """INSERT INTO games (date, time, home_team_id, away_team_id,
                   home_score, away_score, status, competition, matchday)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (match_date_str, match_time_str, home_id, away_id,
                 match.get("home_score"), match.get("away_score"),
                 status, LEAGUE, match.get("matchday")),
            )
            inserted += 1

    return {"inserted": inserted, "updated": updated, "skipped": skipped,
            "total_fetched": len(all_matches)}


# ─── Form Update for Mood Computation ───────────────────────────────

def update_form_from_standings(conn: sqlite3.Connection, dry_run: bool) -> dict:
    """
    Copy form strings from standings into club_mood table if it exists.
    The 4D persona system uses club_mood for emotional state computation.
    """
    print("\n=== Updating Club Mood Form Data ===")

    # Check if club_mood table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='club_mood'"
    ).fetchone()

    if not table_check:
        print("  club_mood table not found -- skipping mood update")
        return {"skipped": True, "reason": "no club_mood table"}

    # Get current form from standings
    rows = conn.execute(
        """SELECT s.team_id, t.name, s.form, s.position, s.points
           FROM standings s
           JOIN teams t ON s.team_id = t.id
           WHERE s.season = ?
           ORDER BY s.position""",
        (SEASON,),
    ).fetchall()

    updated = 0
    for row in rows:
        form = row["form"] or ""
        # Derive a simple mood from recent form or W/D/L record
        # W=3, D=1, L=0 -- average over last 5
        form_chars = [c for c in form.replace(",", "") if c in "WDL"]
        recent = form_chars[-5:] if form_chars else []

        if recent:
            score = sum({"W": 3, "D": 1, "L": 0}.get(c, 0) for c in recent)
            max_score = len(recent) * 3
        else:
            # No form string available — compute from W/D/L record
            played = conn.execute(
                "SELECT played, won, drawn, lost FROM standings WHERE team_id = ? AND season = ?",
                (row["team_id"], SEASON)
            ).fetchone()
            if played and played["played"] > 0:
                score = played["won"] * 3 + played["drawn"]
                max_score = played["played"] * 3
            else:
                score = 0
                max_score = 1

        if max_score > 0:
            ratio = score / max_score
            if ratio >= 0.8:
                mood = "euphoric"
            elif ratio >= 0.6:
                mood = "confident"
            elif ratio >= 0.4:
                mood = "steady"
            elif ratio >= 0.2:
                mood = "anxious"
            else:
                mood = "despairing"
        else:
            mood = "steady"

        intensity = round(ratio, 2) if max_score > 0 else 0.5

        if not dry_run:
            # Upsert into club_mood
            existing = conn.execute(
                "SELECT rowid FROM club_mood WHERE team_id = ?", (row["team_id"],)
            ).fetchone()

            if existing:
                conn.execute(
                    """UPDATE club_mood SET current_mood = ?, mood_intensity = ?,
                       form = ?, league_position = ?,
                       mood_reason = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE team_id = ?""",
                    (mood, intensity, form, row["position"],
                     f"Matchday form: {form or 'N/A'}, position {row['position']}",
                     row["team_id"]),
                )
            else:
                try:
                    conn.execute(
                        """INSERT INTO club_mood (team_id, current_mood, mood_intensity,
                           form, league_position, mood_reason)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (row["team_id"], mood, intensity, form, row["position"],
                         f"Matchday form: {form or 'N/A'}, position {row['position']}"),
                    )
                except sqlite3.OperationalError:
                    # Schema mismatch -- skip gracefully
                    pass

        print(f"  {row['name']:<25} Form: {form or 'N/A':<12} Mood: {mood}")
        updated += 1

    return {"updated": updated if not dry_run else 0, "previewed": updated}


# ─── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Refresh Soccer-AI database with current 2025-26 PL season data",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be updated without writing to the database",
    )
    parser.add_argument(
        "--days-back", type=int, default=14,
        help="How many days of recent results to fetch (default: 14)",
    )
    parser.add_argument(
        "--days-ahead", type=int, default=14,
        help="How many days of upcoming fixtures to fetch (default: 14)",
    )
    parser.add_argument(
        "--db", type=str, default=str(DB_PATH),
        help=f"Path to soccer_ai.db (default: {DB_PATH})",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        sys.exit(1)

    if args.dry_run:
        print("=" * 60)
        print("  DRY RUN -- no changes will be written to the database")
        print("=" * 60)

    print(f"Database: {db_path}")
    print(f"Season:   {SEASON}")
    print(f"Date:     {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Initialize API (loads token from .football_api_token)
    try:
        api = FootballDataAPI()
    except ValueError as e:
        print(f"ERROR: {e}")
        print("Make sure .football_api_token exists in the project root with your API key.")
        sys.exit(1)

    conn = get_db_connection(db_path)
    team_map = load_team_id_map(conn)

    summary = {}

    try:
        # 1. Standings (1 API call)
        summary["standings"] = fetch_and_update_standings(api, conn, team_map, args.dry_run)

        # 2. Games -- recent results + upcoming fixtures (2 API calls)
        summary["games"] = fetch_and_update_games(
            api, conn, team_map, args.dry_run, args.days_back, args.days_ahead,
        )

        # 3. Form/mood update (no API call, uses standings data)
        summary["mood"] = update_form_from_standings(conn, args.dry_run)

        if not args.dry_run:
            conn.commit()
            print("\n  Database committed.")
        else:
            print("\n  [dry-run] No changes written.")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        if "rate limit" in str(e).lower() or "429" in str(e):
            print("Hit API rate limit. Wait 60 seconds and try again.")
            print("Free tier allows 10 requests/minute.")
        sys.exit(1)
    finally:
        conn.close()

    # Print summary
    print("\n" + "=" * 60)
    print("  REFRESH SUMMARY")
    print("=" * 60)

    s = summary.get("standings", {})
    print(f"  Standings:  {s.get('total', 0)} teams, "
          f"{s.get('inserted', 0)} new, {s.get('updated', 0)} updated  "
          f"(matchday {s.get('matchday', '?')})")

    g = summary.get("games", {})
    print(f"  Games:      {g.get('total_fetched', 0)} fetched, "
          f"{g.get('inserted', 0)} new, {g.get('updated', 0)} updated, "
          f"{g.get('skipped', 0)} skipped")

    m = summary.get("mood", {})
    if m.get("skipped"):
        print(f"  Mood:       skipped ({m.get('reason', 'unknown')})")
    else:
        print(f"  Mood:       {m.get('updated', 0) or m.get('previewed', 0)} teams processed")

    print(f"\n  API calls used: ~3 of 10/min limit")

    if args.dry_run:
        print("\n  Re-run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
