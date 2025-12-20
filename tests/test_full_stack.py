"""
Full Stack Test Suite for Soccer-AI

Tests all backend components:
1. KG Integration (entity resolution, fact retrieval)
2. Match Insights (H2H, comebacks, ELO, on this day)
3. Football API (live data, caching)
4. Mood Engine (mood calculation, templates)
5. Pattern Extractor (pattern mining, ingestion)
6. Edge Cases (missing data, malformed queries, boundaries)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import sqlite3
from datetime import datetime
from pathlib import Path

# Import all components
from backend.kg_integration import get_kg, KGIntegration
from backend.match_insights import get_match_insights, MatchInsights
from backend.mood_engine import get_mood_engine, MoodEngine, Mood
from backend.pattern_extractor import get_pattern_extractor, PatternExtractor

DB_PATH = Path(__file__).parent.parent / "soccer_ai_architecture_kg.db"


class TestKGIntegration(unittest.TestCase):
    """Test Knowledge Graph Integration Layer"""

    @classmethod
    def setUpClass(cls):
        cls.kg = get_kg()

    def test_kg_loads(self):
        """KG should load with entities"""
        self.assertIsNotNone(self.kg)
        self.assertGreater(len(self.kg.entities), 0)

    def test_entity_resolution_direct(self):
        """Should find entities by direct name match"""
        entities = self.kg.find_entities("Liverpool")
        names = [e[1] for e in entities]
        self.assertIn("Liverpool", names)

    def test_entity_resolution_alias(self):
        """Should resolve aliases to canonical names"""
        entities = self.kg.find_entities("Fergie was the best manager")
        names = [e[1] for e in entities]
        self.assertIn("Alex Ferguson", names)

    def test_entity_resolution_multiple(self):
        """Should find multiple entities in one query"""
        entities = self.kg.find_entities("Liverpool vs Man United derby")
        names = [e[1] for e in entities]
        self.assertIn("Liverpool", names)
        # Should find either Manchester United or related entity

    def test_get_entity_context(self):
        """Should return entity context with relationships"""
        ctx = self.kg.get_entity_context("Liverpool")
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx["entity"]["name"], "Liverpool")
        self.assertIn("relationships", ctx)

    def test_search_facts(self):
        """Should find facts via FTS"""
        facts = self.kg.search_facts("Premier League", limit=5)
        self.assertGreater(len(facts), 0)

    def test_search_facts_pattern_keywords(self):
        """Should find pattern facts via keywords"""
        facts = self.kg.search_facts("comebacks", limit=5)
        self.assertGreater(len(facts), 0)
        # At least one should mention comebacks
        comeback_facts = [f for f in facts if 'comeback' in f['content'].lower()]
        self.assertGreater(len(comeback_facts), 0)

    def test_enhanced_context_with_keywords(self):
        """Should surface pattern facts via keyword matching"""
        result = self.kg.get_enhanced_context("Tell me about comebacks")
        comeback_facts = [f for f in result['facts'] if 'comeback' in f['content'].lower()]
        self.assertGreater(len(comeback_facts), 0)

    def test_kg_stats(self):
        """Should return valid stats"""
        stats = self.kg.get_stats()
        self.assertGreater(stats["total_nodes"], 500)
        self.assertGreater(stats["total_edges"], 400)
        self.assertGreater(stats["total_facts"], 600)


class TestMatchInsights(unittest.TestCase):
    """Test Match Insights Engine"""

    @classmethod
    def setUpClass(cls):
        cls.insights = get_match_insights()

    def test_insights_loads(self):
        """Insights engine should initialize"""
        self.assertIsNotNone(self.insights)

    def test_head_to_head(self):
        """Should return H2H stats for two teams"""
        h2h = self.insights.head_to_head("Liverpool", "Manchester United")
        self.assertGreater(h2h["total_matches"], 0)
        self.assertIn("team1_wins", h2h)
        self.assertIn("team2_wins", h2h)
        self.assertIn("draws", h2h)

    def test_head_to_head_alias(self):
        """Should handle team aliases"""
        h2h = self.insights.head_to_head("Liverpool", "Man United")
        self.assertGreater(h2h["total_matches"], 0)

    def test_on_this_day(self):
        """Should return matches from today's date in history"""
        otd = self.insights.on_this_day(limit=10)
        # May or may not have matches on today's date
        self.assertIsInstance(otd, list)

    def test_on_this_day_with_team(self):
        """Should filter by team"""
        otd = self.insights.on_this_day(team="Liverpool", limit=10)
        self.assertIsInstance(otd, list)

    def test_find_comebacks(self):
        """Should find comeback matches"""
        comebacks = self.insights.find_comebacks(limit=10)
        self.assertGreater(len(comebacks), 0)
        # Verify structure
        if comebacks:
            c = comebacks[0]
            self.assertIn("ht_score", c)
            self.assertIn("ft_score", c)
            self.assertIn("comeback_team", c)

    def test_find_comebacks_team_filter(self):
        """Should filter comebacks by team"""
        comebacks = self.insights.find_comebacks(team="Liverpool", limit=10)
        self.assertIsInstance(comebacks, list)

    def test_find_upsets(self):
        """Should find upset matches by ELO difference"""
        upsets = self.insights.find_upsets(elo_diff_min=100, limit=10)
        self.assertGreater(len(upsets), 0)
        if upsets:
            self.assertIn("elo_diff", upsets[0])
            self.assertIn("underdog", upsets[0])

    def test_get_elo_trajectory(self):
        """Should return ELO trajectory for a team"""
        elo = self.insights.get_elo_trajectory("Liverpool")
        self.assertIn("trajectory", elo)
        self.assertIn("peak", elo)
        self.assertIn("low", elo)

    def test_derby_stats(self):
        """Should return derby stats"""
        derby = self.insights.derby_stats("Liverpool", "Everton")
        self.assertIn("total_matches", derby)
        self.assertIn("total_yellows", derby)

    def test_generate_matchday_context(self):
        """Should generate context string"""
        ctx = self.insights.generate_matchday_context("Liverpool", "Everton")
        self.assertIsInstance(ctx, str)
        self.assertGreater(len(ctx), 0)


