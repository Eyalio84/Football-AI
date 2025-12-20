"""
Soccer Predictor v3.0 - Enhanced Backtest with Draw Detection
==============================================================
Compares power-rating-only predictions vs Third Knowledge enhanced.

Expected improvement:
- Before: 58.6% accuracy, 0% draw detection
- After: Higher overall accuracy with draw detection
"""

from team_ratings import TeamRatingSystem
from draw_detector import enhanced_predict

# 2024-25 Premier League Results (Matchweek 1-7)
ACTUAL_RESULTS = [
    # Matchweek 1
    ("manchester_united", "fulham", "H"),
    ("ipswich", "liverpool", "A"),
    ("arsenal", "wolves", "H"),
    ("everton", "brighton", "A"),
    ("newcastle", "southampton", "H"),
    ("nottingham_forest", "bournemouth", "D"),
    ("west_ham", "aston_villa", "A"),
    ("brentford", "crystal_palace", "D"),
    ("chelsea", "manchester_city", "D"),
    ("leicester", "tottenham", "A"),

    # Matchweek 2
    ("brighton", "manchester_united", "D"),
    ("crystal_palace", "west_ham", "A"),
    ("fulham", "leicester", "D"),
    ("manchester_city", "ipswich", "H"),
    ("southampton", "nottingham_forest", "A"),
    ("tottenham", "everton", "H"),
    ("aston_villa", "arsenal", "D"),
    ("bournemouth", "newcastle", "A"),
    ("wolves", "chelsea", "A"),
    ("liverpool", "brentford", "H"),

    # Matchweek 3
    ("arsenal", "brighton", "D"),
    ("brentford", "southampton", "H"),
    ("everton", "bournemouth", "D"),
    ("ipswich", "fulham", "D"),
    ("leicester", "aston_villa", "A"),
    ("nottingham_forest", "wolves", "H"),
    ("west_ham", "manchester_city", "A"),
    ("chelsea", "crystal_palace", "H"),
    ("manchester_united", "liverpool", "A"),
    ("newcastle", "tottenham", "D"),

    # Matchweek 4
    ("brighton", "ipswich", "H"),
    ("fulham", "west_ham", "D"),
    ("southampton", "manchester_united", "A"),
    ("tottenham", "arsenal", "D"),
    ("bournemouth", "chelsea", "A"),
    ("aston_villa", "everton", "H"),
    ("crystal_palace", "leicester", "D"),
    ("manchester_city", "brentford", "H"),
    ("wolves", "newcastle", "A"),
    ("liverpool", "nottingham_forest", "H"),

    # Matchweek 5
    ("aston_villa", "wolves", "H"),
    ("bournemouth", "southampton", "H"),
    ("arsenal", "leicester", "H"),
    ("brentford", "tottenham", "A"),
    ("chelsea", "brighton", "H"),
    ("everton", "crystal_palace", "D"),
    ("manchester_city", "arsenal", "D"),
    ("nottingham_forest", "liverpool", "H"),
    ("west_ham", "chelsea", "A"),
    ("manchester_united", "tottenham", "A"),

    # Matchweek 6
    ("brighton", "nottingham_forest", "D"),
    ("crystal_palace", "manchester_united", "D"),
    ("ipswich", "aston_villa", "A"),
    ("leicester", "everton", "A"),
    ("southampton", "bournemouth", "A"),
    ("tottenham", "brentford", "H"),
    ("wolves", "liverpool", "A"),
    ("fulham", "newcastle", "H"),
    ("arsenal", "southampton", "H"),
    ("manchester_city", "newcastle", "H"),

    # Matchweek 7
    ("aston_villa", "manchester_united", "D"),
    ("bournemouth", "arsenal", "A"),
    ("brighton", "tottenham", "H"),
    ("everton", "newcastle", "D"),
    ("leicester", "bournemouth", "A"),
    ("nottingham_forest", "crystal_palace", "H"),
    ("southampton", "ipswich", "D"),
    ("west_ham", "ipswich", "H"),
    ("manchester_city", "southampton", "D"),
    ("brentford", "wolves", "D"),
]


