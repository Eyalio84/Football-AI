"""
Team Power Rating System (ELO-Style)
=====================================
Part of Soccer Predictor v3.0 - Winner Prediction

Provides absolute team strength ratings (0-100 scale) that enable
winner prediction rather than just upset detection.

Based on ELO rating system with Premier League-specific adjustments.

Reference: WHAT_IS_NEEDED_WINNER_PREDICTION.ctx
"""

import json
import math
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional


# === CONFIGURATION ===

# Starting ELO for new teams (average = 1500)
BASE_ELO = 1500

# K-factor: How much ratings change per match
# Higher = more reactive to recent results
# Lower = more stable, historical-weighted
K_FACTOR_DEFAULT = 32
K_FACTOR_BIG_MATCH = 40  # Top 6 vs Top 6
K_FACTOR_EARLY_SEASON = 48  # First 5 matches (more volatile)

# Home advantage in ELO points
HOME_ADVANTAGE = 65  # ~65 ELO points = ~60% expected win rate at home

# Draw adjustment (football has more draws than chess)
DRAW_FACTOR = 0.5  # Draws count as 0.5 win

# ELO to 0-100 scale conversion
ELO_MIN = 1200  # Maps to 0
ELO_MAX = 1800  # Maps to 100


# === DATA STRUCTURES ===

@dataclass
class TeamRating:
    """Single team's rating data."""
    team_id: str
    team_name: str
    elo: float = BASE_ELO
    matches_played: int = 0
    last_updated: str = ""
    form_last_5: list = field(default_factory=list)  # W/D/L for last 5
    home_elo: float = BASE_ELO  # Home-specific rating
    away_elo: float = BASE_ELO  # Away-specific rating

    @property
    def power_rating(self) -> float:
        """Convert ELO to 0-100 scale."""
        normalized = (self.elo - ELO_MIN) / (ELO_MAX - ELO_MIN)
        return max(0, min(100, normalized * 100))

    @property
    def form_score(self) -> float:
        """Calculate form from last 5 matches (0-1 scale)."""
        if not self.form_last_5:
            return 0.5  # Neutral if no data
        points = sum(1 if r == 'W' else 0.5 if r == 'D' else 0 for r in self.form_last_5)
        return points / len(self.form_last_5)

    def to_dict(self) -> dict:
        """Serialize for JSON storage."""
        d = asdict(self)
        d['power_rating'] = self.power_rating
        d['form_score'] = self.form_score
        return d


@dataclass
class MatchResult:
    """Single match result for rating updates."""
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    date: str
    is_big_match: bool = False
    matchweek: int = 0


# === CORE ELO FUNCTIONS ===

def expected_score(rating_a: float, rating_b: float) -> float:
    """
    Calculate expected score for team A against team B.

    Uses standard ELO formula:
    E_A = 1 / (1 + 10^((R_B - R_A) / 400))

    Returns probability 0-1 that team A wins.
    """
    return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))


def get_k_factor(match: MatchResult, team_matches: int) -> float:
    """
    Determine K-factor based on match importance and team experience.

    - Early season: Higher K (more reactive)
    - Big matches: Higher K (more impactful)
    - Default: Standard K
    """
    if team_matches < 5:
        return K_FACTOR_EARLY_SEASON
    if match.is_big_match:
        return K_FACTOR_BIG_MATCH
    return K_FACTOR_DEFAULT


def match_outcome(home_score: int, away_score: int) -> tuple[float, float]:
    """
    Convert match score to ELO outcome values.

    Returns (home_outcome, away_outcome) where:
    - Win = 1.0
    - Draw = 0.5
    - Loss = 0.0
    """
    if home_score > away_score:
        return (1.0, 0.0)
    elif home_score < away_score:
        return (0.0, 1.0)
    else:
        return (DRAW_FACTOR, DRAW_FACTOR)


def update_elo(
    current_elo: float,
    expected: float,
    actual: float,
    k_factor: float
) -> float:
    """
    Standard ELO update formula.

    New_Rating = Old_Rating + K * (Actual - Expected)
    """
    return current_elo + k_factor * (actual - expected)


# === RATING SYSTEM CLASS ===

