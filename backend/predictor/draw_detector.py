"""
Soccer Predictor v3.0 - Draw Detection Module
==============================================
Uses Third Knowledge patterns to detect when draws are likely.

The power rating system achieves 58.6% accuracy but 0% on draws.
This module adds draw-specific pattern detection.

Third Knowledge Patterns:
1. close_matchup - Power diff < 10 = evenly matched
2. midtable_clash - Both teams in positions 8-15
3. fatigue_x_fatigue - Both teams played recently
4. defensive_matchup - Both teams have low goal averages
5. parked_bus_risk - Big favorite vs defensive underdog
6. derby_caution - Rivalry matches tend toward draws
"""

from dataclasses import dataclass
from typing import Optional
from team_ratings import TeamRatingSystem


@dataclass
class DrawPattern:
    """A single Third Knowledge pattern for draw detection."""
    name: str
    triggered: bool
    confidence: float  # 0-1
    multiplier: float  # How much to boost draw probability
    reason: str


@dataclass
class DrawAnalysis:
    """Complete draw analysis for a match."""
    home_team: str
    away_team: str
    base_draw_prob: float  # From power ratings
    patterns_triggered: list  # List of DrawPattern
    adjusted_draw_prob: float  # After applying patterns
    should_predict_draw: bool  # Final recommendation
    explanation: str


# Team classifications for pattern detection
MIDTABLE_TEAMS = {
    "brentford", "fulham", "crystal_palace", "wolves", "bournemouth",
    "nottingham_forest", "everton", "west_ham", "brighton"
}

DEFENSIVE_TEAMS = {
    "crystal_palace", "wolves", "everton", "nottingham_forest",
    "southampton", "ipswich", "leicester"
}

TOP_TEAMS = {
    "manchester_city", "arsenal", "liverpool", "chelsea",
    "tottenham", "manchester_united", "newcastle", "aston_villa"
}

RELEGATION_TEAMS = {
    "southampton", "ipswich", "leicester", "everton"
}

# Derby/rivalry pairs (both directions)
DERBIES = {
    ("liverpool", "everton"),
    ("manchester_united", "manchester_city"),
    ("arsenal", "tottenham"),
    ("west_ham", "tottenham"),
    ("crystal_palace", "brighton"),
    ("aston_villa", "wolves"),
    ("newcastle", "sunderland"),  # Not in PL but example
}


def is_derby(home: str, away: str) -> bool:
    """Check if match is a derby/rivalry."""
    pair1 = (home, away)
    pair2 = (away, home)
    return pair1 in DERBIES or pair2 in DERBIES


def check_close_matchup(power_diff: float) -> DrawPattern:
    """Pattern: Evenly matched teams (power diff < 10)."""
    is_close = abs(power_diff) < 10

    # Closer = higher confidence
    if is_close:
        confidence = 1.0 - (abs(power_diff) / 10)  # 0.0 at diff=10, 1.0 at diff=0
        multiplier = 1.3 + (0.5 * confidence)  # 1.3x to 1.8x
    else:
        confidence = 0.0
        multiplier = 1.0

    return DrawPattern(
        name="close_matchup",
        triggered=is_close,
        confidence=confidence,
        multiplier=multiplier,
        reason=f"Power diff {power_diff:+.1f} - evenly matched" if is_close else ""
    )


def check_midtable_clash(home: str, away: str) -> DrawPattern:
    """Pattern: Both teams are mid-table (positions 8-15)."""
    home_midtable = home in MIDTABLE_TEAMS
    away_midtable = away in MIDTABLE_TEAMS
    both_midtable = home_midtable and away_midtable

    # Either midtable also has effect, but weaker
    if both_midtable:
        confidence = 0.8
        multiplier = 1.4
        reason = "Both teams mid-table - lower stakes"
    elif home_midtable or away_midtable:
        confidence = 0.4
        multiplier = 1.15
        reason = "One team mid-table"
    else:
        confidence = 0.0
        multiplier = 1.0
        reason = ""

    return DrawPattern(
        name="midtable_clash",
        triggered=both_midtable or (home_midtable or away_midtable),
        confidence=confidence,
        multiplier=multiplier,
        reason=reason
    )