def run_backtest():
    """Run backtest with both prediction methods."""
    system = TeamRatingSystem()
    system.initialize_premier_league_2024()

    # Track results for both methods
    results = {
        "base": {"correct": 0, "total": 0, "by_actual": {"H": [0,0], "D": [0,0], "A": [0,0]}},
        "enhanced": {"correct": 0, "total": 0, "by_actual": {"H": [0,0], "D": [0,0], "A": [0,0]}}
    }

    draw_stats = {
        "actual_draws": 0,
        "base_predicted_draws": 0,
        "enhanced_predicted_draws": 0,
        "base_correct_draws": 0,
        "enhanced_correct_draws": 0,
        "false_positives": 0,  # Enhanced predicted draw but wasn't
    }

    print("=" * 70)
    print("Enhanced Backtest: Power Ratings vs Third Knowledge Draw Detection")
    print("=" * 70)
    print()

    for home, away, actual in ACTUAL_RESULTS:
        # Base prediction (power ratings only)
        base_pred = system.predict_match(home, away)
        if "error" in base_pred:
            continue

        # Enhanced prediction (with draw patterns)
        enhanced_pred = enhanced_predict(system, home, away)
        if "error" in enhanced_pred:
            continue

        # Map predictions to H/D/A
        base_result = "H" if base_pred["prediction"] == "home_win" else \
                     "A" if base_pred["prediction"] == "away_win" else "D"

        enhanced_result = "H" if enhanced_pred["prediction"] == "home_win" else \
                         "A" if enhanced_pred["prediction"] == "away_win" else "D"

        # Track totals
        results["base"]["total"] += 1
        results["enhanced"]["total"] += 1

        # Track accuracy by actual result
        results["base"]["by_actual"][actual][1] += 1
        results["enhanced"]["by_actual"][actual][1] += 1

        if base_result == actual:
            results["base"]["correct"] += 1
            results["base"]["by_actual"][actual][0] += 1

        if enhanced_result == actual:
            results["enhanced"]["correct"] += 1
            results["enhanced"]["by_actual"][actual][0] += 1

        # Track draw-specific stats
        if actual == "D":
            draw_stats["actual_draws"] += 1

        if base_result == "D":
            draw_stats["base_predicted_draws"] += 1
            if actual == "D":
                draw_stats["base_correct_draws"] += 1

        if enhanced_result == "D":
            draw_stats["enhanced_predicted_draws"] += 1
            if actual == "D":
                draw_stats["enhanced_correct_draws"] += 1
            else:
                draw_stats["false_positives"] += 1

        # Show changed predictions
        if base_result != enhanced_result:
            status = "✓" if enhanced_result == actual else "✗"
            pattern_info = f"[{enhanced_pred['draw_patterns']} patterns]" if enhanced_pred.get('third_knowledge_active') else ""
            print(f"{status} {home} vs {away}: {base_result} → {enhanced_result} (actual: {actual}) {pattern_info}")

    print()
    print("=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)

    # Overall accuracy
    base_acc = results["base"]["correct"] / results["base"]["total"] * 100
    enhanced_acc = results["enhanced"]["correct"] / results["enhanced"]["total"] * 100

    print(f"\n{'Method':<20} {'Correct':>10} {'Total':>10} {'Accuracy':>12}")
    print("-" * 55)
    print(f"{'Power Ratings Only':<20} {results['base']['correct']:>10} {results['base']['total']:>10} {base_acc:>11.1f}%")
    print(f"{'+ Third Knowledge':<20} {results['enhanced']['correct']:>10} {results['enhanced']['total']:>10} {enhanced_acc:>11.1f}%")

    diff = enhanced_acc - base_acc
    print(f"\n{'Improvement:':<20} {'+' if diff >= 0 else ''}{diff:.1f}%")

    # Accuracy by actual result
    print(f"\n{'Accuracy by Actual Result':}")
    print("-" * 55)
    print(f"{'Actual':<10} {'Base':>15} {'Enhanced':>15} {'Change':>12}")

    for result_type, label in [("H", "Home Win"), ("D", "Draw"), ("A", "Away Win")]:
        base_c, base_t = results["base"]["by_actual"][result_type]
        enh_c, enh_t = results["enhanced"]["by_actual"][result_type]

        base_pct = (base_c / base_t * 100) if base_t > 0 else 0
        enh_pct = (enh_c / enh_t * 100) if enh_t > 0 else 0
        change = enh_pct - base_pct

        print(f"{label:<10} {base_c}/{base_t} ({base_pct:>5.1f}%) {enh_c}/{enh_t} ({enh_pct:>5.1f}%) {'+' if change >= 0 else ''}{change:>5.1f}%")

    # Draw detection stats
    print(f"\n{'Draw Detection Analysis':}")
    print("-" * 55)
    print(f"Actual draws in dataset: {draw_stats['actual_draws']}")
    print(f"Base predicted draws: {draw_stats['base_predicted_draws']} (correct: {draw_stats['base_correct_draws']})")
    print(f"Enhanced predicted draws: {draw_stats['enhanced_predicted_draws']} (correct: {draw_stats['enhanced_correct_draws']})")
    print(f"False positives (predicted draw, wasn't): {draw_stats['false_positives']}")

    # Draw precision/recall
    if draw_stats["enhanced_predicted_draws"] > 0:
        precision = draw_stats["enhanced_correct_draws"] / draw_stats["enhanced_predicted_draws"] * 100
        print(f"\nDraw Precision: {precision:.1f}% (of predicted draws, how many were correct)")

    if draw_stats["actual_draws"] > 0:
        recall = draw_stats["enhanced_correct_draws"] / draw_stats["actual_draws"] * 100
        print(f"Draw Recall: {recall:.1f}% (of actual draws, how many did we catch)")

    print()
    print("=" * 70)

    return {
        "base_accuracy": base_acc,
        "enhanced_accuracy": enhanced_acc,
        "improvement": diff,
        "draw_stats": draw_stats
    }


if __name__ == "__main__":
    run_backtest()
