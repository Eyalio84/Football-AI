"""
Football Oracle v4.0 - Soccer-AI Winner Prediction System
==========================================================
"The Oracle sees what others miss."

Data-driven winner prediction using 230K+ historical matches.
Part of the Soccer-AI Knowledge Graph Architecture.

Key Statistical Discoveries (from match_history analysis):
1. Draw rates vary 19.4% - 30.1% based on odds gap (not fixed 15%)
2. Form differential strongly predicts outcomes
3. 2024 shows trend shift: higher draws (26.3%), lower home advantage (42.2%)
4. Betting odds are extremely well-calibrated for draws
5. Goal-scoring patterns correlate with draw probability

The Oracle combines:
- ELO-based power ratings
- Betting odds calibration (market wisdom)
- Form differential adjustment
- Dynamic draw probability
- Modern era (2024+) adjustment
- Head-to-head historical patterns
- Derby/rivalry detection
"""

import math
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List
from datetime import datetime

# Database path (project root contains the database)
DB_PATH = Path(__file__).parent.parent / "unified_soccer_ai_kg.db"


@dataclass
class MatchPrediction:
    """Complete match prediction with probabilities and confidence."""
    home_team: str
    away_team: str
    home_win_prob: float  # 0-1
    draw_prob: float      # 0-1
    away_win_prob: float  # 0-1
    prediction: str       # 'home_win', 'draw', 'away_win'
    confidence: str       # 'low', 'medium', 'high'
    confidence_score: float  # 0-1

    # Analysis components
    power_diff: float
    form_diff: float
    odds_calibration: Dict
    draw_factors: List[str]
    explanation: str

    def to_dict(self) -> Dict:
        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_win": round(self.home_win_prob * 100, 1),
            "draw": round(self.draw_prob * 100, 1),
            "away_win": round(self.away_win_prob * 100, 1),
            "prediction": self.prediction,
            "confidence": self.confidence,
            "confidence_score": round(self.confidence_score * 100),
            "power_diff": round(self.power_diff, 1),
            "form_diff": round(self.form_diff, 2),
            "draw_factors": self.draw_factors,
            "explanation": self.explanation
        }


# === STATISTICAL CONSTANTS FROM DATA ANALYSIS ===

# Draw rate by odds gap (from 9,410 Premier League matches)
DRAW_RATE_BY_ODDS_GAP = {
    "tight": 0.301,    # |home_odds - away_odds| < 0.5
    "close": 0.297,    # 0.5 - 1.5
    "medium": 0.254,   # 1.5 - 3.0
    "large": 0.194,    # > 3.0
}

# Form differential impact on outcomes (empirical)
FORM_IMPACT = {
    # form_diff = home_form - away_form
    # Returns (home_win_adj, draw_adj, away_win_adj)
    "home_much_better": (0.585, 0.226, 0.189),   # diff > 2
    "home_better": (0.492, 0.252, 0.256),         # diff > 0.5
    "similar": (0.474, 0.252, 0.273),             # |diff| <= 0.5
    "away_better": (0.435, 0.254, 0.312),         # diff < -0.5
    "away_much_better": (0.337, 0.251, 0.412),   # diff < -2
}

# Modern era adjustment (2024 trend)
MODERN_ERA_ADJ = {
    "home_advantage_reduction": 0.04,  # 4% less home advantage vs historical
    "draw_increase": 0.03,              # 3% more draws
}

# Home advantage baseline (ELO points)
HOME_ADVANTAGE_ELO = 65

# ELO scale parameters
ELO_MIN = 1200
ELO_MAX = 1800
BASE_ELO = 1500


