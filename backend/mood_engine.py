"""
Mood Engine for Soccer-AI Fan Personas

Determines fan emotional state based on:
- Live match results (win/loss/draw)
- Context (derby, table position, margin)
- Historical significance (revenge, records)

Modulates response tone, memory selection, and banter intensity.
"""

import json
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Import our data layers (handle both package and direct execution)
try:
    from backend.football_api import get_football_api
    from backend.match_insights import get_match_insights
    from backend.kg_integration import get_kg
except ImportError:
    from football_api import get_football_api
    from match_insights import get_match_insights
    from kg_integration import get_kg


class Mood(Enum):
    """Fan mood states from elated to devastated."""
    ELATED = 5      # Derby win, upset victory, title-winning moment
    HAPPY = 4       # Normal win, good performance
    CONTENT = 3     # Draw against tough opponent, acceptable result
    NEUTRAL = 2     # No recent game, mid-table irrelevance
    FRUSTRATED = 1  # Close loss, controversial decision, VAR
    DEVASTATED = 0  # Heavy loss, derby defeat, relegation confirmed


class MoodEngine:
    """
    Calculates and applies fan mood based on live results and context.
    """

    # Rivalry pairs (both directions checked)
    RIVALRIES = {
        "Liverpool": ["Manchester United", "Everton", "Manchester City"],
        "Manchester United": ["Liverpool", "Manchester City", "Leeds United"],
        "Manchester City": ["Manchester United", "Liverpool"],
        "Arsenal": ["Tottenham Hotspur", "Chelsea", "Manchester United"],
        "Tottenham Hotspur": ["Arsenal", "Chelsea", "West Ham United"],
        "Chelsea": ["Arsenal", "Tottenham Hotspur", "Fulham"],
        "Everton": ["Liverpool"],
        "Newcastle United": ["Sunderland", "Middlesbrough"],
        "West Ham United": ["Tottenham Hotspur", "Millwall"],
        "Aston Villa": ["Birmingham City", "Wolverhampton Wanderers"],
        "Leeds United": ["Manchester United", "Chelsea"],
        "Brighton": ["Crystal Palace"],
        "Crystal Palace": ["Brighton"],
        "Nottingham Forest": ["Derby County", "Leicester City"],
        "Leicester City": ["Nottingham Forest"],
    }

    # Mood response templates
    MOOD_TEMPLATES = {
        Mood.ELATED: {
            "openers": [
                "MATE! Did you SEE that?!",
                "I'm still buzzing!",
                "GET IN! Absolutely unreal!",
                "Best day of the season, hands down!",
                "I might cry happy tears!",
            ],
            "tone": "ecstatic, exclamatory, bragging",
            "memory_bias": "positive",  # Surface triumphant memories
            "banter_level": "maximum",
        },
        Mood.HAPPY: {
            "openers": [
                "Brilliant result that.",
                "The lads showed up today.",
                "Can't complain with that performance.",
                "That's what we needed.",
                "Proper professional job.",
            ],
            "tone": "positive, satisfied, confident",
            "memory_bias": "positive",
            "banter_level": "moderate",
        },
        Mood.CONTENT: {
            "openers": [
                "Fair enough, I'll take it.",
                "A point's a point.",
                "Not our best but not bad either.",
                "Could've been worse.",
                "Solid, if unspectacular.",
            ],
            "tone": "measured, pragmatic, accepting",
            "memory_bias": "neutral",
            "banter_level": "low",
        },
        Mood.NEUTRAL: {
            "openers": [
                "Alright?",
                "What's on your mind?",
                "Ready for the weekend?",
                "How's it going?",
                "What do you want to chat about?",
            ],
            "tone": "conversational, open, balanced",
            "memory_bias": "neutral",
            "banter_level": "moderate",
        },
        Mood.FRUSTRATED: {
            "openers": [
                "Don't even get me started...",
                "I'm fuming mate.",
                "That was painful to watch.",
                "How did we let that happen?",
                "The ref was shocking, but still...",
            ],
            "tone": "annoyed, critical, searching for answers",
            "memory_bias": "negative",  # Surface similar past frustrations
            "banter_level": "defensive",
        },
        Mood.DEVASTATED: {
            "openers": [
                "I can't even talk about it.",
                "Embarrassing. Absolutely embarrassing.",
                "That's the worst I've felt in years.",
                "We got absolutely humiliated.",
                "I need a drink after that.",
            ],
            "tone": "dejected, hurt, questioning loyalty",
            "memory_bias": "seeking_comfort",  # Surface comeback stories
            "banter_level": "none",
        },
    }

    def __init__(self):
        self.api = get_football_api()
        self.insights = get_match_insights()
        self.kg = get_kg()
        self._mood_cache = {}

    def _is_rival(self, team1: str, team2: str) -> bool:
        """Check if two teams are rivals."""
        team1_rivals = self.RIVALRIES.get(team1, [])
        team2_rivals = self.RIVALRIES.get(team2, [])

        # Normalize names for comparison
        t1_lower = team1.lower()
        t2_lower = team2.lower()

        for rival in team1_rivals:
            if rival.lower() in t2_lower or t2_lower in rival.lower():
                return True
        for rival in team2_rivals:
            if rival.lower() in t1_lower or t1_lower in rival.lower():
                return True
        return False

    def _calculate_result_impact(self, team: str, match: Dict) -> Tuple[str, int, bool]:
        """
        Determine if team won/lost/drew and by how much.

        Returns: (result: 'W'/'D'/'L', margin: int, is_derby: bool)
        """
        home = match.get("home_team", "")
        away = match.get("away_team", "")
        home_score = match.get("home_score")
        away_score = match.get("away_score")

        if home_score is None or away_score is None:
            return None, 0, False

        team_lower = team.lower()
        is_home = team_lower in home.lower()
        is_away = team_lower in away.lower()

        if not is_home and not is_away:
            return None, 0, False

        opponent = away if is_home else home
        is_derby = self._is_rival(team, opponent)

        if is_home:
            our_goals, their_goals = home_score, away_score
        else:
            our_goals, their_goals = away_score, home_score

        margin = our_goals - their_goals

        if margin > 0:
            return 'W', margin, is_derby
        elif margin < 0:
            return 'L', abs(margin), is_derby
        else:
            return 'D', 0, is_derby

    def _get_table_context(self, team: str) -> Dict:
        """Get current table position context."""
        try:
            position = self.api.get_team_position(team)
            if position:
                return {
                    "position": position.get("position"),
                    "points": position.get("points"),
                    "in_title_race": position.get("position", 99) <= 4,
                    "in_relegation": position.get("position", 0) >= 18,
                }
        except:
            pass
        return {"position": None, "in_title_race": False, "in_relegation": False}

    def calculate_mood(self, team: str) -> Tuple[Mood, Dict]:
        """
        Calculate current mood for a team's fan based on recent results.

        Returns: (mood: Mood, context: Dict with details)
        """
        context = {
            "team": team,
            "last_match": None,
            "result": None,
            "margin": 0,
            "is_derby": False,
            "table_context": {},
            "mood_reason": "",
        }

        # Get recent results
        try:
            recent = self.api.get_recent_results(team, days_back=7)
        except:
            recent = []

        if not recent:
            context["mood_reason"] = "No recent matches"
            return Mood.NEUTRAL, context

        # Most recent match
        last_match = recent[0]
        context["last_match"] = last_match

        result, margin, is_derby = self._calculate_result_impact(team, last_match)
        context["result"] = result
        context["margin"] = margin
        context["is_derby"] = is_derby

        if result is None:
            context["mood_reason"] = "Match not yet played or data unavailable"
            return Mood.NEUTRAL, context

        # Get table context for additional weight
        table_ctx = self._get_table_context(team)
        context["table_context"] = table_ctx

        # Calculate mood based on result + context
        mood = self._result_to_mood(result, margin, is_derby, table_ctx)
        context["mood_reason"] = self._generate_mood_reason(result, margin, is_derby, table_ctx)

        return mood, context

    def _result_to_mood(self, result: str, margin: int, is_derby: bool,
                        table_ctx: Dict) -> Mood:
        """Convert result to mood with context modifiers."""

        if result == 'W':
            if is_derby:
                return Mood.ELATED  # Derby wins are always elated
            elif margin >= 4:
                return Mood.ELATED  # Thrashing
            elif margin >= 2:
                return Mood.HAPPY   # Comfortable win
            else:
                return Mood.HAPPY   # Any win is good

        elif result == 'D':
            if is_derby:
                return Mood.FRUSTRATED  # Derby draws are frustrating
            elif table_ctx.get("in_relegation"):
                return Mood.CONTENT     # Point is valuable in relegation
            else:
                return Mood.CONTENT     # Normal draw

        elif result == 'L':
            if is_derby:
                return Mood.DEVASTATED  # Derby losses are devastating
            elif margin >= 4:
                return Mood.DEVASTATED  # Thrashing
            elif margin >= 2:
                return Mood.FRUSTRATED  # Clear loss
            else:
                return Mood.FRUSTRATED  # Narrow loss still hurts

        return Mood.NEUTRAL

    def _generate_mood_reason(self, result: str, margin: int, is_derby: bool,
                              table_ctx: Dict) -> str:
        """Generate human-readable mood reason."""
        parts = []

        if result == 'W':
            if is_derby:
                parts.append("DERBY WIN!")
            if margin >= 4:
                parts.append(f"Thrashing ({margin}-goal margin)")
            elif margin >= 2:
                parts.append(f"Comfortable win ({margin} goals)")
            else:
                parts.append("Narrow but deserved victory")

        elif result == 'D':
            if is_derby:
                parts.append("Derby draw - mixed feelings")
            else:
                parts.append("Shared the points")

        elif result == 'L':
            if is_derby:
                parts.append("DERBY LOSS. Pain.")
            if margin >= 4:
                parts.append(f"Humiliated (lost by {margin})")
            elif margin >= 2:
                parts.append(f"Clear defeat ({margin} goals)")
            else:
                parts.append("Narrow loss - so close")

        if table_ctx.get("in_title_race"):
            parts.append("Title race implications")
        if table_ctx.get("in_relegation"):
            parts.append("Relegation battle context")

        return " | ".join(parts) if parts else "Standard result"

    def get_mood_template(self, mood: Mood) -> Dict:
        """Get response template for a mood."""
        return self.MOOD_TEMPLATES.get(mood, self.MOOD_TEMPLATES[Mood.NEUTRAL])

    def get_contextual_memories(self, team: str, mood: Mood,
                                opponent: str = None) -> List[str]:
        """
        Get relevant memories based on mood.

        ELATED/HAPPY: Surface triumphant memories
        FRUSTRATED: Surface similar frustrations (we've been here before)
        DEVASTATED: Surface comeback stories (we recovered from worse)
        """
        memories = []

        if opponent:
            # Get H2H context
            h2h = self.insights.head_to_head(team, opponent)

            if mood in [Mood.ELATED, Mood.HAPPY]:
                # Surface biggest wins
                if h2h.get("team1_biggest_win"):
                    bw = h2h["team1_biggest_win"]
                    memories.append(
                        f"Remember {bw['date'][:4]}? We absolutely destroyed them {bw['score']}!"
                    )
            elif mood == Mood.DEVASTATED:
                # Surface comeback stories
                comebacks = self.insights.find_comebacks(team, limit=3)
                if comebacks:
                    c = comebacks[0]
                    memories.append(
                        f"We've come back from worse. Remember {c['date'][:4]}? "
                        f"Down {c['ht_score']} at half-time, won {c['ft_score']}!"
                    )

        # Get ELO context
        elo = self.insights.get_elo_trajectory(team)
        if elo.get("peak"):
            if mood in [Mood.FRUSTRATED, Mood.DEVASTATED]:
                memories.append(
                    f"We'll get back to our best. Peak was {elo['peak']['elo']:.0f} ELO "
                    f"({elo['peak']['date'][:4]}). We've been champions before."
                )

        return memories

    def generate_mood_aware_opening(self, team: str,
                                     opponent: str = None) -> Dict:
        """
        Generate a complete mood-aware opening for a conversation.

        Returns dict with:
        - mood: The calculated mood
        - opening: Suggested opening line
        - tone: Tone guidance for the rest of response
        - memories: Relevant memories to potentially include
        - banter_level: How much to engage in rivalry banter
        """
        mood, context = self.calculate_mood(team)
        template = self.get_mood_template(mood)

        # Pick an opener
        import random
        opener = random.choice(template["openers"])

        # Get contextual memories
        memories = self.get_contextual_memories(team, mood, opponent)

        return {
            "mood": mood.name,
            "mood_value": mood.value,
            "opening": opener,
            "tone": template["tone"],
            "banter_level": template["banter_level"],
            "memory_bias": template["memory_bias"],
            "memories": memories,
            "context": context,
        }


# Singleton
_mood_engine = None

def get_mood_engine() -> MoodEngine:
    global _mood_engine
    if _mood_engine is None:
        _mood_engine = MoodEngine()
    return _mood_engine


# Quick test
if __name__ == "__main__":
    engine = get_mood_engine()

    print("=" * 60)
    print("MOOD ENGINE TEST")
    print("=" * 60)

    test_teams = ["Liverpool", "Arsenal", "Manchester United", "Everton"]

    for team in test_teams:
        print(f"\n🎭 {team.upper()}")
        result = engine.generate_mood_aware_opening(team)
        print(f"   Mood: {result['mood']} ({result['mood_value']}/5)")
        print(f"   Opening: \"{result['opening']}\"")
        print(f"   Tone: {result['tone']}")
        print(f"   Banter: {result['banter_level']}")
        if result['memories']:
            print(f"   Memory: {result['memories'][0][:60]}...")
        if result['context'].get('mood_reason'):
            print(f"   Reason: {result['context']['mood_reason']}")
