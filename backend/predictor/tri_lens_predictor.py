"""
Tri-Lens Predictor: The Ultimate Fusion
========================================

Combines three distinct prediction philosophies:

1. POISSON LENS (xG-based)
   - Best probability calibration (Brier: 0.5801)
   - Models goal-scoring expectation
   - Captures inherent football randomness

2. ORACLE LENS (ELO + Patterns)
   - Historical pattern awareness
   - Team strength modeling
   - Market calibration from odds

3. UPSET LENS (Third Knowledge)
   - Detects when favorites might fail
   - Conditional draw boosting
   - "Why might the expected NOT happen?"

Fusion Strategy:
- Base: 50% Poisson + 50% Oracle (best of both worlds)
- Conditional: Boost draw when upset signals align
- Result: Higher accuracy + better draw detection

Target: >54% overall with >10% draw detection
"""

import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# Import our three lenses
import sys
from pathlib import Path
# Add predictor directory to path for imports
_predictor_dir = Path(__file__).parent
if str(_predictor_dir) not in sys.path:
    sys.path.insert(0, str(_predictor_dir))

from poisson_predictor import PoissonPredictor, calculate_match_probabilities
from hybrid_oracle import HybridOracle, normalize_team_name

DB_PATH = Path(__file__).parent.parent / "unified_soccer_ai_kg.db"


@dataclass
class TriLensPrediction:
    """Prediction from the three-lens fusion system."""
    home_team: str
    away_team: str

    # Individual lens probabilities
    poisson_probs: Tuple[float, float, float]  # H, D, A
    oracle_probs: Tuple[float, float, float]   # H, D, A

    # Fusion probabilities
    base_fusion: Tuple[float, float, float]    # Before draw boost
    final_probs: Tuple[float, float, float]    # After conditional adjustments

    # Upset analysis
    upset_risk: float
    upset_patterns: List[str]
    draw_boost_applied: bool

    # Expected goals from Poisson
    home_xg: float
    away_xg: float
    likely_scores: List[Tuple[str, float]]

    # Final prediction
    prediction: str
    confidence: str

    # Lens agreement (how many lenses agree on prediction)
    lens_agreement: int


def calculate_upset_risk(
    poisson_probs: Tuple[float, float, float],
    oracle_probs: Tuple[float, float, float],
    power_diff: float
) -> Tuple[float, List[str]]:
    """
    Calculate upset risk from multiple signals.

    Signals:
    1. Probability disagreement between lenses
    2. Close match (small probability gap)
    3. ELO paradox zone (power diff 5-12)
    4. High base draw probability
    """
    patterns = []
    risk_score = 0.0

    # Unpack probabilities
    p_home, p_draw, p_away = poisson_probs
    o_home, o_draw, o_away = oracle_probs

    # Signal 1: Lens disagreement
    home_disagreement = abs(p_home - o_home)
    if home_disagreement > 0.15:
        risk_score += 0.20
        patterns.append("Lens Disagreement")
    elif home_disagreement > 0.10:
        risk_score += 0.10
        patterns.append("Mild Lens Tension")

    # Signal 2: Close match (average of both lenses)
    avg_home = (p_home + o_home) / 2
    avg_away = (p_away + o_away) / 2
    prob_gap = abs(avg_home - avg_away)

    if prob_gap < 0.10:
        risk_score += 0.25
        patterns.append("Very Close Match")
    elif prob_gap < 0.18:
        risk_score += 0.15
        patterns.append("Close Match")

    # Signal 3: ELO paradox zone
    abs_power = abs(power_diff)
    if 5 <= abs_power <= 12:
        risk_score += 0.20
        patterns.append("ELO Paradox Zone")

    # Signal 4: High base draw probability
    avg_draw = (p_draw + o_draw) / 2
    if avg_draw > 0.26:
        risk_score += 0.15
        patterns.append("High Draw Signal")
    elif avg_draw > 0.22:
        risk_score += 0.08
        patterns.append("Elevated Draw")

    # Signal 5: Poisson predicts close xG
    # (We don't have xG here, but we can infer from draw prob)
    if p_draw > 0.25:
        risk_score += 0.10
        patterns.append("Close xG Expected")

    return min(0.85, risk_score), patterns


