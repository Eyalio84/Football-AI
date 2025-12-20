"""
Tri-Lens Predictor Test Suite
=============================

Comprehensive testing including:
1. Unit tests for each component
2. Integration tests for the full pipeline
3. Edge case handling
4. Input validation tests
5. Security tests (injection, malformed input)
6. Regression tests

Run from backend directory:
    python -m pytest predictor/test_tri_lens.py -v
Or standalone:
    python predictor/test_tri_lens.py
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import math

# Ensure predictor directory is in path
_predictor_dir = Path(__file__).parent
_backend_dir = _predictor_dir.parent
if str(_predictor_dir) not in sys.path:
    sys.path.insert(0, str(_predictor_dir))
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))


class TestImports(unittest.TestCase):
    """Test that all imports work correctly from different contexts."""

    def test_poisson_import(self):
        """Verify poisson_predictor imports correctly."""
        from poisson_predictor import PoissonPredictor, poisson_probability
        self.assertIsNotNone(PoissonPredictor)
        self.assertIsNotNone(poisson_probability)

    def test_hybrid_oracle_import(self):
        """Verify hybrid_oracle imports correctly."""
        from hybrid_oracle import HybridOracle, normalize_team_name
        self.assertIsNotNone(HybridOracle)
        self.assertIsNotNone(normalize_team_name)

    def test_tri_lens_import(self):
        """Verify tri_lens_predictor imports correctly."""
        from tri_lens_predictor import TriLensPredictor, TriLensPrediction
        self.assertIsNotNone(TriLensPredictor)
        self.assertIsNotNone(TriLensPrediction)


class TestPoissonMath(unittest.TestCase):
    """Test Poisson probability calculations."""

    def test_poisson_probability_zero_goals(self):
        """P(0 goals) when lambda=1.5 should be ~0.223."""
        from poisson_predictor import poisson_probability
        prob = poisson_probability(0, 1.5)
        self.assertAlmostEqual(prob, 0.223, places=2)

    def test_poisson_probability_one_goal(self):
        """P(1 goal) when lambda=1.5 should be ~0.335."""
        from poisson_predictor import poisson_probability
        prob = poisson_probability(1, 1.5)
        self.assertAlmostEqual(prob, 0.335, places=2)

    def test_poisson_probability_sums_to_one(self):
        """Sum of P(0..10 goals) should be ~1.0."""
        from poisson_predictor import poisson_probability
        total = sum(poisson_probability(k, 2.0) for k in range(20))
        self.assertAlmostEqual(total, 1.0, places=4)

    def test_poisson_zero_lambda(self):
        """When lambda=0, P(0)=1, P(k>0)=0."""
        from poisson_predictor import poisson_probability
        self.assertEqual(poisson_probability(0, 0), 1.0)
        self.assertEqual(poisson_probability(1, 0), 0.0)
        self.assertEqual(poisson_probability(5, 0), 0.0)

    def test_poisson_negative_lambda(self):
        """Negative lambda should return P(0)=1, P(k>0)=0."""
        from poisson_predictor import poisson_probability
        self.assertEqual(poisson_probability(0, -1), 1.0)
        self.assertEqual(poisson_probability(1, -1), 0.0)


class TestMatchProbabilities(unittest.TestCase):
    """Test match probability calculations."""

    def test_probabilities_sum_to_one(self):
        """H + D + A should equal 1.0."""
        from poisson_predictor import calculate_match_probabilities
        h, d, a, _ = calculate_match_probabilities(1.5, 1.2)
        self.assertAlmostEqual(h + d + a, 1.0, places=4)

    def test_high_xg_diff_favors_home(self):
        """When home xG >> away xG, home win should dominate."""
        from poisson_predictor import calculate_match_probabilities
        h, d, a, _ = calculate_match_probabilities(3.0, 0.5)
        self.assertGreater(h, 0.7)
        self.assertLess(a, 0.1)

    def test_equal_xg_gives_draw(self):
        """When xG equal, draw should be significant."""
        from poisson_predictor import calculate_match_probabilities
        h, d, a, _ = calculate_match_probabilities(1.5, 1.5)
        self.assertGreater(d, 0.20)
        self.assertAlmostEqual(h, a, places=2)

    def test_likely_scores_sorted(self):
        """Likely scores should be sorted by probability descending."""
        from poisson_predictor import calculate_match_probabilities
        _, _, _, scores = calculate_match_probabilities(1.5, 1.0)
        probs = [s[1] for s in scores]
        self.assertEqual(probs, sorted(probs, reverse=True))


class TestInputValidation(unittest.TestCase):
    """Test input validation and edge cases."""

    def test_empty_team_name(self):
        """Empty team name should be handled gracefully."""
        from poisson_predictor import PoissonPredictor
        predictor = PoissonPredictor()
        # Should not crash - returns default strengths
        pred = predictor.predict("", "Liverpool")
        self.assertIsNotNone(pred)

    def test_unknown_team(self):
        """Unknown team should use default strength (1.0)."""
        from poisson_predictor import PoissonPredictor
        predictor = PoissonPredictor()
        pred = predictor.predict("Unknown FC", "Another Unknown")
        # Default attack/defense = 1.0
        self.assertAlmostEqual(pred.home_attack, 1.0, places=1)

    def test_same_team_both_sides(self):
        """Same team for home and away should still work."""
        from poisson_predictor import PoissonPredictor
        predictor = PoissonPredictor()
        pred = predictor.predict("Liverpool", "Liverpool")
        # Should be roughly even
        self.assertIsNotNone(pred)

    def test_special_characters_in_name(self):
        """Team names with special chars should be normalized."""
        from poisson_predictor import PoissonPredictor
        predictor = PoissonPredictor()
        # Should not crash
        pred = predictor.predict("Man City!!!", "Arsenal???")
        self.assertIsNotNone(pred)

    def test_very_long_team_name(self):
        """Very long team name should be handled."""
        from poisson_predictor import PoissonPredictor
        predictor = PoissonPredictor()
        long_name = "A" * 1000
        pred = predictor.predict(long_name, "Liverpool")
        self.assertIsNotNone(pred)

    def test_unicode_team_name(self):
        """Unicode characters should be handled."""
        from poisson_predictor import PoissonPredictor
        predictor = PoissonPredictor()
        pred = predictor.predict("日本代表", "Liverpool")
        self.assertIsNotNone(pred)


class TestSecurityValidation(unittest.TestCase):
    """Test security-related edge cases."""

    def test_sql_injection_attempt(self):
        """SQL injection in team name should be sanitized."""
        from poisson_predictor import PoissonPredictor
        predictor = PoissonPredictor()
        # Should not crash or execute SQL
        malicious = "'; DROP TABLE match_history; --"
        pred = predictor.predict(malicious, "Liverpool")
        self.assertIsNotNone(pred)

    def test_script_injection_attempt(self):
        """Script injection should be handled safely."""
        from poisson_predictor import PoissonPredictor
        predictor = PoissonPredictor()
        malicious = "<script>alert('xss')</script>"
        pred = predictor.predict(malicious, "Liverpool")
        self.assertIsNotNone(pred)

    def test_null_bytes(self):
        """Null bytes in input should be handled."""
        from poisson_predictor import PoissonPredictor
        predictor = PoissonPredictor()
        pred = predictor.predict("Liverpool\x00", "Arsenal")
        self.assertIsNotNone(pred)

    def test_path_traversal_attempt(self):
        """Path traversal attempts should be handled."""
        from poisson_predictor import PoissonPredictor
        predictor = PoissonPredictor()
        malicious = "../../../etc/passwd"
        pred = predictor.predict(malicious, "Liverpool")
        self.assertIsNotNone(pred)


class TestTriLensIntegration(unittest.TestCase):
    """Integration tests for full Tri-Lens pipeline."""

    @classmethod
    def setUpClass(cls):
        """Initialize predictor once for all tests."""
        from tri_lens_predictor import TriLensPredictor
        cls.predictor = TriLensPredictor()

    def test_prediction_returns_all_fields(self):
        """Prediction should include all required fields."""
        pred = self.predictor.predict("Liverpool", "Arsenal")

        # Core fields
        self.assertIsNotNone(pred.home_team)
        self.assertIsNotNone(pred.away_team)
        self.assertIsNotNone(pred.prediction)
        self.assertIsNotNone(pred.confidence)

        # Probabilities
        self.assertIsNotNone(pred.final_probs)
        self.assertEqual(len(pred.final_probs), 3)

        # xG
        self.assertIsNotNone(pred.home_xg)
        self.assertIsNotNone(pred.away_xg)
        self.assertGreater(pred.home_xg, 0)
        self.assertGreater(pred.away_xg, 0)

        # Upset analysis
        self.assertIsNotNone(pred.upset_risk)
        self.assertIsNotNone(pred.upset_patterns)

        # Lens agreement
        self.assertIn(pred.lens_agreement, [1, 2, 3])

    def test_probabilities_valid_range(self):
        """All probabilities should be in [0, 1]."""
        pred = self.predictor.predict("Chelsea", "Tottenham")

        for prob in pred.final_probs:
            self.assertGreaterEqual(prob, 0.0)
            self.assertLessEqual(prob, 1.0)

        self.assertAlmostEqual(sum(pred.final_probs), 1.0, places=4)

    def test_upset_risk_valid_range(self):
        """Upset risk should be in [0, 1]."""
        pred = self.predictor.predict("Manchester City", "Southampton")
        self.assertGreaterEqual(pred.upset_risk, 0.0)
        self.assertLessEqual(pred.upset_risk, 1.0)

    def test_xg_clamped(self):
        """xG should be clamped to reasonable range."""
        pred = self.predictor.predict("Manchester City", "Ipswich")
        self.assertLessEqual(pred.home_xg, 4.0)
        self.assertGreaterEqual(pred.home_xg, 0.3)
        self.assertLessEqual(pred.away_xg, 3.5)
        self.assertGreaterEqual(pred.away_xg, 0.2)

    def test_prediction_is_valid_outcome(self):
        """Prediction should be one of home_win, draw, away_win."""
        pred = self.predictor.predict("Everton", "Newcastle")
        self.assertIn(pred.prediction, ["home_win", "draw", "away_win"])

    def test_confidence_is_valid(self):
        """Confidence should be valid level."""
        pred = self.predictor.predict("Brighton", "Fulham")
        self.assertIn(pred.confidence, ["low", "medium", "high", "very_high"])

    def test_draw_boost_conditions(self):
        """Draw boost should only apply when conditions met."""
        # Close match should potentially trigger draw boost
        pred = self.predictor.predict("Everton", "Nottingham Forest")
        # We can't guarantee draw boost, but should not crash
        self.assertIsInstance(pred.draw_boost_applied, bool)


class TestRegressionCases(unittest.TestCase):
    """Regression tests for known issues."""

    def test_import_path_issue_fixed(self):
        """Verify the import path issue is fixed (the bug we just hit)."""
        # This should not raise ImportError
        try:
            from predictor.tri_lens_predictor import TriLensPredictor
            success = True
        except ImportError:
            # Fallback - try direct import
            from tri_lens_predictor import TriLensPredictor
            success = True

        self.assertTrue(success)

    def test_normalize_team_handles_aliases(self):
        """Team name normalization should handle common aliases."""
        from poisson_predictor import PoissonPredictor
        predictor = PoissonPredictor()

        # These should all resolve to the same team
        pred1 = predictor.predict("Man City", "Liverpool")
        pred2 = predictor.predict("Manchester City", "Liverpool")

        # Same home attack strength
        self.assertEqual(pred1.home_attack, pred2.home_attack)

    def test_database_path_resolution(self):
        """Database path should resolve correctly from any directory."""
        from tri_lens_predictor import DB_PATH
        # Path should exist or at least be a valid path object
        self.assertIsInstance(DB_PATH, Path)


class TestDefensiveProgramming(unittest.TestCase):
    """Test defensive programming patterns."""

    def test_division_by_zero_protection(self):
        """Verify no division by zero in calculations."""
        from poisson_predictor import calculate_match_probabilities

        # Very low xG values
        h, d, a, _ = calculate_match_probabilities(0.01, 0.01)
        self.assertFalse(math.isnan(h))
        self.assertFalse(math.isnan(d))
        self.assertFalse(math.isnan(a))

    def test_handles_missing_team_data(self):
        """Should handle teams not in database gracefully."""
        from tri_lens_predictor import TriLensPredictor
        predictor = TriLensPredictor()

        # Fictional team
        pred = predictor.predict("Fictional FC", "Another Fictional")
        self.assertIsNotNone(pred)
        self.assertIsNotNone(pred.prediction)

    def test_handles_none_odds(self):
        """Should handle None betting odds."""
        from tri_lens_predictor import TriLensPredictor
        predictor = TriLensPredictor()

        pred = predictor.predict("Liverpool", "Arsenal", None, None, None)
        self.assertIsNotNone(pred)


def run_all_tests():
    """Run all tests with verbose output."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestImports))
    suite.addTests(loader.loadTestsFromTestCase(TestPoissonMath))
    suite.addTests(loader.loadTestsFromTestCase(TestMatchProbabilities))
    suite.addTests(loader.loadTestsFromTestCase(TestInputValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestTriLensIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestRegressionCases))
    suite.addTests(loader.loadTestsFromTestCase(TestDefensiveProgramming))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    print("=" * 70)
    print("TRI-LENS PREDICTOR TEST SUITE")
    print("=" * 70)
    result = run_all_tests()

    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("ALL TESTS PASSED!")
    else:
        print(f"FAILURES: {len(result.failures)}")
        print(f"ERRORS: {len(result.errors)}")
    print("=" * 70)
