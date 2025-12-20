"""
Poisson Goal Predictor: The Third Lens
======================================

Instead of predicting winner directly, this model:
1. Predicts expected goals (xG) for each team
2. Uses Poisson distribution to calculate scoreline probabilities
3. Derives win/draw/loss from goal probabilities

Mathematical Foundation:
- P(X goals) = (λ^X × e^-λ) / X!
- P(scoreline h-a) = P(home=h) × P(away=a)
- P(Home Win) = Σ P(h > a for all h,a)
- P(Draw) = Σ P(h = a for all h,a)
- P(Away Win) = Σ P(a > h for all h,a)

This approach captures the inherent randomness of football through
the Poisson distribution, which naturally produces draw probabilities.
"""

import math
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

DB_PATH = Path(__file__).parent.parent / "unified_soccer_ai_kg.db"


@dataclass
class PoissonPrediction:
    """Prediction based on Poisson goal model."""
    home_team: str
    away_team: str

    # Expected goals
    home_xg: float
    away_xg: float

    # Win/Draw/Loss probabilities
    home_win_prob: float
    draw_prob: float
    away_win_prob: float

    # Prediction
    prediction: str
    confidence: str

    # Most likely scorelines
    likely_scores: List[Tuple[str, float]]

    # Components
    home_attack: float
    home_defense: float
    away_attack: float
    away_defense: float


def poisson_probability(k: int, lambda_: float) -> float:
    """
    Calculate Poisson probability P(X = k) given λ.

    P(X = k) = (λ^k × e^-λ) / k!
    """
    if lambda_ <= 0:
        return 1.0 if k == 0 else 0.0
    return (math.pow(lambda_, k) * math.exp(-lambda_)) / math.factorial(k)


def calculate_match_probabilities(home_xg: float, away_xg: float, max_goals: int = 8) -> Tuple[float, float, float, List]:
    """
    Calculate match outcome probabilities using Poisson distribution.

    Returns: (home_win_prob, draw_prob, away_win_prob, likely_scores)
    """
    home_win = 0.0
    draw = 0.0
    away_win = 0.0
    scorelines = []

    for h in range(max_goals + 1):
        p_home_h = poisson_probability(h, home_xg)
        for a in range(max_goals + 1):
            p_away_a = poisson_probability(a, away_xg)
            prob = p_home_h * p_away_a

            scorelines.append((f"{h}-{a}", prob))

            if h > a:
                home_win += prob
            elif h == a:
                draw += prob
            else:
                away_win += prob

    # Sort scorelines by probability
    scorelines.sort(key=lambda x: x[1], reverse=True)

    # Normalize (should be ~1.0 already)
    total = home_win + draw + away_win
    if total > 0:
        home_win /= total
        draw /= total
        away_win /= total

    return home_win, draw, away_win, scorelines[:5]