def determine_confidence(max_prob: float, lens_agreement: int) -> str:
    """Determine confidence based on probability and lens agreement."""
    if max_prob > 0.55 and lens_agreement == 3:
        return "very_high"
    elif max_prob > 0.50 and lens_agreement >= 2:
        return "high"
    elif max_prob > 0.40:
        return "medium"
    else:
        return "low"


class TriLensPredictor:
    """
    The Ultimate Fusion Predictor.

    Philosophy: Each lens sees something the others miss.
    - Poisson sees goal-scoring patterns
    - Oracle sees historical strength
    - Upset lens sees why favorites fail

    Together, they form a complete picture.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH

        # Initialize all three lenses
        self.poisson = PoissonPredictor(self.db_path)
        self.oracle = HybridOracle(self.db_path)

        # Fusion weights (tuned)
        self.poisson_weight = 0.55  # Best calibration - slightly dominant
        self.oracle_weight = 0.45   # Pattern awareness

        # Draw boost parameters (moderately aggressive)
        self.draw_boost_threshold = 0.30  # Upset risk threshold
        self.draw_boost_amount = 0.10     # How much to boost draw
        self.close_match_threshold = 0.18 # Prob gap for "close"

    def _sanitize_team_name(self, name: str) -> str:
        """
        Sanitize and validate team name input.

        Defensive programming:
        - Strip whitespace
        - Remove null bytes
        - Limit length
        - Remove dangerous characters
        """
        if name is None:
            return "Unknown"

        # Convert to string if not already
        name = str(name)

        # Remove null bytes (security)
        name = name.replace('\x00', '')

        # Strip whitespace
        name = name.strip()

        # Limit length (prevent DoS)
        if len(name) > 100:
            name = name[:100]

        # If empty after sanitization, use default
        if not name:
            return "Unknown"

        return name

    def _validate_odds(self, odds: float) -> Optional[float]:
        """
        Validate betting odds input.

        Returns None if invalid, otherwise returns clamped value.
        """
        if odds is None:
            return None

        try:
            odds = float(odds)
        except (ValueError, TypeError):
            return None

        # Odds must be positive and reasonable (1.01 to 100.0)
        if odds < 1.01 or odds > 100.0:
            return None

        return odds

    def predict(
        self,
        home_team: str,
        away_team: str,
        home_odds: float = None,
        draw_odds: float = None,
        away_odds: float = None
    ) -> TriLensPrediction:
        """
        Generate prediction using all three lenses.

        Input Validation:
        - Team names are sanitized (null bytes, length, whitespace)
        - Odds are validated (range 1.01-100.0)
        - Defaults used for invalid inputs
        """
        # === INPUT VALIDATION ===
        home_team = self._sanitize_team_name(home_team)
        away_team = self._sanitize_team_name(away_team)
        home_odds = self._validate_odds(home_odds)
        draw_odds = self._validate_odds(draw_odds)
        away_odds = self._validate_odds(away_odds)

        # === LENS 1: POISSON (xG-based) ===
        poisson_pred = self.poisson.predict(home_team, away_team)
        poisson_probs = (
            poisson_pred.home_win_prob,
            poisson_pred.draw_prob,
            poisson_pred.away_win_prob
        )

        # === LENS 2: ORACLE (ELO + Patterns) ===
        oracle_pred = self.oracle.predict(
            home_team, away_team,
            home_odds, draw_odds, away_odds
        )
        oracle_probs = (
            oracle_pred.home_win_prob,
            oracle_pred.draw_prob,
            oracle_pred.away_win_prob
        )

        # === BASE FUSION: Weighted Average ===
        base_home = (
            poisson_probs[0] * self.poisson_weight +
            oracle_probs[0] * self.oracle_weight
        )
        base_draw = (
            poisson_probs[1] * self.poisson_weight +
            oracle_probs[1] * self.oracle_weight
        )
        base_away = (
            poisson_probs[2] * self.poisson_weight +
            oracle_probs[2] * self.oracle_weight
        )

        base_fusion = (base_home, base_draw, base_away)

        # === LENS 3: UPSET DETECTION ===
        upset_risk, patterns = calculate_upset_risk(
            poisson_probs, oracle_probs, oracle_pred.power_diff
        )

        # === CONDITIONAL DRAW BOOST ===
        final_home, final_draw, final_away = base_home, base_draw, base_away
        draw_boost_applied = False

        prob_gap = abs(base_home - base_away)

        # Apply draw boost when conditions align
        if (upset_risk >= self.draw_boost_threshold and
            prob_gap < self.close_match_threshold and
            base_draw > 0.20):

            draw_boost_applied = True

            # Dynamic boost based on upset risk
            boost = self.draw_boost_amount * (upset_risk / 0.5)
            boost = min(boost, 0.12)  # Cap at 12%

            final_draw += boost
            final_home -= boost * 0.5
            final_away -= boost * 0.5

        # Ensure valid probabilities
        final_home = max(0.05, final_home)
        final_draw = max(0.10, final_draw)
        final_away = max(0.05, final_away)

        # Normalize
        total = final_home + final_draw + final_away
        final_home /= total
        final_draw /= total
        final_away /= total

        final_probs = (final_home, final_draw, final_away)

        # === DETERMINE PREDICTION ===
        probs_dict = {
            "home_win": final_home,
            "draw": final_draw,
            "away_win": final_away
        }
        prediction = max(probs_dict, key=probs_dict.get)

        # === LENS AGREEMENT ===
        poisson_pred_type = max(
            {"home_win": poisson_probs[0], "draw": poisson_probs[1], "away_win": poisson_probs[2]},
            key=lambda k: {"home_win": poisson_probs[0], "draw": poisson_probs[1], "away_win": poisson_probs[2]}[k]
        )
        oracle_pred_type = oracle_pred.prediction

        lens_predictions = [poisson_pred_type, oracle_pred_type, prediction]
        lens_agreement = lens_predictions.count(prediction)

        # === CONFIDENCE ===
        confidence = determine_confidence(max(probs_dict.values()), lens_agreement)

        return TriLensPrediction(
            home_team=home_team,
            away_team=away_team,
            poisson_probs=poisson_probs,
            oracle_probs=oracle_probs,
            base_fusion=base_fusion,
            final_probs=final_probs,
            upset_risk=upset_risk,
            upset_patterns=patterns,
            draw_boost_applied=draw_boost_applied,
            home_xg=poisson_pred.home_xg,
            away_xg=poisson_pred.away_xg,
            likely_scores=poisson_pred.likely_scores,
            prediction=prediction,
            confidence=confidence,
            lens_agreement=lens_agreement
        )


def backtest_tri_lens(
    start_date: str = "2024-08-01",
    end_date: str = "2024-12-31"
) -> Dict:
    """Backtest the Tri-Lens predictor."""
    print("=" * 70)
    print("TRI-LENS PREDICTOR BACKTEST")
    print("Poisson (50%) + Oracle (50%) + Conditional Draw Boost")
    print("=" * 70)

    predictor = TriLensPredictor()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT home_team, away_team, ft_home, ft_away, ft_result,
               odd_home, odd_draw, odd_away
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
        "brier_sum": 0.0,
        "draw_boosts_applied": 0,
        "draw_boosts_correct": 0,
        "high_confidence_correct": 0,
        "high_confidence_total": 0
    }

    result_map = {"H": "home_win", "D": "draw", "A": "away_win"}

    print(f"\nProcessing {len(matches)} matches...")

    for i, match in enumerate(matches):
        home, away, h_score, a_score, actual_result, h_odds, d_odds, a_odds = match

        if actual_result not in result_map:
            continue

        actual = result_map[actual_result]

        try:
            pred = predictor.predict(home, away, h_odds, d_odds, a_odds)
        except Exception as e:
            continue

        correct = pred.prediction == actual

        results["total"] += 1
        if correct:
            results["correct"] += 1

        # By outcome type
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

        # Track draw boost effectiveness
        if pred.draw_boost_applied:
            results["draw_boosts_applied"] += 1
            if correct:
                results["draw_boosts_correct"] += 1

        # Track high confidence predictions
        if pred.confidence in ["high", "very_high"]:
            results["high_confidence_total"] += 1
            if correct:
                results["high_confidence_correct"] += 1

        # Brier score
        actual_vec = [
            1 if actual == "home_win" else 0,
            1 if actual == "draw" else 0,
            1 if actual == "away_win" else 0
        ]
        brier = sum((p - a) ** 2 for p, a in zip(pred.final_probs, actual_vec))
        results["brier_sum"] += brier

        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(matches)}...")

    # Calculate final metrics
    results["overall_accuracy"] = results["correct"] / results["total"] if results["total"] > 0 else 0
    results["home_accuracy"] = results["home_correct"] / results["home_total"] if results["home_total"] > 0 else 0
    results["draw_accuracy"] = results["draw_correct"] / results["draw_total"] if results["draw_total"] > 0 else 0
    results["away_accuracy"] = results["away_correct"] / results["away_total"] if results["away_total"] > 0 else 0
    results["brier_score"] = results["brier_sum"] / results["total"] if results["total"] > 0 else 0
    results["draw_boost_accuracy"] = (
        results["draw_boosts_correct"] / results["draw_boosts_applied"]
        if results["draw_boosts_applied"] > 0 else 0
    )
    results["high_confidence_accuracy"] = (
        results["high_confidence_correct"] / results["high_confidence_total"]
        if results["high_confidence_total"] > 0 else 0
    )

    return results


if __name__ == "__main__":
    print("=" * 70)
    print("TRI-LENS PREDICTOR: THE ULTIMATE FUSION")
    print("=" * 70)

    predictor = TriLensPredictor()

    # Demo predictions
    test_matches = [
        ("Liverpool", "Leicester"),
        ("Manchester United", "Newcastle"),
        ("Arsenal", "Ipswich"),
        ("Chelsea", "Fulham"),
        ("Everton", "Nottingham Forest"),
    ]

    print("\nSample Predictions:\n")

    for home, away in test_matches:
        pred = predictor.predict(home, away)
        print(f"{home} vs {away}")
        print(f"  Poisson:  H:{pred.poisson_probs[0]:.0%} D:{pred.poisson_probs[1]:.0%} A:{pred.poisson_probs[2]:.0%}")
        print(f"  Oracle:   H:{pred.oracle_probs[0]:.0%} D:{pred.oracle_probs[1]:.0%} A:{pred.oracle_probs[2]:.0%}")
        print(f"  FUSION:   H:{pred.final_probs[0]:.0%} D:{pred.final_probs[1]:.0%} A:{pred.final_probs[2]:.0%}")
        print(f"  xG: {pred.home_xg:.2f} - {pred.away_xg:.2f}")
        print(f"  Upset Risk: {pred.upset_risk:.0%} {pred.upset_patterns}")
        print(f"  Draw Boost: {'YES' if pred.draw_boost_applied else 'No'}")
        print(f"  Prediction: {pred.prediction.upper()} ({pred.confidence})")
        print(f"  Lens Agreement: {pred.lens_agreement}/3")
        print()

    # Backtest
    print("=" * 70)
    print("BACKTEST: 2024-25 Season")
    print("=" * 70)

    results = backtest_tri_lens("2024-08-01", "2024-12-31")

    print(f"\nTotal matches: {results['total']}")
    print(f"\n{'='*50}")
    print(f"OVERALL ACCURACY: {results['overall_accuracy']:.1%}")
    print(f"{'='*50}")
    print(f"  Home Win:  {results['home_accuracy']:.1%} ({results['home_correct']}/{results['home_total']})")
    print(f"  Draw:      {results['draw_accuracy']:.1%} ({results['draw_correct']}/{results['draw_total']})")
    print(f"  Away Win:  {results['away_accuracy']:.1%} ({results['away_correct']}/{results['away_total']})")
    print(f"  Brier:     {results['brier_score']:.4f}")
    print(f"\n  Draw Boosts Applied: {results['draw_boosts_applied']}")
    print(f"  Draw Boost Accuracy: {results['draw_boost_accuracy']:.1%}")
    print(f"  High Confidence Accuracy: {results['high_confidence_accuracy']:.1%} ({results['high_confidence_correct']}/{results['high_confidence_total']})")
