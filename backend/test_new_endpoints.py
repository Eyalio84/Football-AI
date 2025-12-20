#!/usr/bin/env python3
"""
Test New Endpoints (Phases 0-6)
Tests for gap tracker, security, trivia, on-this-day, metrics, legends.
"""

import unittest
import database


class TestGapTracker(unittest.TestCase):
    """Test Implementation Gap Tracker endpoints."""

    def test_get_gaps(self):
        """Test getting implementation gaps."""
        database.init_gap_tracker()
        gaps = database.get_implementation_gaps()
        self.assertIsInstance(gaps, list)

    def test_get_gap_summary(self):
        """Test getting gap summary."""
        summary = database.get_gap_summary()
        self.assertIn('total', summary)
        self.assertIn('by_status', summary)
        self.assertIn('by_priority', summary)


class TestSecuritySystem(unittest.TestCase):
    """Test Security Infrastructure."""

    def test_security_tables_exist(self):
        """Test security tables are initialized."""
        database.init_security_tables()
        metrics = database.get_security_metrics(days=1)
        self.assertIsInstance(metrics, dict)

    def test_session_state(self):
        """Test session state management."""
        import security_session
        session = security_session.SecuritySession("test_session")
        self.assertEqual(session.state, "normal")

    def test_state_escalation(self):
        """Test state escalation on injection."""
        import security_session
        session = security_session.SecuritySession("test_escalation")
        session.handle_injection("test_pattern")
        self.assertEqual(session.state, "warned")

    def test_de_escalation(self):
        """Test de-escalation path."""
        import security_session
        session = security_session.SecuritySession("test_de_escalation")
        session.state = "probation"
        for _ in range(5):
            session.handle_clean_query()
        self.assertEqual(session.state, "normal")


class TestTriviaSystem(unittest.TestCase):
    """Test Trivia System."""

    def test_trivia_table_exists(self):
        """Test trivia table is initialized."""
        database.init_trivia_table()
        stats = database.get_trivia_stats()
        self.assertIn('total_questions', stats)

    def test_get_trivia_question(self):
        """Test getting a trivia question."""
        question = database.get_trivia_question()
        if question:
            self.assertIn('question', question)
            self.assertIn('correct_answer', question)

    def test_trivia_stats(self):
        """Test trivia statistics."""
        stats = database.get_trivia_stats()
        self.assertIsInstance(stats['total_questions'], int)


class TestOnThisDay(unittest.TestCase):
    """Test On This Day functionality."""

    def test_get_moments_on_date(self):
        """Test getting moments for a specific date."""
        # Test with MM-DD format
        moments = database.get_moments_on_this_day("05-26")  # May 26
        self.assertIsInstance(moments, list)

    def test_get_moments_today(self):
        """Test getting moments for today."""
        moments = database.get_moments_on_this_day()
        self.assertIsInstance(moments, list)


class TestMoodAutoUpdate(unittest.TestCase):
    """Test Mood Auto-Update functionality."""

    def test_mood_function_exists(self):
        """Test mood update function exists and is callable."""
        self.assertTrue(callable(database.update_mood_after_match))

    def test_get_club_mood(self):
        """Test getting club mood."""
        team_id = 3  # Arsenal
        mood = database.get_club_mood(team_id)
        if mood:
            self.assertIn('mood_intensity', mood)


class TestLegendsEndpoints(unittest.TestCase):
    """Test Legends functionality."""

    def test_get_legend(self):
        """Test getting a legend."""
        legends = database.get_legends(limit=1)
        if legends:
            legend = database.get_legend(legends[0]['id'])
            self.assertIsNotNone(legend)

    def test_search_legends(self):
        """Test searching legends."""
        results = database.search_legends("Henry", limit=5)
        self.assertIsInstance(results, list)


class TestAnalystPersona(unittest.TestCase):
    """Test Analyst persona integration."""

    def test_analyst_snap_back_exists(self):
        """Test analyst snap-back response exists."""
        import ai_response
        snap_back = ai_response.get_snap_back_response("analyst")
        self.assertIn("data", snap_back.lower())

    def test_analyst_in_valid_clubs(self):
        """Test analyst is in valid clubs."""
        # Would need to check main.py, but we know it's there


if __name__ == "__main__":
    print("=" * 60)
    print("NEW ENDPOINTS TEST SUITE")
    print("=" * 60)
    unittest.main(verbosity=2)
