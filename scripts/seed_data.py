"""
Soccer-AI Seed Data Script
Populates database with sample Premier League data for testing
"""

import sys
from pathlib import Path
from datetime import datetime, date, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import database


def seed_teams():
    """Seed Premier League teams."""
    teams = [
        {"name": "Manchester City", "short_name": "MAN CITY", "league": "Premier League", "country": "England", "stadium": "Etihad Stadium", "founded": 1880},
        {"name": "Liverpool", "short_name": "LIV", "league": "Premier League", "country": "England", "stadium": "Anfield", "founded": 1892},
        {"name": "Arsenal", "short_name": "ARS", "league": "Premier League", "country": "England", "stadium": "Emirates Stadium", "founded": 1886},
        {"name": "Chelsea", "short_name": "CHE", "league": "Premier League", "country": "England", "stadium": "Stamford Bridge", "founded": 1905},
        {"name": "Manchester United", "short_name": "MAN UTD", "league": "Premier League", "country": "England", "stadium": "Old Trafford", "founded": 1878},
        {"name": "Tottenham", "short_name": "TOT", "league": "Premier League", "country": "England", "stadium": "Tottenham Hotspur Stadium", "founded": 1882},
        {"name": "Newcastle United", "short_name": "NEW", "league": "Premier League", "country": "England", "stadium": "St James' Park", "founded": 1892},
        {"name": "Brighton", "short_name": "BHA", "league": "Premier League", "country": "England", "stadium": "Amex Stadium", "founded": 1901},
        {"name": "Aston Villa", "short_name": "AVL", "league": "Premier League", "country": "England", "stadium": "Villa Park", "founded": 1874},
        {"name": "West Ham", "short_name": "WHU", "league": "Premier League", "country": "England", "stadium": "London Stadium", "founded": 1895},
    ]

    print("Seeding teams...")
    for team in teams:
        try:
            team_id = database.insert_team(team)
            print(f"  + {team['name']} (ID: {team_id})")
        except Exception as e:
            print(f"  ! {team['name']}: {e}")

    return len(teams)


def seed_players():
    """Seed sample players."""
    # Get team IDs
    with database.get_connection() as conn:
        cursor = conn.execute("SELECT id, name FROM teams")
        teams = {row["name"]: row["id"] for row in cursor.fetchall()}

    players = [
        # Manchester City
        {"name": "Erling Haaland", "team_id": teams.get("Manchester City"), "position": "Forward", "nationality": "Norway", "jersey_number": 9},
        {"name": "Kevin De Bruyne", "team_id": teams.get("Manchester City"), "position": "Midfielder", "nationality": "Belgium", "jersey_number": 17},
        {"name": "Phil Foden", "team_id": teams.get("Manchester City"), "position": "Midfielder", "nationality": "England", "jersey_number": 47},

        # Liverpool
        {"name": "Mohamed Salah", "team_id": teams.get("Liverpool"), "position": "Forward", "nationality": "Egypt", "jersey_number": 11},
        {"name": "Virgil van Dijk", "team_id": teams.get("Liverpool"), "position": "Defender", "nationality": "Netherlands", "jersey_number": 4},
        {"name": "Darwin Nunez", "team_id": teams.get("Liverpool"), "position": "Forward", "nationality": "Uruguay", "jersey_number": 9},

        # Arsenal
        {"name": "Bukayo Saka", "team_id": teams.get("Arsenal"), "position": "Forward", "nationality": "England", "jersey_number": 7},
        {"name": "Martin Odegaard", "team_id": teams.get("Arsenal"), "position": "Midfielder", "nationality": "Norway", "jersey_number": 8},
        {"name": "Gabriel Jesus", "team_id": teams.get("Arsenal"), "position": "Forward", "nationality": "Brazil", "jersey_number": 9},

        # Chelsea
        {"name": "Cole Palmer", "team_id": teams.get("Chelsea"), "position": "Midfielder", "nationality": "England", "jersey_number": 20},
        {"name": "Nicolas Jackson", "team_id": teams.get("Chelsea"), "position": "Forward", "nationality": "Senegal", "jersey_number": 15},

        # Manchester United
        {"name": "Bruno Fernandes", "team_id": teams.get("Manchester United"), "position": "Midfielder", "nationality": "Portugal", "jersey_number": 8},
        {"name": "Marcus Rashford", "team_id": teams.get("Manchester United"), "position": "Forward", "nationality": "England", "jersey_number": 10},
        {"name": "Rasmus Hojlund", "team_id": teams.get("Manchester United"), "position": "Forward", "nationality": "Denmark", "jersey_number": 11},

        # Tottenham
        {"name": "Son Heung-min", "team_id": teams.get("Tottenham"), "position": "Forward", "nationality": "South Korea", "jersey_number": 7},
        {"name": "James Maddison", "team_id": teams.get("Tottenham"), "position": "Midfielder", "nationality": "England", "jersey_number": 10},
    ]

    print("Seeding players...")
    for player in players:
        try:
            player_id = database.insert_player(player)
            print(f"  + {player['name']} (ID: {player_id})")
        except Exception as e:
            print(f"  ! {player['name']}: {e}")

    return len(players)


