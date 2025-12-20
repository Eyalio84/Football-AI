"""
Meta-Predictor Backtest: Validating the Combination of Oracle + Third Knowledge
================================================================================

This script tests different strategies for combining:
- Hybrid Oracle (win probability predictor)
- Third Knowledge (upset probability predictor)

Strategies tested:
1. Oracle Only (baseline)
2. Simple Average
3. Weighted Ensemble
4. Confidence-Adjusted
5. Conditional Routing (boost draw when upset risk high)

Goal: Find the optimal combination that maximizes prediction accuracy.
"""

import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import math

# Import our predictors
from hybrid_oracle import HybridOracle, normalize_team_name, DB_PATH
from statistical_predictor import FootballOracle

# Database
DB_PATH_FULL = Path(__file__).parent.parent / "unified_soccer_ai_kg.db"


@dataclass
class MetaPrediction:
    """Combined prediction from multiple sources."""
    home_team: str
    away_team: str

    # Oracle probabilities
    oracle_home: float
    oracle_draw: float
    oracle_away: float
    oracle_prediction: str

    # Upset analysis (simulated from oracle disagreement)
    upset_risk: float
    upset_patterns: List[str]

    # Combined predictions by strategy
    strategy_predictions: Dict[str, str]
    strategy_probs: Dict[str, Tuple[float, float, float]]

    # Final recommendation
    recommended_prediction: str
    confidence: str


def calculate_upset_risk(oracle_pred, home_team: str, away_team: str) -> Tuple[float, List[str]]:
    """
    Calculate upset risk based on Oracle analysis.

    Upset risk is higher when:
    1. Match is close (small probability gap)
    2. Away team has better form
    3. Power difference is in the "paradox zone" (30-60 ELO)
    """
    patterns = []
    risk_score = 0.0

    # Factor 1: Probability gap (closer = higher upset risk)
    prob_gap = abs(oracle_pred.home_win_prob - oracle_pred.away_win_prob)
    if prob_gap < 0.10:
        risk_score += 0.25
        patterns.append("Very Close Match")
    elif prob_gap < 0.20:
        risk_score += 0.15
        patterns.append("Close Match")

    # Factor 2: Power difference in paradox zone
    power_diff = abs(oracle_pred.power_diff)
    if 5 <= power_diff <= 12:
        risk_score += 0.20
        patterns.append("ELO Paradox Zone")

    # Factor 3: Draw probability already high
    if oracle_pred.draw_prob > 0.25:
        risk_score += 0.15
        patterns.append("High Draw Signal")

    # Factor 4: Away team stronger (home upset)
    if oracle_pred.power_diff < -5:
        risk_score += 0.10
        patterns.append("Away Team Stronger")

    # Factor 5: Form disagreement (from draw_factors)
    for factor in oracle_pred.draw_factors:
        if "away_much_better" in factor.lower():
            risk_score += 0.15
            patterns.append("Away Better Form")
            break

    return min(0.8, risk_score), patterns


def strategy_oracle_only(oracle_pred) -> Tuple[str, Tuple[float, float, float]]:
    """Baseline: Use Oracle prediction directly."""
    return oracle_pred.prediction, (
        oracle_pred.home_win_prob,
        oracle_pred.draw_prob,
        oracle_pred.away_win_prob
    )


def strategy_simple_average(oracle_pred, upset_risk: float) -> Tuple[str, Tuple[float, float, float]]:
    """
    Simple average: Reduce favorite probability by upset risk.
    Distribute to draw and underdog.
    """
    home = oracle_pred.home_win_prob
    draw = oracle_pred.draw_prob
    away = oracle_pred.away_win_prob

    # Determine favorite
    if home > away:
        favorite_reduction = home * upset_risk * 0.3
        home -= favorite_reduction
        draw += favorite_reduction * 0.6
        away += favorite_reduction * 0.4
    else:
        favorite_reduction = away * upset_risk * 0.3
        away -= favorite_reduction
        draw += favorite_reduction * 0.6
        home += favorite_reduction * 0.4

    # Normalize
    total = home + draw + away
    home, draw, away = home/total, draw/total, away/total

    # Prediction
    probs = {"home_win": home, "draw": draw, "away_win": away}
    prediction = max(probs, key=probs.get)

    return prediction, (home, draw, away)


