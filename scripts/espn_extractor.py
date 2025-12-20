#!/usr/bin/env python3
"""
ESPN Soccer Data Extractor for Soccer-AI
Fetches games and standings from ESPN API (stdlib only - no pip dependencies)
"""

import urllib.request
import urllib.error
import json
import time
import sqlite3
import os
import argparse
from datetime import datetime, date

# Configuration
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "soccer_ai.db")

# ESPN API endpoints
ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
ESPN_STANDINGS = "https://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings"

# Team name mapping (ESPN name -> our DB name)
TEAM_NAME_MAP = {
    "Manchester City": "Manchester City",
    "Liverpool": "Liverpool",
    "Arsenal": "Arsenal",
    "Chelsea": "Chelsea",
    "Manchester United": "Manchester United",
    "Tottenham Hotspur": "Tottenham",
    "Newcastle United": "Newcastle United",
    "Brighton & Hove Albion": "Brighton",
    "Brighton and Hove Albion": "Brighton",
    "Aston Villa": "Aston Villa",
    "West Ham United": "West Ham",
    "Fulham": "Fulham",
    "Brentford": "Brentford",
    "Crystal Palace": "Crystal Palace",
    "Wolverhampton Wanderers": "Wolverhampton",
    "Wolves": "Wolverhampton",
    "Bournemouth": "Bournemouth",
    "AFC Bournemouth": "Bournemouth",
    "Nottingham Forest": "Nottingham Forest",
    "Everton": "Everton",
    "Luton Town": "Luton Town",
    "Burnley": "Burnley",
    "Sheffield United": "Sheffield United",
    "Ipswich Town": "Ipswich Town",
    "Leicester City": "Leicester City",
    "Southampton": "Southampton",
}