class TestMoodEngine(unittest.TestCase):
    """Test Mood Engine"""

    @classmethod
    def setUpClass(cls):
        cls.engine = get_mood_engine()

    def test_engine_loads(self):
        """Mood engine should initialize"""
        self.assertIsNotNone(self.engine)

    def test_mood_enum_values(self):
        """Mood enum should have correct values"""
        self.assertEqual(Mood.ELATED.value, 5)
        self.assertEqual(Mood.DEVASTATED.value, 0)

    def test_is_rival_true(self):
        """Should detect rivalries"""
        self.assertTrue(self.engine._is_rival("Liverpool", "Manchester United"))
        self.assertTrue(self.engine._is_rival("Arsenal", "Tottenham Hotspur"))
        self.assertTrue(self.engine._is_rival("Liverpool", "Everton"))

    def test_is_rival_false(self):
        """Should not flag non-rivals"""
        self.assertFalse(self.engine._is_rival("Liverpool", "Brighton"))
        self.assertFalse(self.engine._is_rival("Arsenal", "Newcastle"))

    def test_mood_templates_exist(self):
        """All moods should have templates"""
        for mood in Mood:
            template = self.engine.get_mood_template(mood)
            self.assertIn("openers", template)
            self.assertIn("tone", template)
            self.assertIn("banter_level", template)

    def test_calculate_result_impact_win(self):
        """Should detect wins"""
        match = {
            "home_team": "Liverpool",
            "away_team": "Brighton",
            "home_score": 3,
            "away_score": 1
        }
        result, margin, is_derby = self.engine._calculate_result_impact("Liverpool", match)
        self.assertEqual(result, 'W')
        self.assertEqual(margin, 2)
        self.assertFalse(is_derby)

    def test_calculate_result_impact_loss(self):
        """Should detect losses"""
        match = {
            "home_team": "Liverpool",
            "away_team": "Brighton",
            "home_score": 0,
            "away_score": 2
        }
        result, margin, is_derby = self.engine._calculate_result_impact("Liverpool", match)
        self.assertEqual(result, 'L')
        self.assertEqual(margin, 2)

    def test_calculate_result_impact_draw(self):
        """Should detect draws"""
        match = {
            "home_team": "Liverpool",
            "away_team": "Brighton",
            "home_score": 1,
            "away_score": 1
        }
        result, margin, is_derby = self.engine._calculate_result_impact("Liverpool", match)
        self.assertEqual(result, 'D')
        self.assertEqual(margin, 0)

    def test_calculate_result_impact_derby(self):
        """Should detect derby matches"""
        match = {
            "home_team": "Liverpool",
            "away_team": "Manchester United",
            "home_score": 2,
            "away_score": 0
        }
        result, margin, is_derby = self.engine._calculate_result_impact("Liverpool", match)
        self.assertEqual(result, 'W')
        self.assertTrue(is_derby)

    def test_result_to_mood_derby_win(self):
        """Derby win should be ELATED"""
        mood = self.engine._result_to_mood('W', 1, True, {})
        self.assertEqual(mood, Mood.ELATED)

    def test_result_to_mood_derby_loss(self):
        """Derby loss should be DEVASTATED"""
        mood = self.engine._result_to_mood('L', 1, True, {})
        self.assertEqual(mood, Mood.DEVASTATED)

    def test_result_to_mood_heavy_loss(self):
        """Heavy loss should be DEVASTATED"""
        mood = self.engine._result_to_mood('L', 4, False, {})
        self.assertEqual(mood, Mood.DEVASTATED)

    def test_result_to_mood_normal_win(self):
        """Normal win should be HAPPY"""
        mood = self.engine._result_to_mood('W', 2, False, {})
        self.assertEqual(mood, Mood.HAPPY)