class FootballOracle:
    """
    The Oracle sees what others miss.

    Data-driven match prediction using 230K+ historical patterns.
    Uses statistical discoveries from Premier League history to
    predict match outcomes with calibrated probabilities.

    Components:
    1. ELO-based power ratings
    2. Betting odds calibration (market wisdom)
    3. Form differential adjustment
    4. Head-to-head history
    5. Derby/rivalry detection
    6. Modern era (2024+) trend adjustment
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.team_ratings: Dict[str, float] = {}
        self.team_form: Dict[str, List[str]] = {}
        self._load_ratings()

    def _load_ratings(self):
        """Load current team ratings from database or initialize defaults."""
        # Premier League 2024-25 starting ELOs (based on 2023-24 finish + transfers)
        default_ratings = {
            "Manchester City": 1780, "manchester_city": 1780,
            "Arsenal": 1740, "arsenal": 1740,
            "Liverpool": 1720, "liverpool": 1720,
            "Chelsea": 1620, "chelsea": 1620,
            "Tottenham": 1600, "tottenham": 1600,
            "Manchester United": 1580, "manchester_united": 1580,
            "Newcastle": 1570, "newcastle": 1570,
            "Aston Villa": 1560, "aston_villa": 1560,
            "Brighton": 1530, "brighton": 1530,
            "West Ham": 1510, "west_ham": 1510,
            "Brentford": 1490, "brentford": 1490,
            "Fulham": 1480, "fulham": 1480,
            "Crystal Palace": 1470, "crystal_palace": 1470,
            "Wolves": 1460, "wolves": 1460,
            "Bournemouth": 1450, "bournemouth": 1450,
            "Nottingham Forest": 1440, "nottingham_forest": 1440,
            "Everton": 1420, "everton": 1420,
            "Leicester": 1400, "leicester": 1400,
            "Ipswich": 1370, "ipswich": 1370,
            "Southampton": 1360, "southampton": 1360,
        }
        self.team_ratings = default_ratings

        # Try to load from team_ratings.json if exists
        ratings_file = Path(__file__).parent / "team_ratings.json"
        if ratings_file.exists():
            try:
                import json
                with open(ratings_file) as f:
                    data = json.load(f)
                    for team_id, rating_data in data.get("ratings", {}).items():
                        self.team_ratings[team_id] = rating_data.get("elo", BASE_ELO)
                        self.team_form[team_id] = rating_data.get("form_last_5", [])
            except Exception as e:
                print(f"Warning: Could not load ratings: {e}")

    def _get_elo(self, team: str) -> float:
        """Get ELO rating for team (handles name variations)."""
        # Normalize team name
        team_key = team.lower().replace(" ", "_").replace("-", "_")

        # Try exact match first
        if team_key in self.team_ratings:
            return self.team_ratings[team_key]

        # Try original name
        if team in self.team_ratings:
            return self.team_ratings[team]

        # Default
        return BASE_ELO

    def _get_form_score(self, team: str) -> float:
        """
        Get form score (0-1) from last 5 matches.
        W=1, D=0.5, L=0
        """
        team_key = team.lower().replace(" ", "_")
        form = self.team_form.get(team_key, [])

        if not form:
            return 0.5  # Neutral

        points = sum(1 if r == 'W' else 0.5 if r == 'D' else 0 for r in form)
        return points / len(form)

    def _expected_score(self, elo_a: float, elo_b: float) -> float:
        """Standard ELO expected score formula."""
        return 1 / (1 + math.pow(10, (elo_b - elo_a) / 400))

    def _classify_odds_gap(self, home_odds: float, away_odds: float) -> str:
        """Classify odds gap for draw rate lookup."""
        gap = abs(home_odds - away_odds)
        if gap < 0.5:
            return "tight"
        elif gap < 1.5:
            return "close"
        elif gap < 3.0:
            return "medium"
        else:
            return "large"

    def _classify_form_diff(self, form_diff: float) -> str:
        """Classify form differential."""
        if form_diff > 2:
            return "home_much_better"
        elif form_diff > 0.5:
            return "home_better"
        elif form_diff < -2:
            return "away_much_better"
        elif form_diff < -0.5:
            return "away_better"
        else:
            return "similar"

    def _get_h2h_adjustment(self, home_team: str, away_team: str) -> float:
        """
        Get head-to-head adjustment from database.

        Returns: adjustment (-0.15 to +0.15)
        - Positive = home team historically dominant
        - Negative = away team historically dominant
        """
        if not self.db_path.exists():
            return 0.0

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get last 10 meetings
            cursor.execute("""
                SELECT ft_result, COUNT(*) as cnt
                FROM match_history
                WHERE (home_team LIKE ? AND away_team LIKE ?)
                   OR (home_team LIKE ? AND away_team LIKE ?)
                GROUP BY ft_result
                ORDER BY match_date DESC
                LIMIT 10
            """, (f"%{home_team}%", f"%{away_team}%",
                  f"%{away_team}%", f"%{home_team}%"))

            results = cursor.fetchall()
            conn.close()

            if not results:
                return 0.0

            # Calculate home team advantage
            home_wins = 0
            away_wins = 0
            total = 0

            for result, count in results:
                total += count
                if result == 'H':
                    home_wins += count
                elif result == 'A':
                    away_wins += count

            if total < 3:
                return 0.0  # Not enough data

            # Convert to adjustment
            home_advantage = (home_wins - away_wins) / total
            return max(-0.15, min(0.15, home_advantage * 0.3))

        except Exception as e:
            print(f"H2H lookup error: {e}")
            return 0.0

    def _is_derby(self, home_team: str, away_team: str) -> bool:
        """Check if match is a derby/rivalry."""
        derbies = {
            ("liverpool", "everton"),
            ("manchester_united", "manchester_city"),
            ("arsenal", "tottenham"),
            ("west_ham", "tottenham"),
            ("crystal_palace", "brighton"),
            ("aston_villa", "wolves"),
            ("manchester_united", "liverpool"),
            ("arsenal", "chelsea"),
        }

        h = home_team.lower().replace(" ", "_")
        a = away_team.lower().replace(" ", "_")

        return (h, a) in derbies or (a, h) in derbies

    def predict(
        self,
        home_team: str,
        away_team: str,
        home_odds: Optional[float] = None,
        draw_odds: Optional[float] = None,
        away_odds: Optional[float] = None
    ) -> MatchPrediction:
        """
        Generate match prediction using statistical model.

        Args:
            home_team: Home team name
            away_team: Away team name
            home_odds: Optional betting odds for home win
            draw_odds: Optional betting odds for draw
            away_odds: Optional betting odds for away win

        Returns:
            MatchPrediction with probabilities and analysis
        """
        draw_factors = []

        # Step 1: Get base ELO ratings
        home_elo = self._get_elo(home_team)
        away_elo = self._get_elo(away_team)

        # Apply home advantage
        home_effective = home_elo + HOME_ADVANTAGE_ELO

        # Step 2: Calculate base win probability from ELO
        home_base = self._expected_score(home_effective, away_elo)
        away_base = 1 - home_base

        # Power difference (0-100 scale)
        power_diff = ((home_elo - away_elo) / (ELO_MAX - ELO_MIN)) * 100

        # Step 3: Calculate form differential
        home_form = self._get_form_score(home_team)
        away_form = self._get_form_score(away_team)
        form_diff = (home_form - away_form) * 9  # Scale to match historical buckets

        # Step 4: Determine draw probability
        if home_odds and away_odds:
            # Use betting odds calibration
            odds_gap = self._classify_odds_gap(home_odds, away_odds)
            base_draw_prob = DRAW_RATE_BY_ODDS_GAP[odds_gap]
            draw_factors.append(f"Odds-based draw: {odds_gap} gap → {base_draw_prob:.1%}")
        else:
            # Use ELO-based draw estimation
            elo_diff = abs(home_elo - away_elo)
            if elo_diff < 50:
                base_draw_prob = 0.30
                draw_factors.append("Very close match (ELO diff < 50)")
            elif elo_diff < 100:
                base_draw_prob = 0.27
            elif elo_diff < 150:
                base_draw_prob = 0.24
            elif elo_diff < 200:
                base_draw_prob = 0.21
            else:
                base_draw_prob = 0.18

        # Step 5: Apply form differential adjustment
        form_category = self._classify_form_diff(form_diff)
        form_probs = FORM_IMPACT[form_category]

        # Blend ELO base with form-based probabilities
        elo_weight = 0.6
        form_weight = 0.4

        home_prob = (home_base * elo_weight) + (form_probs[0] * form_weight)
        away_prob = (away_base * elo_weight) + (form_probs[2] * form_weight)
        draw_prob = base_draw_prob

        # Step 6: Apply H2H adjustment
        h2h_adj = self._get_h2h_adjustment(home_team, away_team)
        if abs(h2h_adj) > 0.03:
            home_prob += h2h_adj
            away_prob -= h2h_adj
            draw_factors.append(f"H2H advantage: {'home' if h2h_adj > 0 else 'away'}")

        # Step 7: Derby adjustment (increases draw probability)
        if self._is_derby(home_team, away_team):
            draw_prob += 0.05
            draw_factors.append("Derby match: +5% draw")

        # Step 8: Modern era adjustment (2024+)
        home_prob -= MODERN_ERA_ADJ["home_advantage_reduction"]
        draw_prob += MODERN_ERA_ADJ["draw_increase"]
        away_prob += MODERN_ERA_ADJ["home_advantage_reduction"] - MODERN_ERA_ADJ["draw_increase"]

        # Step 9: Normalize probabilities to sum to 1
        total = home_prob + draw_prob + away_prob
        home_prob /= total
        draw_prob /= total
        away_prob /= total

        # Clamp to reasonable ranges
        home_prob = max(0.05, min(0.85, home_prob))
        away_prob = max(0.05, min(0.85, away_prob))
        draw_prob = max(0.10, min(0.40, draw_prob))

        # Re-normalize
        total = home_prob + draw_prob + away_prob
        home_prob /= total
        draw_prob /= total
        away_prob /= total

        # Step 10: Determine prediction with SMART DRAW THRESHOLD
        # Insight #1032: Draws rarely exceed 33%, so they never win max()
        # Solution: Override when draw conditions are strong
        probs = {"home_win": home_prob, "draw": draw_prob, "away_win": away_prob}

        # Calculate win probability gap
        win_gap = abs(home_prob - away_prob)

        # Smart draw detection: predict draw when:
        # 1. Draw probability is high (>28%), AND
        # 2. Win probabilities are close (<10% difference)
        if draw_prob > 0.28 and win_gap < 0.10:
            prediction = "draw"
            draw_factors.append(f"Draw threshold triggered: {draw_prob:.1%} draw, {win_gap:.1%} win gap")
        # Also predict draw when very evenly matched
        elif draw_prob > 0.25 and win_gap < 0.06:
            prediction = "draw"
            draw_factors.append(f"Even match draw: {draw_prob:.1%} draw, {win_gap:.1%} win gap")
        else:
            prediction = max(probs, key=probs.get)

        # Step 11: Calculate confidence
        max_prob = max(probs.values())
        second_prob = sorted(probs.values(), reverse=True)[1]
        margin = max_prob - second_prob

        if margin > 0.25:
            confidence = "high"
            confidence_score = 0.8 + (margin - 0.25) * 0.8
        elif margin > 0.10:
            confidence = "medium"
            confidence_score = 0.5 + (margin - 0.10) * 2
        else:
            confidence = "low"
            confidence_score = 0.3 + margin * 2

        confidence_score = min(0.95, max(0.30, confidence_score))

        # Step 12: Generate explanation
        explanation_parts = []

        if power_diff > 20:
            explanation_parts.append(f"{home_team} is significantly stronger (+{power_diff:.0f} power)")
        elif power_diff > 5:
            explanation_parts.append(f"{home_team} has slight advantage (+{power_diff:.0f} power)")
        elif power_diff < -20:
            explanation_parts.append(f"{away_team} is significantly stronger (+{-power_diff:.0f} power)")
        elif power_diff < -5:
            explanation_parts.append(f"{away_team} has slight advantage (+{-power_diff:.0f} power)")
        else:
            explanation_parts.append("Teams are evenly matched")

        if form_diff > 1:
            explanation_parts.append(f"{home_team} in better form")
        elif form_diff < -1:
            explanation_parts.append(f"{away_team} in better form")

        if draw_prob > 0.28:
            explanation_parts.append(f"High draw probability ({draw_prob:.1%})")

        explanation = ". ".join(explanation_parts)

        return MatchPrediction(
            home_team=home_team,
            away_team=away_team,
            home_win_prob=home_prob,
            draw_prob=draw_prob,
            away_win_prob=away_prob,
            prediction=prediction,
            confidence=confidence,
            confidence_score=confidence_score,
            power_diff=power_diff,
            form_diff=form_diff,
            odds_calibration={"home": home_odds, "draw": draw_odds, "away": away_odds},
            draw_factors=draw_factors,
            explanation=explanation
        )

    def predict_batch(
        self,
        matches: List[Tuple[str, str]]
    ) -> List[MatchPrediction]:
        """Predict multiple matches."""
        return [self.predict(home, away) for home, away in matches]

    def update_from_result(
        self,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        k_factor: float = 32
    ):
        """
        Update ratings after a match result.

        Uses standard ELO update formula.
        """
        home_elo = self._get_elo(home_team)
        away_elo = self._get_elo(away_team)

        # Expected scores
        home_expected = self._expected_score(home_elo + HOME_ADVANTAGE_ELO, away_elo)
        away_expected = 1 - home_expected

        # Actual outcomes
        if home_score > away_score:
            home_actual, away_actual = 1.0, 0.0
            result = 'W'
        elif home_score < away_score:
            home_actual, away_actual = 0.0, 1.0
            result = 'L'
        else:
            home_actual, away_actual = 0.5, 0.5
            result = 'D'

        # Update ELOs
        home_key = home_team.lower().replace(" ", "_")
        away_key = away_team.lower().replace(" ", "_")

        self.team_ratings[home_key] = home_elo + k_factor * (home_actual - home_expected)
        self.team_ratings[away_key] = away_elo + k_factor * (away_actual - away_expected)

        # Update form
        if home_key not in self.team_form:
            self.team_form[home_key] = []
        if away_key not in self.team_form:
            self.team_form[away_key] = []

        self.team_form[home_key] = (self.team_form[home_key] + [result])[-5:]
        away_result = 'W' if result == 'L' else 'L' if result == 'W' else 'D'
        self.team_form[away_key] = (self.team_form[away_key] + [away_result])[-5:]


# === BACKTEST FUNCTION ===

def backtest_oracle(
    db_path: Path,
    start_date: str = "2024-08-01",
    end_date: str = "2024-12-31"
) -> Dict:
    """
    Backtest the Football Oracle against historical matches.

    Returns accuracy metrics and match-by-match results.
    """
    oracle = FootballOracle(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT home_team, away_team, ft_home, ft_away, ft_result,
               odd_home, odd_draw, odd_away, form3_home, form3_away
        FROM match_history
        WHERE division = 'E0'
          AND match_date BETWEEN ? AND ?
        ORDER BY match_date
    """, (start_date, end_date))

    matches = cursor.fetchall()
    conn.close()

    if not matches:
        return {"error": "No matches found in date range"}

    results = {
        "total": 0,
        "correct": 0,
        "home_win_correct": 0,
        "home_win_total": 0,
        "draw_correct": 0,
        "draw_total": 0,
        "away_win_correct": 0,
        "away_win_total": 0,
        "predictions": []
    }

    # Map result codes
    result_map = {"H": "home_win", "D": "draw", "A": "away_win"}

    for match in matches:
        home, away, home_score, away_score, actual_result, h_odds, d_odds, a_odds, h_form, a_form = match

        # Skip if missing data
        if actual_result not in result_map:
            continue

        # Predict
        pred = oracle.predict(home, away, h_odds, d_odds, a_odds)

        actual = result_map[actual_result]
        correct = pred.prediction == actual

        results["total"] += 1
        if correct:
            results["correct"] += 1

        # Track by outcome type
        if actual == "home_win":
            results["home_win_total"] += 1
            if correct:
                results["home_win_correct"] += 1
        elif actual == "draw":
            results["draw_total"] += 1
            if correct:
                results["draw_correct"] += 1
        elif actual == "away_win":
            results["away_win_total"] += 1
            if correct:
                results["away_win_correct"] += 1

        results["predictions"].append({
            "match": f"{home} vs {away}",
            "actual": actual,
            "predicted": pred.prediction,
            "correct": correct,
            "home_prob": round(pred.home_win_prob * 100, 1),
            "draw_prob": round(pred.draw_prob * 100, 1),
            "away_prob": round(pred.away_win_prob * 100, 1),
            "confidence": pred.confidence
        })

        # Update ratings from result
        oracle.update_from_result(home, away, home_score or 0, away_score or 0)

    # Calculate accuracies
    results["overall_accuracy"] = results["correct"] / results["total"] if results["total"] > 0 else 0
    results["home_accuracy"] = results["home_win_correct"] / results["home_win_total"] if results["home_win_total"] > 0 else 0
    results["draw_accuracy"] = results["draw_correct"] / results["draw_total"] if results["draw_total"] > 0 else 0
    results["away_accuracy"] = results["away_win_correct"] / results["away_win_total"] if results["away_win_total"] > 0 else 0

    return results