def seed_games():
    """Seed sample games."""
    with database.get_connection() as conn:
        cursor = conn.execute("SELECT id, name FROM teams")
        teams = {row["name"]: row["id"] for row in cursor.fetchall()}

    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    games = [
        # Yesterday's games
        {
            "date": yesterday.isoformat(),
            "time": "20:00",
            "home_team_id": teams.get("Manchester United"),
            "away_team_id": teams.get("West Ham"),
            "home_score": 2,
            "away_score": 1,
            "status": "finished",
            "competition": "Premier League",
            "matchday": 17,
            "venue": "Old Trafford",
            "attendance": 73500
        },
        {
            "date": yesterday.isoformat(),
            "time": "17:30",
            "home_team_id": teams.get("Arsenal"),
            "away_team_id": teams.get("Brighton"),
            "home_score": 3,
            "away_score": 0,
            "status": "finished",
            "competition": "Premier League",
            "matchday": 17,
            "venue": "Emirates Stadium",
            "attendance": 60200
        },
        # Today's games
        {
            "date": today.isoformat(),
            "time": "15:00",
            "home_team_id": teams.get("Liverpool"),
            "away_team_id": teams.get("Tottenham"),
            "status": "scheduled",
            "competition": "Premier League",
            "matchday": 18,
            "venue": "Anfield"
        },
        {
            "date": today.isoformat(),
            "time": "20:00",
            "home_team_id": teams.get("Manchester City"),
            "away_team_id": teams.get("Chelsea"),
            "status": "scheduled",
            "competition": "Premier League",
            "matchday": 18,
            "venue": "Etihad Stadium"
        },
        # Tomorrow's games
        {
            "date": tomorrow.isoformat(),
            "time": "15:00",
            "home_team_id": teams.get("Newcastle United"),
            "away_team_id": teams.get("Aston Villa"),
            "status": "scheduled",
            "competition": "Premier League",
            "matchday": 18,
            "venue": "St James' Park"
        },
    ]

    print("Seeding games...")
    for game in games:
        try:
            game_id = database.insert_game(game)
            home = [k for k, v in teams.items() if v == game["home_team_id"]][0]
            away = [k for k, v in teams.items() if v == game["away_team_id"]][0]
            print(f"  + {home} vs {away} ({game['date']}) (ID: {game_id})")
        except Exception as e:
            print(f"  ! Game: {e}")

    return len(games)


