"""
Live Football Data Provider for 4D Persona Architecture

Bridges Soccer-AI data sources (football_api.py, database.py) to the 4D
FootballDataProvider interface.

This provides GROUND TRUTH for:
- X (Emotional): Recent results -> computed mood
- Y (Relational): Injuries, transfers -> conversation context
- T (Temporal): Upcoming fixtures -> anticipation

The key insight: emotions are DERIVED from real data, not declared.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
import sys

# Local imports - handle both package and direct execution contexts
try:
    from backend.config import CLUB_DISPLAY_NAMES, CLUB_API_NAMES
except ImportError:
    from config import CLUB_DISPLAY_NAMES, CLUB_API_NAMES


class LiveFootballProvider:
    """
    Bridges Soccer-AI data sources to 4D persona architecture.

    Provides ground truth that makes Robert's emotions REAL:
    - Win 3-0 -> euphoric (computed, not declared)
    - Loss to rival -> devastated (rivalry boost applied)
    - Injury to key player -> concerned (topic for conversation)

    Usage:
        provider = LiveFootballProvider()
        ground_truth = provider.get_ground_truth("liverpool")
        match_result = provider.get_match_result_for_4d("liverpool")
    """

    def __init__(self, api_token: str = None):
        """
        Initialize with optional API token.

        Args:
            api_token: Football-data.org API token. If None, loads from file.
        """
        self._api = None
        self._api_token = api_token
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    @property
    def api(self):
        """Lazy-load API client."""
        if self._api is None:
            try:
                from backend.football_api import get_football_api
                self._api = get_football_api(self._api_token)
            except Exception as e:
                print(f"[4D] Warning: Could not initialize football API: {e}")
                self._api = None
        return self._api

    def get_ground_truth(self, club_id: str) -> Dict[str, Any]:
        """
        Get comprehensive ground truth for a club.

        This is the main method that provides all data needed for 4D computation:
        - recent_results: For X-axis (emotional dimension)
        - league_position: For X-axis context
        - upcoming_fixtures: For T-axis (anticipation) and conversation topics
        - injuries: For conversation topics (weaved naturally)
        - transfers: For conversation topics (weaved naturally)

        Args:
            club_id: Internal club identifier (e.g., "liverpool")

        Returns:
            Dict with all ground truth data
        """
        # Check cache
        cache_key = f"ground_truth_{club_id}"
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if datetime.now().timestamp() - cached_time < self._cache_ttl:
                return cached_data

        # Get display/API names
        team_name = CLUB_DISPLAY_NAMES.get(club_id, club_id.replace("_", " ").title())

        ground_truth = {
            "club_id": club_id,
            "team_name": team_name,
            "timestamp": datetime.now().isoformat(),
            "recent_results": [],
            "league_position": None,
            "upcoming_fixtures": [],
            "injuries": [],
            "transfers": [],
            "form_string": "",
            "mood_reason": ""
        }

        # Fetch from live API if available
        if self.api:
            try:
                # Recent results (last 5 matches) - PRIMARY for mood
                results = self.api.get_recent_results(team_name, days_back=60)[:5]
                ground_truth["recent_results"] = self._transform_results(results, team_name)

                # Compute form string (WWDLL etc)
                ground_truth["form_string"] = self._compute_form_string(
                    ground_truth["recent_results"]
                )

                # League position - for context
                position = self.api.get_team_position(team_name)
                ground_truth["league_position"] = position

                # Upcoming fixtures - for anticipation and topics
                upcoming = self.api.get_upcoming_fixtures(team_name, days_ahead=14)[:3]
                ground_truth["upcoming_fixtures"] = self._transform_fixtures(upcoming, team_name)

                # Compute mood reason
                ground_truth["mood_reason"] = self._compute_mood_reason(
                    ground_truth["recent_results"],
                    ground_truth["league_position"]
                )

            except Exception as e:
                print(f"[4D] API fetch failed for {club_id}: {e}")
                # Will fall back to database

        # Fallback/supplement with database
        if not ground_truth["recent_results"]:
            ground_truth["recent_results"] = self._get_db_results(club_id)
            ground_truth["form_string"] = self._compute_form_string(
                ground_truth["recent_results"]
            )

        # Get injuries and transfers from database (always)
        ground_truth["injuries"] = self._get_injuries(club_id)
        ground_truth["transfers"] = self._get_transfers(club_id)

        # Cache the result
        self._cache[cache_key] = (datetime.now().timestamp(), ground_truth)

        return ground_truth

    def get_match_result_for_4d(self, club_id: str) -> Dict[str, Any]:
        """
        Get the most recent match result in 4D format.

        This is what PersonaEngine.compute_position() expects in the
        match_result parameter for emotional dimension computation.

        Returns:
            Dict with: result, opponent, score, goal_difference, is_rivalry
        """
        ground_truth = self.get_ground_truth(club_id)

        if not ground_truth.get("recent_results"):
            return {
                "result": "neutral",
                "opponent": "unknown",
                "score": {"for": 0, "against": 0},
                "goal_difference": 0,
                "is_rivalry": False
            }

        latest = ground_truth["recent_results"][0]

        # Check if it was a rivalry match
        is_rivalry = self._check_rivalry(club_id, latest.get("opponent", ""))

        return {
            "result": latest.get("result", "neutral"),
            "opponent": latest.get("opponent", "unknown"),
            "score": latest.get("score", {"for": 0, "against": 0}),
            "goal_difference": latest.get("goal_difference", 0),
            "is_rivalry": is_rivalry,
            "venue": latest.get("venue", "unknown"),
            "date": latest.get("date")
        }

    def get_conversation_topics(self, club_id: str) -> List[Dict[str, str]]:
        """
        Get conversation topics to weave naturally.

        User Requirement: Option C - mention injuries/transfers/fixtures
        when contextually relevant, not forced.

        Returns:
            List of topic dicts with type and content
        """
        ground_truth = self.get_ground_truth(club_id)
        topics = []

        # Next fixture - high relevance
        if ground_truth.get("upcoming_fixtures"):
            next_match = ground_truth["upcoming_fixtures"][0]
            topics.append({
                "type": "fixture",
                "priority": "high",
                "content": f"Next match: {next_match.get('opponent', 'TBD')} ({next_match.get('venue', 'TBD')})",
                "raw": next_match
            })

        # Key injuries - medium relevance
        injuries = ground_truth.get("injuries", [])
        if injuries:
            key_injuries = [i for i in injuries if i.get("severity") in ["major", "long-term"]][:2]
            if key_injuries:
                names = [i.get("player", "Unknown") for i in key_injuries]
                topics.append({
                    "type": "injury",
                    "priority": "medium",
                    "content": f"Injuries: {', '.join(names)}",
                    "raw": key_injuries
                })

        # Recent transfers - lower relevance
        transfers = ground_truth.get("transfers", [])
        if transfers:
            recent = [t for t in transfers if t.get("status") == "completed"][:2]
            if recent:
                topics.append({
                    "type": "transfer",
                    "priority": "low",
                    "content": "Recent transfer activity",
                    "raw": recent
                })

        return topics

    def _transform_results(self, api_results: List[Dict], team_name: str) -> List[Dict]:
        """Transform API match results to 4D format."""
        transformed = []
        team_lower = team_name.lower()

        for match in api_results:
            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")

            is_home = team_lower in home_team.lower()

            home_score = match.get("home_score") or 0
            away_score = match.get("away_score") or 0

            if is_home:
                goals_for = home_score
                goals_against = away_score
                opponent = away_team
            else:
                goals_for = away_score
                goals_against = home_score
                opponent = home_team

            # Determine result
            if goals_for > goals_against:
                result = "win"
            elif goals_for < goals_against:
                result = "loss"
            else:
                result = "draw"

            transformed.append({
                "date": match.get("date"),
                "opponent": opponent,
                "result": result,
                "score": {"for": goals_for, "against": goals_against},
                "goal_difference": goals_for - goals_against,
                "venue": "home" if is_home else "away"
            })

        return transformed

    def _transform_fixtures(self, api_fixtures: List[Dict], team_name: str) -> List[Dict]:
        """Transform API fixtures to 4D format."""
        transformed = []
        team_lower = team_name.lower()

        for match in api_fixtures:
            home_team = match.get("home_team", "")
            away_team = match.get("away_team", "")

            is_home = team_lower in home_team.lower()
            opponent = away_team if is_home else home_team

            transformed.append({
                "date": match.get("date"),
                "opponent": opponent,
                "venue": "home" if is_home else "away",
                "matchday": match.get("matchday")
            })

        return transformed

    def _compute_form_string(self, results: List[Dict]) -> str:
        """Compute form string like 'WWDLL' from results."""
        form = []
        for r in results[:5]:
            if r.get("result") == "win":
                form.append("W")
            elif r.get("result") == "loss":
                form.append("L")
            else:
                form.append("D")
        return "".join(form)

    def _compute_mood_reason(self, results: List[Dict], position: Optional[Dict]) -> str:
        """Generate natural language reason for current mood."""
        if not results:
            return "No recent matches"

        parts = []

        # Recent form
        wins = sum(1 for r in results if r.get("result") == "win")
        losses = sum(1 for r in results if r.get("result") == "loss")

        if wins >= 4:
            parts.append(f"Flying! {wins} wins from last {len(results)}")
        elif wins >= 3:
            parts.append(f"Good form - {wins} wins recently")
        elif losses >= 4:
            parts.append(f"Nightmare run - {losses} losses from {len(results)}")
        elif losses >= 3:
            parts.append(f"Poor form - {losses} losses recently")
        else:
            parts.append(f"Mixed results - {wins}W {losses}L from {len(results)}")

        # Latest result
        latest = results[0]
        if latest.get("result") == "win":
            gd = latest.get("goal_difference", 0)
            if gd >= 3:
                parts.append(f"Thumped {latest.get('opponent')} {gd} goals")
            else:
                parts.append(f"Beat {latest.get('opponent')}")
        elif latest.get("result") == "loss":
            parts.append(f"Lost to {latest.get('opponent')}")

        # League position
        if position:
            pos = position.get("position", 0)
            if pos <= 4:
                parts.append(f"Sitting {pos}{'st' if pos==1 else 'nd' if pos==2 else 'rd' if pos==3 else 'th'} - Champions League spot")
            elif pos >= 18:
                parts.append(f"In the drop zone at {pos}th")

        return ". ".join(parts)

    def _check_rivalry(self, club_id: str, opponent: str) -> bool:
        """Check if opponent is a rival."""
        # Major rivalries - will be enhanced with KG data
        RIVALRIES = {
            "liverpool": ["everton", "manchester_united", "manchester_city"],
            "manchester_united": ["liverpool", "manchester_city", "leeds"],
            "manchester_city": ["manchester_united", "liverpool"],
            "arsenal": ["tottenham", "chelsea"],
            "tottenham": ["arsenal", "chelsea", "west_ham"],
            "chelsea": ["arsenal", "tottenham", "fulham"],
            "everton": ["liverpool"],
            "west_ham": ["tottenham", "millwall"],
            "newcastle": ["sunderland"],
            "aston_villa": ["birmingham", "wolves"],
            "wolves": ["aston_villa", "west_brom"]
        }

        rivals = RIVALRIES.get(club_id, [])
        opponent_lower = opponent.lower()

        for rival in rivals:
            if rival in opponent_lower or rival.replace("_", " ") in opponent_lower:
                return True

        return False

    def _get_db_results(self, club_id: str) -> List[Dict]:
        """Fallback: get results from unified database match_history."""
        import sqlite3
        from pathlib import Path

        # Map club_id to match_history team name format
        team_name_mapping = {
            "manchester_united": "Man United",
            "manchester_city": "Man City",
            "liverpool": "Liverpool",
            "arsenal": "Arsenal",
            "chelsea": "Chelsea",
            "tottenham": "Tottenham",
            "everton": "Everton",
            "newcastle": "Newcastle",
            "west_ham": "West Ham",
            "aston_villa": "Aston Villa",
            "brighton": "Brighton",
            "crystal_palace": "Crystal Palace",
            "bournemouth": "Bournemouth",
            "brentford": "Brentford",
            "fulham": "Fulham",
            "wolves": "Wolves",
            "nottingham_forest": "Nott'm Forest",
            "leicester": "Leicester",
            "ipswich": "Ipswich",
            "southampton": "Southampton",
        }

        team_name = team_name_mapping.get(club_id, club_id.replace("_", " ").title())

        try:
            # Find unified KG database
            backend_dir = Path(__file__).parent
            db_path = backend_dir / "unified_soccer_ai_kg.db"

            if not db_path.exists():
                return []

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get last 5 matches
            cursor.execute("""
                SELECT match_date, home_team, away_team, ft_home, ft_away, ft_result
                FROM match_history
                WHERE home_team LIKE ? OR away_team LIKE ?
                ORDER BY match_date DESC
                LIMIT 5
            """, (f"%{team_name}%", f"%{team_name}%"))

            rows = cursor.fetchall()
            conn.close()

            results = []
            for row in rows:
                match_date, home, away, ft_home, ft_away, ft_result = row

                is_home = team_name.lower() in home.lower()

                if is_home:
                    goals_for = ft_home or 0
                    goals_against = ft_away or 0
                    opponent = away
                    venue = "home"
                else:
                    goals_for = ft_away or 0
                    goals_against = ft_home or 0
                    opponent = home
                    venue = "away"

                # Determine result
                if goals_for > goals_against:
                    result = "win"
                elif goals_for < goals_against:
                    result = "loss"
                else:
                    result = "draw"

                results.append({
                    "date": match_date,
                    "opponent": opponent,
                    "result": result,
                    "score": {"for": goals_for, "against": goals_against},
                    "goal_difference": goals_for - goals_against,
                    "venue": venue
                })

            return results

        except Exception as e:
            print(f"[4D] DB fallback failed for {club_id}: {e}")
            return []

    def _get_injuries(self, club_id: str) -> List[Dict]:
        """Get current injuries for conversation topics."""
        try:
            from backend import database
            # Get team_id from club_id mapping
            # Query injuries table
            return []
        except Exception:
            return []

    def _get_transfers(self, club_id: str) -> List[Dict]:
        """Get recent transfers for conversation topics."""
        try:
            from backend import database
            # Get team_id from club_id mapping
            # Query transfers table
            return []
        except Exception:
            return []


# Singleton instance
_provider_instance = None

def get_live_football_provider(api_token: str = None) -> LiveFootballProvider:
    """Get the LiveFootballProvider singleton."""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = LiveFootballProvider(api_token)
    return _provider_instance


# Quick test
if __name__ == "__main__":
    print("=== Live Football Provider Test ===")
    provider = LiveFootballProvider()

    # Test ground truth
    gt = provider.get_ground_truth("liverpool")
    print(f"\nGround Truth for Liverpool:")
    print(f"  Timestamp: {gt['timestamp']}")
    print(f"  Recent Results: {len(gt['recent_results'])} matches")
    print(f"  Form: {gt['form_string']}")
    print(f"  Mood Reason: {gt['mood_reason']}")

    # Test match result for 4D
    match = provider.get_match_result_for_4d("liverpool")
    print(f"\nLatest Match (4D format):")
    print(f"  Result: {match['result']}")
    print(f"  Opponent: {match['opponent']}")
    print(f"  Score: {match['score']}")
    print(f"  Is Rivalry: {match['is_rivalry']}")

    # Test conversation topics
    topics = provider.get_conversation_topics("liverpool")
    print(f"\nConversation Topics: {len(topics)}")
    for t in topics:
        print(f"  [{t['priority']}] {t['type']}: {t['content']}")