def strategy_weighted_ensemble(oracle_pred, upset_risk: float) -> Tuple[str, Tuple[float, float, float]]:
    """
    Weighted ensemble: Weight oracle by (1 - upset_risk).
    """
    oracle_weight = 1 - (upset_risk * 0.5)  # Max 50% reduction

    home = oracle_pred.home_win_prob * oracle_weight
    draw = oracle_pred.draw_prob + (upset_risk * 0.15)  # Boost draw
    away = oracle_pred.away_win_prob + (upset_risk * 0.10)  # Slight underdog boost

    # Normalize
    total = home + draw + away
    home, draw, away = home/total, draw/total, away/total

    probs = {"home_win": home, "draw": draw, "away_win": away}
    prediction = max(probs, key=probs.get)

    return prediction, (home, draw, away)


def strategy_confidence_adjusted(oracle_pred, upset_risk: float) -> Tuple[str, Tuple[float, float, float]]:
    """
    Confidence adjusted: Only change prediction if upset risk > threshold
    and match is close.
    """
    home = oracle_pred.home_win_prob
    draw = oracle_pred.draw_prob
    away = oracle_pred.away_win_prob
    prob_gap = abs(home - away)

    # If high upset risk AND close match, boost draw significantly
    if upset_risk > 0.35 and prob_gap < 0.15:
        draw_boost = 0.12
        draw += draw_boost
        home -= draw_boost * 0.5
        away -= draw_boost * 0.5
    elif upset_risk > 0.25:
        draw_boost = 0.06
        draw += draw_boost
        home -= draw_boost * 0.5
        away -= draw_boost * 0.5

    # Normalize
    total = home + draw + away
    home, draw, away = home/total, draw/total, away/total

    probs = {"home_win": home, "draw": draw, "away_win": away}
    prediction = max(probs, key=probs.get)

    return prediction, (home, draw, away)


def strategy_conditional_routing(oracle_pred, upset_risk: float, patterns: List[str]) -> Tuple[str, Tuple[float, float, float]]:
    """
    Conditional routing: Different logic based on upset patterns.
    """
    home = oracle_pred.home_win_prob
    draw = oracle_pred.draw_prob
    away = oracle_pred.away_win_prob

    # Special handling based on patterns
    if "ELO Paradox Zone" in patterns and "Close Match" in patterns:
        # Strong draw signal
        draw += 0.15
        home -= 0.08
        away -= 0.07
    elif "Away Better Form" in patterns and "Away Team Stronger" in patterns:
        # Away likely to win
        away += 0.10
        home -= 0.10
    elif upset_risk > 0.40:
        # General upset risk - boost draw
        draw += 0.10
        home -= 0.05
        away -= 0.05

    # Clamp and normalize
    home = max(0.05, home)
    draw = max(0.10, draw)
    away = max(0.05, away)
    total = home + draw + away
    home, draw, away = home/total, draw/total, away/total

    probs = {"home_win": home, "draw": draw, "away_win": away}
    prediction = max(probs, key=probs.get)

    return prediction, (home, draw, away)


def strategy_draw_boost_threshold(oracle_pred, upset_risk: float) -> Tuple[str, Tuple[float, float, float]]:
    """
    Draw boost with threshold: If upset_risk > 0.3 AND draw_prob > 0.22,
    predict draw.
    """
    home = oracle_pred.home_win_prob
    draw = oracle_pred.draw_prob
    away = oracle_pred.away_win_prob
    prob_gap = abs(home - away)

    # Explicit draw prediction when conditions align
    if upset_risk > 0.30 and draw > 0.22 and prob_gap < 0.12:
        prediction = "draw"
        draw += 0.08
        home -= 0.04
        away -= 0.04
    else:
        probs = {"home_win": home, "draw": draw, "away_win": away}
        prediction = max(probs, key=probs.get)

    # Normalize
    total = home + draw + away
    home, draw, away = home/total, draw/total, away/total

    return prediction, (home, draw, away)