def seed_injuries():
    """Seed sample injuries."""
    with database.get_connection() as conn:
        cursor = conn.execute("SELECT id, name FROM players")
        players = {row["name"]: row["id"] for row in cursor.fetchall()}

    injuries = [
        {
            "player_id": players.get("Kevin De Bruyne"),
            "injury_type": "Hamstring",
            "severity": "Moderate",
            "occurred_date": (date.today() - timedelta(days=14)).isoformat(),
            "expected_return": (date.today() + timedelta(days=7)).isoformat(),
            "status": "active"
        },
        {
            "player_id": players.get("Gabriel Jesus"),
            "injury_type": "Knee",
            "severity": "Severe",
            "occurred_date": (date.today() - timedelta(days=30)).isoformat(),
            "expected_return": (date.today() + timedelta(days=60)).isoformat(),
            "status": "active"
        },
        {
            "player_id": players.get("James Maddison"),
            "injury_type": "Ankle",
            "severity": "Minor",
            "occurred_date": (date.today() - timedelta(days=5)).isoformat(),
            "expected_return": (date.today() + timedelta(days=3)).isoformat(),
            "status": "active"
        },
    ]

    print("Seeding injuries...")
    with database.get_connection() as conn:
        for injury in injuries:
            if injury["player_id"]:
                try:
                    conn.execute("""
                        INSERT INTO injuries (player_id, injury_type, severity, occurred_date, expected_return, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        injury["player_id"],
                        injury["injury_type"],
                        injury["severity"],
                        injury["occurred_date"],
                        injury["expected_return"],
                        injury["status"]
                    ))
                    player_name = [k for k, v in players.items() if v == injury["player_id"]][0]
                    print(f"  + {player_name}: {injury['injury_type']}")
                except Exception as e:
                    print(f"  ! Injury: {e}")
        conn.commit()

    return len(injuries)


def seed_standings():
    """Seed Premier League standings."""
    with database.get_connection() as conn:
        cursor = conn.execute("SELECT id, name FROM teams WHERE league = 'Premier League'")
        teams = [(row["id"], row["name"]) for row in cursor.fetchall()]

    standings_data = [
        ("Liverpool", 1, 17, 13, 3, 1, 40, 15, 25, 42, "WWWDW"),
        ("Arsenal", 2, 17, 11, 5, 1, 35, 14, 21, 38, "WDWDW"),
        ("Manchester City", 3, 17, 10, 4, 3, 38, 20, 18, 34, "WWLWW"),
        ("Chelsea", 4, 17, 9, 5, 3, 32, 18, 14, 32, "DWWLW"),
        ("Newcastle United", 5, 17, 9, 4, 4, 28, 18, 10, 31, "WLWWD"),
        ("Manchester United", 6, 17, 8, 4, 5, 24, 19, 5, 28, "WDLLW"),
        ("Tottenham", 7, 17, 8, 3, 6, 30, 24, 6, 27, "LLDWW"),
        ("Brighton", 8, 17, 7, 6, 4, 26, 22, 4, 27, "DDWLD"),
        ("Aston Villa", 9, 17, 7, 5, 5, 25, 23, 2, 26, "LWDWD"),
        ("West Ham", 10, 17, 6, 5, 6, 22, 24, -2, 23, "LLWDL"),
    ]

    print("Seeding standings...")
    with database.get_connection() as conn:
        team_dict = {name: tid for tid, name in teams}
        for team_name, pos, played, won, drawn, lost, gf, ga, gd, pts, form in standings_data:
            team_id = team_dict.get(team_name)
            if team_id:
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO standings
                        (team_id, league, season, position, played, won, drawn, lost,
                         goals_for, goals_against, goal_difference, points, form)
                        VALUES (?, 'Premier League', '2024-25', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (team_id, pos, played, won, drawn, lost, gf, ga, gd, pts, form))
                    print(f"  + {pos}. {team_name} ({pts} pts)")
                except Exception as e:
                    print(f"  ! {team_name}: {e}")
        conn.commit()

    return len(standings_data)


def seed_news():
    """Seed sample news articles."""
    news_articles = [
        {
            "title": "Haaland scores hat-trick as City thrash Brighton",
            "content": "Erling Haaland continued his incredible scoring form with a hat-trick as Manchester City demolished Brighton 4-0 at the Etihad Stadium.",
            "summary": "Haaland hat-trick powers City to 4-0 win over Brighton.",
            "source": "ESPN",
            "category": "match_report",
            "published_at": datetime.now().isoformat(),
        },
        {
            "title": "Liverpool move top after Salah masterclass",
            "content": "Mohamed Salah scored twice and provided an assist as Liverpool moved to the top of the Premier League table with a 3-1 win over Aston Villa.",
            "summary": "Salah's brace sends Liverpool top of the table.",
            "source": "BBC Sport",
            "category": "match_report",
            "published_at": (datetime.now() - timedelta(days=1)).isoformat(),
        },
        {
            "title": "De Bruyne injury update: City star to miss 3 weeks",
            "content": "Manchester City have confirmed that Kevin De Bruyne will be sidelined for approximately three weeks with a hamstring injury sustained in training.",
            "summary": "De Bruyne out for 3 weeks with hamstring injury.",
            "source": "Sky Sports",
            "category": "injury",
            "published_at": (datetime.now() - timedelta(days=2)).isoformat(),
        },
        {
            "title": "Transfer rumor: Chelsea eye January move for Victor Osimhen",
            "content": "Chelsea are reportedly interested in signing Napoli striker Victor Osimhen in the January transfer window as they look to strengthen their attack.",
            "summary": "Chelsea linked with January move for Osimhen.",
            "source": "The Athletic",
            "category": "transfer",
            "published_at": (datetime.now() - timedelta(hours=6)).isoformat(),
        },
        {
            "title": "Arsenal vs Man City preview: Title showdown at Emirates",
            "content": "Arsenal host Manchester City in a crucial Premier League clash that could have major implications for the title race.",
            "summary": "Arsenal and Man City face off in potential title decider.",
            "source": "ESPN",
            "category": "preview",
            "published_at": datetime.now().isoformat(),
        },
    ]

    print("Seeding news...")
    for article in news_articles:
        try:
            news_id = database.insert_news(article)
            print(f"  + {article['title'][:50]}... (ID: {news_id})")
        except Exception as e:
            print(f"  ! {article['title'][:30]}: {e}")

    return len(news_articles)


def main():
    """Run all seed functions."""
    print("=" * 50)
    print("Soccer-AI Data Seeding")
    print("=" * 50)

    # Initialize database
    print("\nInitializing database...")
    database.init_db()

    # Seed data
    teams_count = seed_teams()
    players_count = seed_players()
    games_count = seed_games()
    injuries_count = seed_injuries()
    standings_count = seed_standings()
    news_count = seed_news()

    # Summary
    print("\n" + "=" * 50)
    print("Seeding Complete!")
    print("=" * 50)
    print(f"Teams:     {teams_count}")
    print(f"Players:   {players_count}")
    print(f"Games:     {games_count}")
    print(f"Injuries:  {injuries_count}")
    print(f"Standings: {standings_count}")
    print(f"News:      {news_count}")

    # Verify
    print("\nDatabase stats:")
    stats = database.get_db_stats()
    for table, count in stats.items():
        print(f"  {table}: {count}")


if __name__ == "__main__":
    main()