# === DEMO ===

if __name__ == "__main__":
    print("=" * 60)
    print("⚽ FOOTBALL ORACLE v4.0")
    print("   'The Oracle sees what others miss.'")
    print("=" * 60)

    oracle = FootballOracle()

    # Test predictions
    test_matches = [
        ("Liverpool", "Manchester City"),
        ("Arsenal", "Tottenham"),
        ("Chelsea", "Wolves"),
        ("Southampton", "Manchester City"),
        ("Everton", "Nottingham Forest"),
    ]

    print("\n🔮 Oracle Predictions:\n")

    for home, away in test_matches:
        pred = oracle.predict(home, away)

        print(f"{home} vs {away}")
        print(f"  Home Win: {pred.home_win_prob:.1%}  |  Draw: {pred.draw_prob:.1%}  |  Away Win: {pred.away_win_prob:.1%}")
        print(f"  Prediction: {pred.prediction.upper()} (Confidence: {pred.confidence})")
        print(f"  Power diff: {pred.power_diff:+.1f}")
        if pred.draw_factors:
            print(f"  Draw factors: {', '.join(pred.draw_factors)}")
        print(f"  Explanation: {pred.explanation}")
        print()

    # Backtest if database exists
    if DB_PATH.exists():
        print("\n" + "=" * 60)
        print("📈 Oracle Backtest: 2024-25 Season")
        print("=" * 60)

        results = backtest_oracle(DB_PATH, "2024-08-01", "2024-12-31")

        if "error" not in results:
            print(f"\nTotal matches: {results['total']}")
            print(f"\n✅ OVERALL ACCURACY: {results['overall_accuracy']:.1%}")
            print(f"   Home Win: {results['home_accuracy']:.1%} ({results['home_win_correct']}/{results['home_win_total']})")
            print(f"   Draw:     {results['draw_accuracy']:.1%} ({results['draw_correct']}/{results['draw_total']})")
            print(f"   Away Win: {results['away_accuracy']:.1%} ({results['away_win_correct']}/{results['away_win_total']})")

            # Show some predictions
            print("\n📋 Sample Predictions:")
            for p in results['predictions'][:10]:
                status = "✓" if p['correct'] else "✗"
                print(f"  {status} {p['match']}: Pred={p['predicted']}, Actual={p['actual']}")
        else:
            print(f"Error: {results['error']}")

    print("\n" + "=" * 60)
    print("⚽ Football Oracle Demo Complete")
    print("   'The Oracle has spoken.'")
    print("=" * 60)