def backtest_meta_predictor(
    start_date: str = "2024-08-01",
    end_date: str = "2024-12-31"
) -> Dict:
    """
    Backtest all meta-predictor strategies against historical matches.
    """
    print("=" * 70)
    print("META-PREDICTOR BACKTEST")
    print("Combining Oracle + Third Knowledge Analysis")
    print("=" * 70)

    oracle = HybridOracle(DB_PATH_FULL)

    conn = sqlite3.connect(DB_PATH_FULL)
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

    if not matches:
        return {"error": "No matches found"}

    # Results tracking
    strategies = [
        "oracle_only",
        "simple_average",
        "weighted_ensemble",
        "confidence_adjusted",
        "conditional_routing",
        "draw_boost_threshold"
    ]

    results = {s: {
        "total": 0, "correct": 0,
        "home_correct": 0, "home_total": 0,
        "draw_correct": 0, "draw_total": 0,
        "away_correct": 0, "away_total": 0,
        "brier_sum": 0.0
    } for s in strategies}

    result_map = {"H": "home_win", "D": "draw", "A": "away_win"}

    print(f"\nProcessing {len(matches)} matches...")

    for i, match in enumerate(matches):
        home, away, home_score, away_score, actual_result, h_odds, d_odds, a_odds = match

        if actual_result not in result_map:
            continue

        actual = result_map[actual_result]

        # Get Oracle prediction
        try:
            oracle_pred = oracle.predict(home, away, h_odds, d_odds, a_odds)
        except Exception as e:
            continue

        # Calculate upset risk
        upset_risk, patterns = calculate_upset_risk(oracle_pred, home, away)

        # Test each strategy
        strategy_results = {
            "oracle_only": strategy_oracle_only(oracle_pred),
            "simple_average": strategy_simple_average(oracle_pred, upset_risk),
            "weighted_ensemble": strategy_weighted_ensemble(oracle_pred, upset_risk),
            "confidence_adjusted": strategy_confidence_adjusted(oracle_pred, upset_risk),
            "conditional_routing": strategy_conditional_routing(oracle_pred, upset_risk, patterns),
            "draw_boost_threshold": strategy_draw_boost_threshold(oracle_pred, upset_risk),
        }

        # Score each strategy
        for strategy_name, (prediction, probs) in strategy_results.items():
            r = results[strategy_name]
            r["total"] += 1

            correct = prediction == actual
            if correct:
                r["correct"] += 1

            # By outcome type
            if actual == "home_win":
                r["home_total"] += 1
                if correct:
                    r["home_correct"] += 1
            elif actual == "draw":
                r["draw_total"] += 1
                if correct:
                    r["draw_correct"] += 1
            elif actual == "away_win":
                r["away_total"] += 1
                if correct:
                    r["away_correct"] += 1

            # Brier score
            actual_vec = [1 if actual == "home_win" else 0,
                         1 if actual == "draw" else 0,
                         1 if actual == "away_win" else 0]
            brier = sum((p - a) ** 2 for p, a in zip(probs, actual_vec))
            r["brier_sum"] += brier

        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(matches)} matches...")

    # Calculate final metrics
    print("\n" + "=" * 70)
    print("RESULTS BY STRATEGY")
    print("=" * 70)

    summary = []

    for strategy in strategies:
        r = results[strategy]
        if r["total"] == 0:
            continue

        overall = r["correct"] / r["total"]
        home_acc = r["home_correct"] / r["home_total"] if r["home_total"] > 0 else 0
        draw_acc = r["draw_correct"] / r["draw_total"] if r["draw_total"] > 0 else 0
        away_acc = r["away_correct"] / r["away_total"] if r["away_total"] > 0 else 0
        brier = r["brier_sum"] / r["total"]

        summary.append({
            "strategy": strategy,
            "overall": overall,
            "home": home_acc,
            "draw": draw_acc,
            "away": away_acc,
            "brier": brier,
            "draw_detected": r["draw_correct"],
            "draw_total": r["draw_total"]
        })

        print(f"\n{strategy.upper().replace('_', ' ')}")
        print(f"  Overall:  {overall:.1%} ({r['correct']}/{r['total']})")
        print(f"  Home:     {home_acc:.1%} ({r['home_correct']}/{r['home_total']})")
        print(f"  Draw:     {draw_acc:.1%} ({r['draw_correct']}/{r['draw_total']})")
        print(f"  Away:     {away_acc:.1%} ({r['away_correct']}/{r['away_total']})")
        print(f"  Brier:    {brier:.4f}")

    # Find best strategy
    print("\n" + "=" * 70)
    print("RANKING (by Overall Accuracy)")
    print("=" * 70)

    summary.sort(key=lambda x: x["overall"], reverse=True)
    for i, s in enumerate(summary, 1):
        print(f"{i}. {s['strategy']:25} {s['overall']:.1%} (Draw: {s['draw']:.1%}, Brier: {s['brier']:.4f})")

    return {
        "strategies": summary,
        "best_strategy": summary[0]["strategy"] if summary else None,
        "best_overall": summary[0]["overall"] if summary else 0,
        "matches_tested": results["oracle_only"]["total"]
    }


if __name__ == "__main__":
    results = backtest_meta_predictor("2024-08-01", "2024-12-31")

    print("\n" + "=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print(f"Best Strategy: {results['best_strategy']}")
    print(f"Best Accuracy: {results['best_overall']:.1%}")
    print(f"Matches Tested: {results['matches_tested']}")