def fetch_url(url: str, retries: int = 3) -> str:
    """Fetch URL with retries and rate limiting."""
    headers = {"User-Agent": USER_AGENT}

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            print(f"  HTTP Error {e.code}: {e.reason}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
        except urllib.error.URLError as e:
            print(f"  URL Error: {e.reason}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
        except Exception as e:
            print(f"  Error: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
    return ""


def normalize_team_name(name: str) -> str:
    """Normalize ESPN team name to our database format."""
    if name in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[name]
    # Try partial matches
    for espn_name, db_name in TEAM_NAME_MAP.items():
        if espn_name.lower() in name.lower() or name.lower() in espn_name.lower():
            return db_name
    return name


def extract_games(data: dict) -> list:
    """Extract games from ESPN API response."""
    games = []

    for event in data.get("events", []):
        try:
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])

            if len(competitors) >= 2:
                home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
                away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

                home_team = home.get("team", {}).get("displayName", "")
                away_team = away.get("team", {}).get("displayName", "")

                # Get scores (may be None for scheduled games)
                home_score = home.get("score")
                away_score = away.get("score")

                # Parse status
                status_info = event.get("status", {})
                status_type = status_info.get("type", {}).get("name", "STATUS_SCHEDULED")

                # Map ESPN status to our status
                status_map = {
                    "STATUS_SCHEDULED": "scheduled",
                    "STATUS_IN_PROGRESS": "live",
                    "STATUS_HALFTIME": "live",
                    "STATUS_FINAL": "finished",
                    "STATUS_FULL_TIME": "finished",
                    "STATUS_POSTPONED": "postponed",
                    "STATUS_CANCELED": "cancelled",
                }
                status = status_map.get(status_type, "scheduled")

                # Parse date
                game_date = event.get("date", "")

                # Venue
                venue = competition.get("venue", {}).get("fullName", "")

                games.append({
                    "home_team": normalize_team_name(home_team),
                    "away_team": normalize_team_name(away_team),
                    "home_score": int(home_score) if home_score and home_score != "" else None,
                    "away_score": int(away_score) if away_score and away_score != "" else None,
                    "game_date": game_date,
                    "status": status,
                    "venue": venue,
                    "competition": "Premier League"
                })
        except Exception as e:
            print(f"  Warning: Failed to parse event: {e}")
            continue

    return games


def extract_standings(data: dict) -> list:
    """Extract standings from ESPN API response."""
    standings = []

    # ESPN v2 standings structure: children[0].standings.entries
    children = data.get("children", [])
    if not children:
        print("  Warning: No standings data found")
        return standings

    for group in children:
        entries = group.get("standings", {}).get("entries", [])

        for idx, entry in enumerate(entries):
            try:
                team = entry.get("team", {})
                team_name = team.get("displayName", "")

                # Get position from note.rank or index
                note = entry.get("note", {})
                position = note.get("rank", idx + 1)

                # Get stats as dict
                stats = {}
                for stat in entry.get("stats", []):
                    stat_name = stat.get("name", "")
                    stat_value = stat.get("value", 0)
                    stats[stat_name] = stat_value

                standings.append({
                    "team_name": normalize_team_name(team_name),
                    "position": int(position),
                    "played": int(stats.get("gamesPlayed", 0)),
                    "won": int(stats.get("wins", 0)),
                    "drawn": int(stats.get("ties", 0)),
                    "lost": int(stats.get("losses", 0)),
                    "goals_for": int(stats.get("pointsFor", 0)),
                    "goals_against": int(stats.get("pointsAgainst", 0)),
                    "points": int(stats.get("points", 0)),
                    "goal_diff": int(stats.get("pointDifferential", 0))
                })
            except Exception as e:
                print(f"  Warning: Failed to parse standing entry: {e}")
                continue

    return standings


def get_team_id(cursor, team_name: str) -> int:
    """Get team ID by name, handling variations."""
    # Try exact match
    cursor.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
    result = cursor.fetchone()
    if result:
        return result[0]

    # Try case-insensitive match
    cursor.execute("SELECT id FROM teams WHERE LOWER(name) = LOWER(?)", (team_name,))
    result = cursor.fetchone()
    if result:
        return result[0]

    # Try fuzzy match (contains)
    cursor.execute("SELECT id FROM teams WHERE name LIKE ?", (f"%{team_name}%",))
    result = cursor.fetchone()
    if result:
        return result[0]

    # Try short name
    cursor.execute("SELECT id FROM teams WHERE short_name = ?", (team_name,))
    result = cursor.fetchone()
    if result:
        return result[0]

    return None


def upsert_game(cursor, game: dict) -> bool:
    """Insert or update a game."""
    home_id = get_team_id(cursor, game["home_team"])
    away_id = get_team_id(cursor, game["away_team"])

    if not home_id:
        print(f"  Skipping: Unknown home team ({game['home_team']})")
        return False
    if not away_id:
        print(f"  Skipping: Unknown away team ({game['away_team']})")
        return False

    # Parse date for comparison
    game_date = game["game_date"]

    # Check if game exists (same teams, same date)
    cursor.execute("""
        SELECT id FROM games
        WHERE home_team_id = ? AND away_team_id = ? AND DATE(date) = DATE(?)
    """, (home_id, away_id, game_date))

    existing = cursor.fetchone()

    if existing:
        # Update existing game
        cursor.execute("""
            UPDATE games SET
                home_score = COALESCE(?, home_score),
                away_score = COALESCE(?, away_score),
                status = ?,
                venue = COALESCE(?, venue),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (game["home_score"], game["away_score"], game["status"],
              game["venue"], existing[0]))
        return True
    else:
        # Insert new game
        cursor.execute("""
            INSERT INTO games (home_team_id, away_team_id, date, time, venue,
                             competition, status, home_score, away_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (home_id, away_id, game_date[:10] if len(game_date) >= 10 else game_date,
              game_date[11:16] if len(game_date) >= 16 else None,
              game["venue"], game["competition"], game["status"],
              game["home_score"], game["away_score"]))
        return True


def upsert_standing(cursor, standing: dict, season: str = "2024-25") -> bool:
    """Insert or update a standing."""
    team_id = get_team_id(cursor, standing["team_name"])

    if not team_id:
        print(f"  Skipping: Unknown team ({standing['team_name']})")
        return False

    # Check if standing exists
    cursor.execute("""
        SELECT id FROM standings WHERE team_id = ? AND season = ?
    """, (team_id, season))

    existing = cursor.fetchone()

    if existing:
        # Update
        cursor.execute("""
            UPDATE standings SET
                position = ?,
                played = ?,
                won = ?,
                drawn = ?,
                lost = ?,
                goals_for = ?,
                goals_against = ?,
                points = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (standing["position"], standing["played"], standing["won"],
              standing["drawn"], standing["lost"], standing["goals_for"],
              standing["goals_against"], standing["points"], existing[0]))
    else:
        # Insert
        cursor.execute("""
            INSERT INTO standings (team_id, league, season, position, played,
                                  won, drawn, lost, goals_for, goals_against, points)
            VALUES (?, 'Premier League', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (team_id, season, standing["position"], standing["played"],
              standing["won"], standing["drawn"], standing["lost"],
              standing["goals_for"], standing["goals_against"], standing["points"]))

    return True


def ensure_teams_exist(cursor, games: list, standings: list):
    """Ensure all teams from fetched data exist in database."""
    all_teams = set()

    for game in games:
        all_teams.add(game["home_team"])
        all_teams.add(game["away_team"])

    for standing in standings:
        all_teams.add(standing["team_name"])

    for team_name in all_teams:
        if not get_team_id(cursor, team_name):
            print(f"  Adding missing team: {team_name}")
            cursor.execute("""
                INSERT INTO teams (name, league, country)
                VALUES (?, 'Premier League', 'England')
            """, (team_name,))


def main():
    parser = argparse.ArgumentParser(description="ESPN Soccer Data Extractor")
    parser.add_argument("--games", action="store_true", help="Fetch today's/recent games")
    parser.add_argument("--standings", action="store_true", help="Fetch current standings")
    parser.add_argument("--all", action="store_true", help="Fetch everything")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to database")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.all:
        args.games = args.standings = True

    if not any([args.games, args.standings]):
        parser.print_help()
        return

    print(f"ESPN Extractor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_PATH}")
    print()

    # Check database exists
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    games = []
    standings = []

    try:
        # Fetch games
        if args.games:
            print("Fetching games from ESPN API...")
            try:
                raw_data = fetch_url(ESPN_SCOREBOARD)
                data = json.loads(raw_data)
                games = extract_games(data)
                print(f"  Found {len(games)} games")

                if args.verbose:
                    for g in games:
                        score = f"{g['home_score']}-{g['away_score']}" if g['home_score'] is not None else "vs"
                        print(f"    {g['home_team']} {score} {g['away_team']} ({g['status']})")
            except Exception as e:
                print(f"  ERROR fetching games: {e}")

        # Fetch standings
        if args.standings:
            print("Fetching standings from ESPN API...")
            try:
                raw_data = fetch_url(ESPN_STANDINGS)
                data = json.loads(raw_data)
                standings = extract_standings(data)
                print(f"  Found {len(standings)} teams in standings")

                if args.verbose:
                    for s in standings[:5]:  # Top 5
                        print(f"    {s['position']}. {s['team_name']} - {s['points']} pts")
            except Exception as e:
                print(f"  ERROR fetching standings: {e}")

        # Save to database
        if not args.dry_run:
            print()
            print("Saving to database...")

            # Ensure all teams exist
            ensure_teams_exist(cursor, games, standings)

            # Save games
            if games:
                saved = 0
                for game in games:
                    if upsert_game(cursor, game):
                        saved += 1
                conn.commit()
                print(f"  Saved {saved}/{len(games)} games")

            # Save standings
            if standings:
                saved = 0
                for standing in standings:
                    if upsert_standing(cursor, standing):
                        saved += 1
                conn.commit()
                print(f"  Saved {saved}/{len(standings)} standings")
        else:
            print()
            print("[DRY RUN - No database changes made]")

        print()
        print("Done!")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