class TeamRatingSystem:
    """
    Manages ratings for all teams.

    Usage:
        system = TeamRatingSystem()
        system.initialize_premier_league_2024()
        system.process_match(match_result)
        rating = system.get_rating("arsenal")
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.ratings: dict[str, TeamRating] = {}
        self.match_history: list[dict] = []
        self.db_path = db_path or Path(__file__).parent / "team_ratings.json"

    def initialize_team(self, team_id: str, team_name: str, initial_elo: float = BASE_ELO):
        """Add a new team with initial rating."""
        self.ratings[team_id] = TeamRating(
            team_id=team_id,
            team_name=team_name,
            elo=initial_elo,
            home_elo=initial_elo,
            away_elo=initial_elo,
            last_updated=datetime.now().isoformat()
        )

    def initialize_premier_league_2024(self):
        """
        Initialize all 20 Premier League teams with estimated starting ELOs.

        Starting ELOs based on 2023-24 finish + historical strength:
        - Man City: 1750 (dominant champions)
        - Arsenal: 1700 (title challengers)
        - Liverpool: 1680 (top 4 regulars)
        ...down to...
        - Promoted teams: 1400 (new to league)
        """
        teams = {
            # Top 6
            "manchester_city": ("Manchester City", 1750),
            "arsenal": ("Arsenal", 1700),
            "liverpool": ("Liverpool", 1680),
            "chelsea": ("Chelsea", 1600),
            "tottenham": ("Tottenham", 1580),
            "manchester_united": ("Manchester United", 1560),

            # Upper mid-table
            "newcastle": ("Newcastle", 1550),
            "aston_villa": ("Aston Villa", 1540),
            "brighton": ("Brighton", 1520),
            "west_ham": ("West Ham", 1500),

            # Mid-table
            "brentford": ("Brentford", 1480),
            "fulham": ("Fulham", 1470),
            "crystal_palace": ("Crystal Palace", 1460),
            "wolves": ("Wolves", 1450),
            "bournemouth": ("Bournemouth", 1440),

            # Lower table
            "nottingham_forest": ("Nottingham Forest", 1430),
            "everton": ("Everton", 1420),

            # Promoted / Recently promoted
            "leicester": ("Leicester City", 1410),
            "ipswich": ("Ipswich Town", 1380),
            "southampton": ("Southampton", 1380),
        }

        for team_id, (name, elo) in teams.items():
            self.initialize_team(team_id, name, elo)

        return len(self.ratings)

    def get_rating(self, team_id: str) -> Optional[TeamRating]:
        """Get current rating for a team."""
        return self.ratings.get(team_id)

    def get_power_rating(self, team_id: str) -> float:
        """Get 0-100 power rating for a team."""
        rating = self.get_rating(team_id)
        return rating.power_rating if rating else 50.0

    def process_match(self, match: MatchResult) -> dict:
        """
        Process a match result and update both teams' ratings.

        Returns dict with rating changes.
        """
        home = self.ratings.get(match.home_team)
        away = self.ratings.get(match.away_team)

        if not home or not away:
            return {"error": f"Unknown team: {match.home_team} or {match.away_team}"}

        # Calculate expected scores (with home advantage)
        home_expected = expected_score(home.elo + HOME_ADVANTAGE, away.elo)
        away_expected = 1 - home_expected

        # Get actual outcomes
        home_actual, away_actual = match_outcome(match.home_score, match.away_score)

        # Determine K-factors
        k_home = get_k_factor(match, home.matches_played)
        k_away = get_k_factor(match, away.matches_played)

        # Store old ratings
        old_home_elo = home.elo
        old_away_elo = away.elo

        # Update ratings
        home.elo = update_elo(home.elo, home_expected, home_actual, k_home)
        away.elo = update_elo(away.elo, away_expected, away_actual, k_away)

        # Update home/away specific ratings
        home.home_elo = update_elo(home.home_elo, home_expected, home_actual, k_home)
        away.away_elo = update_elo(away.away_elo, away_expected, away_actual, k_away)

        # Update form
        home_result = 'W' if home_actual == 1 else 'D' if home_actual == 0.5 else 'L'
        away_result = 'W' if away_actual == 1 else 'D' if away_actual == 0.5 else 'L'

        home.form_last_5 = (home.form_last_5 + [home_result])[-5:]
        away.form_last_5 = (away.form_last_5 + [away_result])[-5:]

        # Update metadata
        home.matches_played += 1
        away.matches_played += 1
        home.last_updated = match.date
        away.last_updated = match.date

        # Record history
        result = {
            "match": f"{match.home_team} vs {match.away_team}",
            "score": f"{match.home_score}-{match.away_score}",
            "date": match.date,
            "home_elo_change": round(home.elo - old_home_elo, 1),
            "away_elo_change": round(away.elo - old_away_elo, 1),
            "home_new_elo": round(home.elo, 1),
            "away_new_elo": round(away.elo, 1),
            "expected_home_win": round(home_expected * 100, 1)
        }

        self.match_history.append(result)
        return result

    def predict_match(self, home_team: str, away_team: str) -> dict:
        """
        Predict match outcome probabilities.

        Returns three-way probability distribution:
        - home_win: probability home team wins
        - draw: probability of draw
        - away_win: probability away team wins
        """
        home = self.ratings.get(home_team)
        away = self.ratings.get(away_team)

        if not home or not away:
            return {"error": f"Unknown team: {home_team} or {away_team}"}

        # Use home-specific ELO for home team, away-specific for away
        home_effective = (home.elo + home.home_elo) / 2 + HOME_ADVANTAGE
        away_effective = (away.elo + away.away_elo) / 2

        # Base win probability
        home_win_base = expected_score(home_effective, away_effective)
        away_win_base = 1 - home_win_base

        # Extract draw probability (Premier League average ~25%)
        # Higher when teams are close in rating
        rating_diff = abs(home_effective - away_effective)
        draw_prob = 0.28 - (rating_diff / 1000)  # ~28% for equal teams, less for mismatches
        draw_prob = max(0.15, min(0.35, draw_prob))  # Clamp to 15-35%

        # Adjust win probabilities for draw
        home_win = home_win_base * (1 - draw_prob)
        away_win = away_win_base * (1 - draw_prob)

        # Normalize to ensure sum = 1
        total = home_win + draw_prob + away_win
        home_win /= total
        draw_prob /= total
        away_win /= total

        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_win": round(home_win * 100, 1),
            "draw": round(draw_prob * 100, 1),
            "away_win": round(away_win * 100, 1),
            "home_power": round(home.power_rating, 1),
            "away_power": round(away.power_rating, 1),
            "power_diff": round(home.power_rating - away.power_rating, 1),
            "home_form": home.form_last_5,
            "away_form": away.form_last_5,
            "prediction": (
                "home_win" if home_win > max(draw_prob, away_win) else
                "away_win" if away_win > max(draw_prob, home_win) else
                "draw"
            )
        }

    def get_rankings(self) -> list[dict]:
        """Get all teams ranked by power rating."""
        ranked = sorted(
            self.ratings.values(),
            key=lambda t: t.elo,
            reverse=True
        )
        return [
            {
                "rank": i + 1,
                "team": t.team_name,
                "team_id": t.team_id,
                "elo": round(t.elo, 1),
                "power_rating": round(t.power_rating, 1),
                "form": t.form_last_5,
                "matches": t.matches_played
            }
            for i, t in enumerate(ranked)
        ]

    def save(self):
        """Save ratings to JSON file."""
        data = {
            "last_updated": datetime.now().isoformat(),
            "ratings": {k: v.to_dict() for k, v in self.ratings.items()},
            "match_history": self.match_history[-100:]  # Keep last 100
        }
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self) -> bool:
        """Load ratings from JSON file."""
        if not self.db_path.exists():
            return False

        with open(self.db_path) as f:
            data = json.load(f)

        for team_id, rating_data in data.get("ratings", {}).items():
            self.ratings[team_id] = TeamRating(
                team_id=rating_data["team_id"],
                team_name=rating_data["team_name"],
                elo=rating_data["elo"],
                matches_played=rating_data["matches_played"],
                last_updated=rating_data["last_updated"],
                form_last_5=rating_data["form_last_5"],
                home_elo=rating_data.get("home_elo", rating_data["elo"]),
                away_elo=rating_data.get("away_elo", rating_data["elo"])
            )

        self.match_history = data.get("match_history", [])
        return True


# === DEMO / TEST ===

if __name__ == "__main__":
    print("=== Team Power Rating System Demo ===\n")

    # Initialize system
    system = TeamRatingSystem()
    count = system.initialize_premier_league_2024()
    print(f"Initialized {count} teams\n")

    # Show initial rankings
    print("Initial Power Rankings (Top 10):")
    print("-" * 50)
    for r in system.get_rankings()[:10]:
        print(f"{r['rank']:2}. {r['team']:20} ELO: {r['elo']:6.1f}  Power: {r['power_rating']:5.1f}")

    print("\n" + "=" * 50)
    print("Simulating some matches...\n")

    # Simulate a few matches
    matches = [
        MatchResult("manchester_city", "arsenal", 2, 1, "2024-09-15"),
        MatchResult("liverpool", "chelsea", 3, 0, "2024-09-16"),
        MatchResult("brighton", "manchester_united", 2, 1, "2024-09-17"),  # Upset!
        MatchResult("tottenham", "newcastle", 1, 1, "2024-09-18"),
    ]

    for match in matches:
        result = system.process_match(match)
        print(f"{result['match']}: {result['score']}")
        print(f"  Home ELO change: {result['home_elo_change']:+.1f} → {result['home_new_elo']}")
        print(f"  Away ELO change: {result['away_elo_change']:+.1f} → {result['away_new_elo']}")
        print(f"  Expected home win was: {result['expected_home_win']}%\n")

    print("=" * 50)
    print("Updated Power Rankings (Top 10):")
    print("-" * 50)
    for r in system.get_rankings()[:10]:
        form_str = ''.join(r['form']) if r['form'] else '-'
        print(f"{r['rank']:2}. {r['team']:20} ELO: {r['elo']:6.1f}  Power: {r['power_rating']:5.1f}  Form: {form_str}")

    print("\n" + "=" * 50)
    print("Match Prediction Example:")
    print("-" * 50)

    pred = system.predict_match("manchester_united", "aston_villa")
    print(f"\n{pred['home_team']} vs {pred['away_team']}")
    print(f"  Home Win: {pred['home_win']}%")
    print(f"  Draw:     {pred['draw']}%")
    print(f"  Away Win: {pred['away_win']}%")
    print(f"  Power Diff: {pred['power_diff']:+.1f}")
    print(f"  Prediction: {pred['prediction'].upper()}")

    # Save
    system.save()
    print(f"\nRatings saved to {system.db_path}")
