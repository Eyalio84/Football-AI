"""
Football-Data.org API Integration for Soccer-AI

Provides live Premier League data:
- Current standings
- Upcoming fixtures
- Recent results
- Team details

API Documentation: https://www.football-data.org/documentation/quickstart
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path


class FootballDataAPI:
    """
    Client for football-data.org API.

    Provides live Premier League data for fan personas.
    """

    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, api_token: str = None):
        """Initialize with API token."""
        self.api_token = api_token or self._load_token()
        self.headers = {
            "X-Auth-Token": self.api_token
        }

        # Cache for reducing API calls
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    def _load_token(self) -> str:
        """Load token from config file."""
        config_path = Path(__file__).parent.parent / ".football_api_token"
        if config_path.exists():
            return config_path.read_text().strip()
        raise ValueError("API token not provided and .football_api_token not found")

    def _request(self, endpoint: str) -> Dict:
        """Make API request with caching."""
        cache_key = endpoint
        now = datetime.now().timestamp()

        # Check cache
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if now - cached_time < self._cache_ttl:
                return cached_data

        url = f"{self.BASE_URL}{endpoint}"
        req = urllib.request.Request(url, headers=self.headers)

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                self._cache[cache_key] = (now, data)
                return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise Exception("API rate limit exceeded. Wait before retrying.")
            raise Exception(f"API error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            raise Exception(f"Network error: {e.reason}")

    def get_standings(self, competition: str = "PL") -> Dict:
        """
        Get current league standings.

        Args:
            competition: Competition code (PL = Premier League)

        Returns:
            Dict with standings table
        """
        data = self._request(f"/competitions/{competition}/standings")

        standings = []
        if "standings" in data and data["standings"]:
            table = data["standings"][0].get("table", [])
            for team in table:
                standings.append({
                    "position": team.get("position"),
                    "team": team.get("team", {}).get("name"),
                    "team_id": team.get("team", {}).get("id"),
                    "played": team.get("playedGames"),
                    "won": team.get("won"),
                    "drawn": team.get("draw"),
                    "lost": team.get("lost"),
                    "goals_for": team.get("goalsFor"),
                    "goals_against": team.get("goalsAgainst"),
                    "goal_diff": team.get("goalDifference"),
                    "points": team.get("points"),
                    "form": team.get("form"),
                })

        return {
            "competition": data.get("competition", {}).get("name"),
            "season": data.get("season", {}).get("startDate", "")[:4],
            "matchday": data.get("season", {}).get("currentMatchday"),
            "standings": standings
        }

    def get_team_position(self, team_name: str, competition: str = "PL") -> Optional[Dict]:
        """Get a specific team's current position."""
        standings = self.get_standings(competition)

        # Fuzzy match team name
        team_lower = team_name.lower()
        for team in standings["standings"]:
            if team_lower in team["team"].lower():
                return team
        return None

    def get_matches(self, competition: str = "PL",
                    status: str = None,
                    matchday: int = None,
                    date_from: str = None,
                    date_to: str = None) -> List[Dict]:
        """
        Get matches for a competition.

        Args:
            competition: Competition code
            status: SCHEDULED, LIVE, IN_PLAY, PAUSED, FINISHED, POSTPONED, etc.
            matchday: Specific matchday number
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
        """
        params = []
        if status:
            params.append(f"status={status}")
        if matchday:
            params.append(f"matchday={matchday}")
        if date_from:
            params.append(f"dateFrom={date_from}")
        if date_to:
            params.append(f"dateTo={date_to}")

        query = f"?{'&'.join(params)}" if params else ""
        data = self._request(f"/competitions/{competition}/matches{query}")

        matches = []
        for match in data.get("matches", []):
            matches.append({
                "id": match.get("id"),
                "matchday": match.get("matchday"),
                "date": match.get("utcDate"),
                "status": match.get("status"),
                "home_team": match.get("homeTeam", {}).get("name"),
                "away_team": match.get("awayTeam", {}).get("name"),
                "home_score": match.get("score", {}).get("fullTime", {}).get("home"),
                "away_score": match.get("score", {}).get("fullTime", {}).get("away"),
                "winner": match.get("score", {}).get("winner"),
            })

        return matches

    def get_upcoming_fixtures(self, team_name: str = None,
                              days_ahead: int = 14) -> List[Dict]:
        """Get upcoming fixtures, optionally filtered by team."""
        today = datetime.now().strftime("%Y-%m-%d")
        future = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        matches = self.get_matches(
            status="SCHEDULED",
            date_from=today,
            date_to=future
        )

        if team_name:
            team_lower = team_name.lower()
            matches = [m for m in matches
                      if team_lower in m["home_team"].lower()
                      or team_lower in m["away_team"].lower()]

        return matches

    def get_recent_results(self, team_name: str = None,
                           days_back: int = 14) -> List[Dict]:
        """Get recent match results, optionally filtered by team."""
        today = datetime.now().strftime("%Y-%m-%d")
        past = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        matches = self.get_matches(
            status="FINISHED",
            date_from=past,
            date_to=today
        )

        if team_name:
            team_lower = team_name.lower()
            matches = [m for m in matches
                      if team_lower in m["home_team"].lower()
                      or team_lower in m["away_team"].lower()]

        return matches

    def get_team_context(self, team_name: str) -> Dict:
        """
        Get comprehensive context for a team.

        Returns position, form, recent results, upcoming fixtures.
        """
        position = self.get_team_position(team_name)
        recent = self.get_recent_results(team_name, days_back=30)[:5]
        upcoming = self.get_upcoming_fixtures(team_name, days_ahead=14)[:3]

        return {
            "team": team_name,
            "position": position,
            "recent_results": recent,
            "upcoming_fixtures": upcoming,
            "summary": self._generate_summary(team_name, position, recent, upcoming)
        }

    def _generate_summary(self, team_name: str, position: Dict,
                          recent: List, upcoming: List) -> str:
        """Generate natural language summary for fan persona."""
        parts = []

        if position:
            parts.append(
                f"{team_name} are {position['position']}{'st' if position['position']==1 else 'nd' if position['position']==2 else 'rd' if position['position']==3 else 'th'} "
                f"with {position['points']} points from {position['played']} games."
            )
            if position.get('form'):
                parts.append(f"Recent form: {position['form']}.")

        if recent:
            wins = sum(1 for m in recent if
                      (team_name.lower() in m['home_team'].lower() and m['winner'] == 'HOME_TEAM') or
                      (team_name.lower() in m['away_team'].lower() and m['winner'] == 'AWAY_TEAM'))
            parts.append(f"Won {wins} of last {len(recent)} matches.")

        if upcoming:
            next_match = upcoming[0]
            opponent = next_match['away_team'] if team_name.lower() in next_match['home_team'].lower() else next_match['home_team']
            venue = "home" if team_name.lower() in next_match['home_team'].lower() else "away"
            parts.append(f"Next: {opponent} ({venue}).")

        return " ".join(parts)


# Singleton instance
_api_instance = None

def get_football_api(token: str = None) -> FootballDataAPI:
    """Get the Football Data API singleton."""
    global _api_instance
    if _api_instance is None:
        _api_instance = FootballDataAPI(token)
    return _api_instance


# Quick test
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python football_api.py <API_TOKEN>")
        sys.exit(1)

    token = sys.argv[1]
    api = FootballDataAPI(token)

    print("=== Premier League Standings ===")
    standings = api.get_standings()
    print(f"Season: {standings['season']}, Matchday: {standings['matchday']}")
    for team in standings['standings'][:5]:
        print(f"  {team['position']}. {team['team']} - {team['points']} pts")

    print("\n=== Liverpool Context ===")
    context = api.get_team_context("Liverpool")
    print(context['summary'])