def check_defensive_matchup(home: str, away: str) -> DrawPattern:
    """Pattern: Both teams play defensively."""
    home_defensive = home in DEFENSIVE_TEAMS
    away_defensive = away in DEFENSIVE_TEAMS
    both_defensive = home_defensive and away_defensive

    if both_defensive:
        confidence = 0.7
        multiplier = 1.35
        reason = "Both teams defensive - expect low scoring"
    elif home_defensive or away_defensive:
        confidence = 0.3
        multiplier = 1.1
        reason = "One team defensive"
    else:
        confidence = 0.0
        multiplier = 1.0
        reason = ""

    return DrawPattern(
        name="defensive_matchup",
        triggered=both_defensive,
        confidence=confidence,
        multiplier=multiplier,
        reason=reason
    )


def check_parked_bus_risk(home: str, away: str, power_diff: float) -> DrawPattern:
    """
    Pattern: Big favorite vs defensive underdog.

    When power diff > 25 and underdog is defensive, they might
    park the bus and steal a 0-0 or 1-1 draw.
    """
    is_big_favorite = abs(power_diff) > 25

    if not is_big_favorite:
        return DrawPattern(
            name="parked_bus_risk",
            triggered=False,
            confidence=0.0,
            multiplier=1.0,
            reason=""
        )

    # Determine underdog
    if power_diff > 0:
        underdog = away
    else:
        underdog = home

    underdog_defensive = underdog in DEFENSIVE_TEAMS

    if underdog_defensive:
        confidence = 0.6
        multiplier = 1.25
        reason = f"{underdog} likely to park the bus vs big favorite"
    else:
        confidence = 0.0
        multiplier = 1.0
        reason = ""

    return DrawPattern(
        name="parked_bus_risk",
        triggered=underdog_defensive,
        confidence=confidence,
        multiplier=multiplier,
        reason=reason
    )


def check_derby_caution(home: str, away: str) -> DrawPattern:
    """Pattern: Derby matches tend to be cagey."""
    is_derby_match = is_derby(home, away)

    if is_derby_match:
        confidence = 0.7
        multiplier = 1.3
        reason = "Derby match - both teams cautious"
    else:
        confidence = 0.0
        multiplier = 1.0
        reason = ""

    return DrawPattern(
        name="derby_caution",
        triggered=is_derby_match,
        confidence=confidence,
        multiplier=multiplier,
        reason=reason
    )


def check_top_vs_top(home: str, away: str) -> DrawPattern:
    """Pattern: Top 6 clashes often end in draws."""
    home_top = home in TOP_TEAMS
    away_top = away in TOP_TEAMS
    both_top = home_top and away_top

    if both_top:
        confidence = 0.6
        multiplier = 1.25
        reason = "Top teams clash - tactical battle"
    else:
        confidence = 0.0
        multiplier = 1.0
        reason = ""

    return DrawPattern(
        name="top_vs_top",
        triggered=both_top,
        confidence=confidence,
        multiplier=multiplier,
        reason=reason
    )


def analyze_draw_probability(
    home_team: str,
    away_team: str,
    base_draw_prob: float,
    power_diff: float,
    draw_threshold: float = 0.30  # Predict draw if prob > 30%
) -> DrawAnalysis:
    """
    Complete draw analysis using Third Knowledge patterns.

    Args:
        home_team: Home team ID
        away_team: Away team ID
        base_draw_prob: Draw probability from power ratings (0-1)
        power_diff: Home power - Away power
        draw_threshold: Threshold for predicting draw

    Returns:
        DrawAnalysis with adjusted probability and recommendation
    """
    patterns = []

    # Check all patterns
    patterns.append(check_close_matchup(power_diff))
    patterns.append(check_midtable_clash(home_team, away_team))
    patterns.append(check_defensive_matchup(home_team, away_team))
    patterns.append(check_parked_bus_risk(home_team, away_team, power_diff))
    patterns.append(check_derby_caution(home_team, away_team))
    patterns.append(check_top_vs_top(home_team, away_team))

    # Calculate adjusted probability
    triggered = [p for p in patterns if p.triggered]

    if triggered:
        # Combine multipliers (weighted by confidence)
        total_boost = 0.0
        total_weight = 0.0

        for p in triggered:
            total_boost += (p.multiplier - 1.0) * p.confidence
            total_weight += p.confidence

        if total_weight > 0:
            avg_boost = 1.0 + (total_boost / total_weight)
        else:
            avg_boost = 1.0

        adjusted_prob = min(0.45, base_draw_prob * avg_boost)  # Cap at 45%
    else:
        adjusted_prob = base_draw_prob

    # Build explanation
    if triggered:
        explanations = [p.reason for p in triggered if p.reason]
        explanation = " | ".join(explanations)
    else:
        explanation = "No draw patterns detected"

    return DrawAnalysis(
        home_team=home_team,
        away_team=away_team,
        base_draw_prob=base_draw_prob,
        patterns_triggered=triggered,
        adjusted_draw_prob=adjusted_prob,
        should_predict_draw=(adjusted_prob > draw_threshold),
        explanation=explanation
    )