class PoissonPredictor:
    """
    Goal-based prediction using Poisson distribution.

    Key insight: Football goals follow a Poisson distribution.
    By modeling xG, we get natural draw probabilities.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH

        # League-wide averages (will be calculated from data)
        self.league_avg_home_goals = 1.55  # Historical PL average
        self.league_avg_away_goals = 1.20  # Historical PL average

        # Team strength ratings (attack and defense)
        self.team_attack = {}   # Goals scored per game / league avg
        self.team_defense = {}  # Goals conceded per game / league avg

        # Load historical data
        self._calculate_team_strengths()

    def _calculate_team_strengths(self):
        """
        Calculate attack and defense strength for each team.

        Attack Strength = (Team Goals Scored / Team Games) / League Avg Goals
        Defense Strength = (Team Goals Conceded / Team Games) / League Avg Goals
        """
        if not self.db_path.exists():
            self._use_default_strengths()
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get recent Premier League matches (last 2 seasons)
            cursor.execute("""
                SELECT home_team, away_team, ft_home, ft_away
                FROM match_history
                WHERE division = 'E0'
                  AND match_date >= '2023-01-01'
                  AND ft_home IS NOT NULL
                  AND ft_away IS NOT NULL
            """)

            matches = cursor.fetchall()
            conn.close()

            if len(matches) < 100:
                self._use_default_strengths()
                return

            # Calculate team statistics
            team_stats = defaultdict(lambda: {
                "home_scored": 0, "home_conceded": 0, "home_games": 0,
                "away_scored": 0, "away_conceded": 0, "away_games": 0
            })

            total_home_goals = 0
            total_away_goals = 0
            total_games = 0

            for home, away, h_goals, a_goals in matches:
                if h_goals is None or a_goals is None:
                    continue

                home = home.lower().replace(" ", "_")
                away = away.lower().replace(" ", "_")

                team_stats[home]["home_scored"] += h_goals
                team_stats[home]["home_conceded"] += a_goals
                team_stats[home]["home_games"] += 1

                team_stats[away]["away_scored"] += a_goals
                team_stats[away]["away_conceded"] += h_goals
                team_stats[away]["away_games"] += 1

                total_home_goals += h_goals
                total_away_goals += a_goals
                total_games += 1

            # League averages
            self.league_avg_home_goals = total_home_goals / total_games if total_games > 0 else 1.55
            self.league_avg_away_goals = total_away_goals / total_games if total_games > 0 else 1.20

            # Calculate strength ratings
            for team, stats in team_stats.items():
                total_games = stats["home_games"] + stats["away_games"]
                if total_games < 5:
                    continue

                total_scored = stats["home_scored"] + stats["away_scored"]
                total_conceded = stats["home_conceded"] + stats["away_conceded"]

                avg_scored = total_scored / total_games
                avg_conceded = total_conceded / total_games

                league_avg_goals = (self.league_avg_home_goals + self.league_avg_away_goals) / 2

                self.team_attack[team] = avg_scored / league_avg_goals
                self.team_defense[team] = avg_conceded / league_avg_goals

            print(f"Poisson: Loaded {len(self.team_attack)} teams from {total_games} matches")
            print(f"  League avg: {self.league_avg_home_goals:.2f} home, {self.league_avg_away_goals:.2f} away")

        except Exception as e:
            print(f"Error calculating strengths: {e}")
            self._use_default_strengths()

    def _use_default_strengths(self):
        """Use default Premier League team strengths."""
        defaults = {
            "manchester_city": (1.45, 0.55),
            "arsenal": (1.35, 0.65),
            "liverpool": (1.40, 0.60),
            "chelsea": (1.15, 0.85),
            "tottenham": (1.20, 0.90),
            "manchester_united": (1.10, 0.95),
            "newcastle": (1.15, 0.80),
            "aston_villa": (1.20, 0.85),
            "brighton": (1.10, 0.90),
            "west_ham": (1.00, 1.00),
            "brentford": (1.05, 1.00),
            "fulham": (0.95, 1.05),
            "crystal_palace": (0.90, 1.00),
            "wolves": (0.85, 0.95),
            "bournemouth": (0.95, 1.10),
            "nottingham_forest": (0.85, 1.05),
            "everton": (0.80, 1.00),
            "leicester": (0.90, 1.15),
            "ipswich": (0.75, 1.20),
            "southampton": (0.80, 1.25),
        }

        for team, (attack, defense) in defaults.items():
            self.team_attack[team] = attack
            self.team_defense[team] = defense

    def _normalize_team(self, name: str) -> str:
        """Normalize team name to match our keys."""
        name = name.lower().strip()

        aliases = {
            "manchester city": "manchester_city",
            "man city": "manchester_city",
            "manchester united": "manchester_united",
            "man united": "manchester_united",
            "man utd": "manchester_united",
            "tottenham hotspur": "tottenham",
            "spurs": "tottenham",
            "wolverhampton": "wolves",
            "wolverhampton wanderers": "wolves",
            "nottingham forest": "nottingham_forest",
            "nott'm forest": "nottingham_forest",
            "crystal palace": "crystal_palace",
            "west ham": "west_ham",
            "west ham united": "west_ham",
            "aston villa": "aston_villa",
            "leicester city": "leicester",
            "ipswich town": "ipswich",
        }

        if name in aliases:
            return aliases[name]

        return name.replace(" ", "_")

    def predict(self, home_team: str, away_team: str) -> PoissonPrediction:
        """
        Predict match outcome using Poisson goal model.

        Expected Goals Formula:
        Home xG = League Avg Home × Home Attack × Away Defense
        Away xG = League Avg Away × Away Attack × Home Defense
        """
        home_norm = self._normalize_team(home_team)
        away_norm = self._normalize_team(away_team)

        # Get team strengths (default to average if unknown)
        home_attack = self.team_attack.get(home_norm, 1.0)
        home_defense = self.team_defense.get(home_norm, 1.0)
        away_attack = self.team_attack.get(away_norm, 1.0)
        away_defense = self.team_defense.get(away_norm, 1.0)

        # Calculate expected goals
        home_xg = self.league_avg_home_goals * home_attack * away_defense
        away_xg = self.league_avg_away_goals * away_attack * home_defense

        # Clamp xG to reasonable range
        home_xg = max(0.3, min(4.0, home_xg))
        away_xg = max(0.2, min(3.5, away_xg))

        # Calculate probabilities
        home_prob, draw_prob, away_prob, likely_scores = calculate_match_probabilities(home_xg, away_xg)

        # Determine prediction
        probs = {"home_win": home_prob, "draw": draw_prob, "away_win": away_prob}
        prediction = max(probs, key=probs.get)

        # Confidence based on margin
        max_prob = max(probs.values())
        if max_prob > 0.50:
            confidence = "high"
        elif max_prob > 0.40:
            confidence = "medium"
        else:
            confidence = "low"

        return PoissonPrediction(
            home_team=home_team,
            away_team=away_team,
            home_xg=home_xg,
            away_xg=away_xg,
            home_win_prob=home_prob,
            draw_prob=draw_prob,
            away_win_prob=away_prob,
            prediction=prediction,
            confidence=confidence,
            likely_scores=likely_scores,
            home_attack=home_attack,
            home_defense=home_defense,
            away_attack=away_attack,
            away_defense=away_defense
        )


def backtest_poisson(start_date: str = "2024-08-01", end_date: str = "2024-12-31") -> Dict:
    """Backtest Poisson predictor."""
    predictor = PoissonPredictor()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT home_team, away_team, ft_home, ft_away, ft_result
        FROM match_history
        WHERE division = 'E0'
          AND match_date BETWEEN ? AND ?
        ORDER BY match_date
    """, (start_date, end_date))

    matches = cursor.fetchall()
    conn.close()

    results = {
        "total": 0, "correct": 0,
        "home_correct": 0, "home_total": 0,
        "draw_correct": 0, "draw_total": 0,
        "away_correct": 0, "away_total": 0,
        "brier_sum": 0.0
    }

    result_map = {"H": "home_win", "D": "draw", "A": "away_win"}

    for match in matches:
        home, away, h_goals, a_goals, actual_result = match

        if actual_result not in result_map:
            continue

        actual = result_map[actual_result]

        pred = predictor.predict(home, away)
        correct = pred.prediction == actual

        results["total"] += 1
        if correct:
            results["correct"] += 1

        if actual == "home_win":
            results["home_total"] += 1
            if correct:
                results["home_correct"] += 1
        elif actual == "draw":
            results["draw_total"] += 1
            if correct:
                results["draw_correct"] += 1
        elif actual == "away_win":
            results["away_total"] += 1
            if correct:
                results["away_correct"] += 1

        # Brier score
        actual_vec = [1 if actual == "home_win" else 0,
                     1 if actual == "draw" else 0,
                     1 if actual == "away_win" else 0]
        probs = (pred.home_win_prob, pred.draw_prob, pred.away_win_prob)
        brier = sum((p - a) ** 2 for p, a in zip(probs, actual_vec))
        results["brier_sum"] += brier

    # Calculate final metrics
    results["overall_accuracy"] = results["correct"] / results["total"] if results["total"] > 0 else 0
    results["home_accuracy"] = results["home_correct"] / results["home_total"] if results["home_total"] > 0 else 0
    results["draw_accuracy"] = results["draw_correct"] / results["draw_total"] if results["draw_total"] > 0 else 0
    results["away_accuracy"] = results["away_correct"] / results["away_total"] if results["away_total"] > 0 else 0
    results["brier_score"] = results["brier_sum"] / results["total"] if results["total"] > 0 else 0

    return results