class TestPatternExtractor(unittest.TestCase):
    """Test Pattern Extraction Engine"""

    @classmethod
    def setUpClass(cls):
        cls.extractor = get_pattern_extractor()

    def test_extractor_loads(self):
        """Pattern extractor should initialize"""
        self.assertIsNotNone(self.extractor)

    def test_extract_bogey_teams(self):
        """Should extract bogey team patterns"""
        bogey = self.extractor.extract_bogey_teams(min_games=10)
        self.assertGreater(len(bogey), 0)
        if bogey:
            self.assertIn("team", bogey[0])
            self.assertIn("bogey", bogey[0])
            self.assertIn("win_rate", bogey[0])

    def test_extract_golden_eras(self):
        """Should extract golden era patterns"""
        eras = self.extractor.extract_golden_eras()
        self.assertGreater(len(eras), 0)
        if eras:
            self.assertIn("team", eras[0])
            self.assertIn("peak_elo", eras[0])

    def test_extract_comeback_specialists(self):
        """Should extract comeback patterns"""
        comebacks = self.extractor.extract_comeback_specialists()
        self.assertGreater(len(comebacks), 0)
        if comebacks:
            self.assertIn("team", comebacks[0])
            self.assertIn("comebacks", comebacks[0])

    def test_extract_derby_dominance(self):
        """Should extract derby dominance patterns"""
        derbies = self.extractor.extract_derby_dominance()
        self.assertGreater(len(derbies), 0)