def enhanced_predict(
    system: TeamRatingSystem,
    home_team: str,
    away_team: str,
    draw_threshold: float = 0.32  # Tuned: best accuracy at 62.9%
) -> dict:
    """
    Enhanced prediction with Third Knowledge draw detection.

    Combines power rating prediction with draw pattern analysis.
    """
    # Get base prediction from power ratings
    base_pred = system.predict_match(home_team, away_team)

    if "error" in base_pred:
        return base_pred

    # Analyze draw probability
    base_draw = base_pred["draw"] / 100
    power_diff = base_pred["power_diff"]

    draw_analysis = analyze_draw_probability(
        home_team, away_team, base_draw, power_diff, draw_threshold
    )

    # Adjust probabilities if draw patterns detected
    if draw_analysis.patterns_triggered:
        # Boost draw, reduce win probabilities proportionally
        draw_boost = draw_analysis.adjusted_draw_prob - base_draw

        home_win = base_pred["home_win"] / 100
        away_win = base_pred["away_win"] / 100

        # Distribute boost from both win probabilities
        home_reduction = draw_boost * (home_win / (home_win + away_win))
        away_reduction = draw_boost * (away_win / (home_win + away_win))

        new_home = max(0.1, home_win - home_reduction)
        new_away = max(0.1, away_win - away_reduction)
        new_draw = draw_analysis.adjusted_draw_prob

        # Normalize
        total = new_home + new_draw + new_away
        new_home /= total
        new_draw /= total
        new_away /= total
    else:
        new_home = base_pred["home_win"] / 100
        new_draw = base_pred["draw"] / 100
        new_away = base_pred["away_win"] / 100

    # Determine prediction
    probs = {"home_win": new_home, "draw": new_draw, "away_win": new_away}
    prediction = max(probs, key=probs.get)

    # Override if draw analysis strongly suggests draw
    if draw_analysis.should_predict_draw and new_draw > 0.25:
        prediction = "draw"

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_win": round(new_home * 100, 1),
        "draw": round(new_draw * 100, 1),
        "away_win": round(new_away * 100, 1),
        "prediction": prediction,
        "power_diff": power_diff,
        "draw_patterns": len(draw_analysis.patterns_triggered),
        "draw_analysis": draw_analysis.explanation,
        "base_prediction": base_pred["prediction"],
        "third_knowledge_active": len(draw_analysis.patterns_triggered) > 0
    }


# === DEMO ===

if __name__ == "__main__":
    print("=" * 60)
    print("Draw Detection Module - Demo")
    print("=" * 60)

    system = TeamRatingSystem()
    system.initialize_premier_league_2024()

    # Test cases from missed draws in backtest
    test_matches = [
        ("nottingham_forest", "bournemouth"),  # Power diff -1.7, was draw
        ("manchester_city", "southampton"),     # Power diff +71.9, was draw!
        ("arsenal", "brighton"),                # Power diff +27.0, was draw
        ("crystal_palace", "leicester"),        # Power diff +8.1, was draw
        ("newcastle", "manchester_united"),     # Power diff +10.9, was draw
        # Control cases - should NOT predict draw
        ("manchester_city", "ipswich"),         # Big win expected
        ("liverpool", "southampton"),           # Big win expected
    ]

    print("\nAnalyzing matches for draw probability:\n")

    for home, away in test_matches:
        result = enhanced_predict(system, home, away)

        print(f"{home} vs {away}")
        print(f"  Prediction: {result['prediction'].upper()}")
        print(f"  Probabilities: H:{result['home_win']}% D:{result['draw']}% A:{result['away_win']}%")
        print(f"  Draw patterns: {result['draw_patterns']}")
        if result['draw_analysis']:
            print(f"  Analysis: {result['draw_analysis']}")
        print()