if __name__ == "__main__":
    print("=" * 70)
    print("POISSON GOAL PREDICTOR: THE THIRD LENS")
    print("=" * 70)

    predictor = PoissonPredictor()

    # Demo predictions
    test_matches = [
        ("Liverpool", "Leicester"),
        ("Manchester United", "Newcastle"),
        ("Arsenal", "Ipswich"),
        ("Chelsea", "Fulham"),
        ("Everton", "Nottingham Forest"),
    ]

    print("\n🎯 Sample Predictions:\n")

    for home, away in test_matches:
        pred = predictor.predict(home, away)
        print(f"{home} vs {away}")
        print(f"  xG: {pred.home_xg:.2f} - {pred.away_xg:.2f}")
        print(f"  Probabilities: H:{pred.home_win_prob:.0%} D:{pred.draw_prob:.0%} A:{pred.away_win_prob:.0%}")
        print(f"  Prediction: {pred.prediction.upper()} ({pred.confidence})")
        print(f"  Likely scores: {pred.likely_scores[:3]}")
        print()

    # Backtest
    print("=" * 70)
    print("BACKTEST: 2024-25 Season")
    print("=" * 70)

    results = backtest_poisson("2024-08-01", "2024-12-31")

    print(f"\nTotal matches: {results['total']}")
    print(f"\n✅ OVERALL ACCURACY: {results['overall_accuracy']:.1%}")
    print(f"   Home Win: {results['home_accuracy']:.1%} ({results['home_correct']}/{results['home_total']})")
    print(f"   Draw:     {results['draw_accuracy']:.1%} ({results['draw_correct']}/{results['draw_total']})")
    print(f"   Away Win: {results['away_accuracy']:.1%} ({results['away_correct']}/{results['away_total']})")
    print(f"   Brier:    {results['brier_score']:.4f}")