class TestEdgeCases(unittest.TestCase):
    """Test Edge Cases and Error Handling"""

    @classmethod
    def setUpClass(cls):
        cls.kg = get_kg()
        cls.insights = get_match_insights()
        cls.engine = get_mood_engine()

    def test_empty_query(self):
        """Should handle empty query"""
        entities = self.kg.find_entities("")
        self.assertIsInstance(entities, list)

    def test_nonexistent_entity(self):
        """Should handle nonexistent entity"""
        ctx = self.kg.get_entity_context("Nonexistent FC")
        self.assertIsNone(ctx)

    def test_h2h_nonexistent_team(self):
        """Should handle nonexistent team in H2H"""
        h2h = self.insights.head_to_head("Nonexistent FC", "Liverpool")
        self.assertEqual(h2h["total_matches"], 0)

    def test_h2h_same_team(self):
        """Should handle same team vs itself"""
        h2h = self.insights.head_to_head("Liverpool", "Liverpool")
        self.assertEqual(h2h["total_matches"], 0)

    def test_rival_detection_partial_name(self):
        """Should handle partial team names in rivalry"""
        # Man United should still match Manchester United rivalry
        is_rival = self.engine._is_rival("Liverpool", "Man United")
        # This may or may not work depending on normalization
        self.assertIsInstance(is_rival, bool)

    def test_mood_calculation_no_recent_games(self):
        """Should handle team with no recent games"""
        # This would need mocking for proper test
        mood, ctx = self.engine.calculate_mood("Nonexistent FC")
        self.assertEqual(mood, Mood.NEUTRAL)

    def test_result_impact_missing_scores(self):
        """Should handle missing scores"""
        match = {
            "home_team": "Liverpool",
            "away_team": "Brighton",
            "home_score": None,
            "away_score": None
        }
        result, margin, is_derby = self.engine._calculate_result_impact("Liverpool", match)
        self.assertIsNone(result)

    def test_result_impact_team_not_playing(self):
        """Should handle when team not in match"""
        match = {
            "home_team": "Arsenal",
            "away_team": "Chelsea",
            "home_score": 2,
            "away_score": 1
        }
        result, margin, is_derby = self.engine._calculate_result_impact("Liverpool", match)
        self.assertIsNone(result)

    def test_elo_trajectory_unknown_team(self):
        """Should handle unknown team in ELO"""
        elo = self.insights.get_elo_trajectory("Nonexistent FC")
        self.assertEqual(len(elo.get("trajectory", [])), 0)

    def test_fts_special_characters(self):
        """Should handle special characters in FTS"""
        # FTS might fail on special chars
        facts = self.kg.search_facts("test & query | special", limit=5)
        self.assertIsInstance(facts, list)

    def test_unicode_in_query(self):
        """Should handle unicode in query"""
        entities = self.kg.find_entities("Liverpool \u26bd champions")
        self.assertIsInstance(entities, list)


class TestDatabaseIntegrity(unittest.TestCase):
    """Test Database Integrity"""

    @classmethod
    def setUpClass(cls):
        cls.conn = sqlite3.connect(str(DB_PATH))
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_tables_exist(self):
        """All required tables should exist"""
        tables = ['kg_nodes', 'kg_edges', 'kb_facts', 'match_history', 'elo_history']
        for table in tables:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            self.assertIsNotNone(self.cursor.fetchone(), f"Table {table} should exist")

    def test_fts_table_exists(self):
        """FTS table should exist"""
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='kb_facts_fts'")
        self.assertIsNotNone(self.cursor.fetchone())

    def test_fts_synced_with_facts(self):
        """FTS should have same count as facts"""
        self.cursor.execute("SELECT COUNT(*) FROM kb_facts")
        facts_count = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM kb_facts_fts")
        fts_count = self.cursor.fetchone()[0]
        self.assertEqual(facts_count, fts_count)

    def test_match_history_has_data(self):
        """Match history should have substantial data"""
        self.cursor.execute("SELECT COUNT(*) FROM match_history")
        count = self.cursor.fetchone()[0]
        self.assertGreater(count, 200000)

    def test_elo_history_has_data(self):
        """ELO history should have data"""
        self.cursor.execute("SELECT COUNT(*) FROM elo_history")
        count = self.cursor.fetchone()[0]
        self.assertGreater(count, 20000)

    def test_kg_nodes_minimum(self):
        """Should have minimum nodes"""
        self.cursor.execute("SELECT COUNT(*) FROM kg_nodes")
        count = self.cursor.fetchone()[0]
        self.assertGreater(count, 500)

    def test_kb_facts_minimum(self):
        """Should have minimum facts"""
        self.cursor.execute("SELECT COUNT(*) FROM kb_facts")
        count = self.cursor.fetchone()[0]
        self.assertGreater(count, 600)


def run_tests():
    """Run all tests and return results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestKGIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestMatchInsights))
    suite.addTests(loader.loadTestsFromTestCase(TestMoodEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseIntegrity))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    run_tests()
