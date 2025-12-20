"""
Third Knowledge: Tune Draw Detection Threshold
================================================
Finds optimal threshold by testing multiple values.
"""

from team_ratings import TeamRatingSystem
from draw_detector import enhanced_predict

ACTUAL_RESULTS = [
    ("manchester_united", "fulham", "H"), ("ipswich", "liverpool", "A"),
    ("arsenal", "wolves", "H"), ("everton", "brighton", "A"),
    ("newcastle", "southampton", "H"), ("nottingham_forest", "bournemouth", "D"),
    ("west_ham", "aston_villa", "A"), ("brentford", "crystal_palace", "D"),
    ("chelsea", "manchester_city", "D"), ("leicester", "tottenham", "A"),
    ("brighton", "manchester_united", "D"), ("crystal_palace", "west_ham", "A"),
    ("fulham", "leicester", "D"), ("manchester_city", "ipswich", "H"),
    ("southampton", "nottingham_forest", "A"), ("tottenham", "everton", "H"),
    ("aston_villa", "arsenal", "D"), ("bournemouth", "newcastle", "A"),
    ("wolves", "chelsea", "A"), ("liverpool", "brentford", "H"),
    ("arsenal", "brighton", "D"), ("brentford", "southampton", "H"),
    ("everton", "bournemouth", "D"), ("ipswich", "fulham", "D"),
    ("leicester", "aston_villa", "A"), ("nottingham_forest", "wolves", "H"),
    ("west_ham", "manchester_city", "A"), ("chelsea", "crystal_palace", "H"),
    ("manchester_united", "liverpool", "A"), ("newcastle", "tottenham", "D"),
    ("brighton", "ipswich", "H"), ("fulham", "west_ham", "D"),
    ("southampton", "manchester_united", "A"), ("tottenham", "arsenal", "D"),
    ("bournemouth", "chelsea", "A"), ("aston_villa", "everton", "H"),
    ("crystal_palace", "leicester", "D"), ("manchester_city", "brentford", "H"),
    ("wolves", "newcastle", "A"), ("liverpool", "nottingham_forest", "H"),
    ("aston_villa", "wolves", "H"), ("bournemouth", "southampton", "H"),
    ("arsenal", "leicester", "H"), ("brentford", "tottenham", "A"),
    ("chelsea", "brighton", "H"), ("everton", "crystal_palace", "D"),
    ("manchester_city", "arsenal", "D"), ("nottingham_forest", "liverpool", "H"),
    ("west_ham", "chelsea", "A"), ("manchester_united", "tottenham", "A"),
    ("brighton", "nottingham_forest", "D"), ("crystal_palace", "manchester_united", "D"),
    ("ipswich", "aston_villa", "A"), ("leicester", "everton", "A"),
    ("southampton", "bournemouth", "A"), ("tottenham", "brentford", "H"),
    ("wolves", "liverpool", "A"), ("fulham", "newcastle", "H"),
    ("arsenal", "southampton", "H"), ("manchester_city", "newcastle", "H"),
    ("aston_villa", "manchester_united", "D"), ("bournemouth", "arsenal", "A"),
    ("brighton", "tottenham", "H"), ("everton", "newcastle", "D"),
    ("leicester", "bournemouth", "A"), ("nottingham_forest", "crystal_palace", "H"),
    ("southampton", "ipswich", "D"), ("west_ham", "ipswich", "H"),
    ("manchester_city", "southampton", "D"), ("brentford", "wolves", "D"),
]


def test_threshold(threshold: float):
    """Test a specific threshold value."""
    system = TeamRatingSystem()
    system.initialize_premier_league_2024()

    correct = 0
    total = 0
    draw_correct = 0
    draw_predicted = 0
    actual_draws = 0
    false_positives = 0

    for home, away, actual in ACTUAL_RESULTS:
        pred = enhanced_predict(system, home, away, draw_threshold=threshold)
        if "error" in pred:
            continue

        result = "H" if pred["prediction"] == "home_win" else \
                 "A" if pred["prediction"] == "away_win" else "D"

        total += 1
        if result == actual:
            correct += 1

        if actual == "D":
            actual_draws += 1

        if result == "D":
            draw_predicted += 1
            if actual == "D":
                draw_correct += 1
            else:
                false_positives += 1

    accuracy = correct / total * 100
    precision = (draw_correct / draw_predicted * 100) if draw_predicted > 0 else 0
    recall = (draw_correct / actual_draws * 100) if actual_draws > 0 else 0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0

    return {
        "threshold": threshold,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "predicted": draw_predicted,
        "correct": draw_correct,
        "false_positives": false_positives
    }


def main():
    print("=" * 75)
    print("Third Knowledge: Draw Threshold Tuning")
    print("=" * 75)
    print()

    # Test range of thresholds
    thresholds = [0.25, 0.28, 0.30, 0.32, 0.34, 0.36, 0.38, 0.40]

    results = []
    for t in thresholds:
        r = test_threshold(t)
        results.append(r)

    # Print table
    print(f"{'Threshold':>10} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Predicted':>10} {'FalsePos':>10}")
    print("-" * 75)

    best_accuracy = None
    best_f1 = None

    for r in results:
        print(f"{r['threshold']:>10.2f} {r['accuracy']:>9.1f}% {r['precision']:>9.1f}% {r['recall']:>9.1f}% {r['f1']:>9.1f} {r['predicted']:>10} {r['false_positives']:>10}")

        if best_accuracy is None or r['accuracy'] > best_accuracy['accuracy']:
            best_accuracy = r
        if best_f1 is None or r['f1'] > best_f1['f1']:
            best_f1 = r

    print("-" * 75)
    print(f"\nBest for ACCURACY: threshold={best_accuracy['threshold']:.2f} → {best_accuracy['accuracy']:.1f}%")
    print(f"Best for F1 SCORE:  threshold={best_f1['threshold']:.2f} → F1={best_f1['f1']:.1f}")
    print()

    # Baseline comparison
    base_result = test_threshold(1.0)  # Threshold so high no draws predicted
    print(f"Baseline (no draw detection): {base_result['accuracy']:.1f}%")
    print(f"Best improvement: +{best_accuracy['accuracy'] - base_result['accuracy']:.1f}%")

    return best_accuracy


if __name__ == "__main__":
    main()
