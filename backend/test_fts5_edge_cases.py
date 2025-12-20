"""
FTS5 Edge Case Tests
Tests for Insight #927 bug fix - FTS5 reserved word collision
"""

import pytest
import database


class TestFTS5Escaping:
    """Test the escape_fts_query function."""

    def test_normal_query(self):
        """Normal queries should work."""
        result = database.escape_fts_query("Arsenal")
        assert result == '"Arsenal"'

    def test_multi_word_query(self):
        """Multi-word queries should quote each word."""
        result = database.escape_fts_query("Thierry Henry")
        assert result == '"Thierry" "Henry"'

    def test_or_keyword(self):
        """OR keyword should be quoted to prevent FTS5 syntax error."""
        result = database.escape_fts_query("Arsenal OR Chelsea")
        assert '"OR"' in result
        # Should not cause syntax error when used in query
        results = database.search_teams("Arsenal OR Chelsea")
        assert isinstance(results, list)

    def test_and_keyword(self):
        """AND keyword should be quoted."""
        result = database.escape_fts_query("Arsenal AND Tottenham")
        assert '"AND"' in result
        results = database.search_teams("Arsenal AND Tottenham")
        assert isinstance(results, list)

    def test_not_keyword(self):
        """NOT keyword should be quoted."""
        result = database.escape_fts_query("NOT Arsenal")
        assert '"NOT"' in result
        results = database.search_teams("NOT Arsenal")
        assert isinstance(results, list)

    def test_near_keyword(self):
        """NEAR keyword should be quoted."""
        result = database.escape_fts_query("Arsenal NEAR London")
        assert '"NEAR"' in result

    def test_sql_injection_attempt(self):
        """SQL injection patterns should be safely escaped."""
        result = database.escape_fts_query("1=1 OR 1=1")
        assert '"OR"' in result
        # Should not cause error
        results = database.search_teams("1=1 OR 1=1")
        assert isinstance(results, list)

    def test_special_characters(self):
        """Special characters should be removed."""
        result = database.escape_fts_query("Arsenal's (best) player?")
        assert "'" not in result
        assert "(" not in result
        assert "?" not in result

    def test_empty_query(self):
        """Empty query should return empty string."""
        result = database.escape_fts_query("")
        assert result == ""

    def test_only_special_chars(self):
        """Query with only special chars should return empty."""
        result = database.escape_fts_query("??? !!! ***")
        assert result == ""

    def test_mixed_case_reserved_words(self):
        """Reserved words in different cases should be handled."""
        # OR in lowercase
        result = database.escape_fts_query("Arsenal or Chelsea")
        assert '"or"' in result
        results = database.search_teams("Arsenal or Chelsea")
        assert isinstance(results, list)


class TestSearchWithReservedWords:
    """Integration tests for search functions with reserved words."""

    def test_search_players_with_or(self):
        """Search players with OR keyword."""
        results = database.search_players("player OR forward")
        assert isinstance(results, list)

    def test_search_teams_with_and(self):
        """Search teams with AND keyword."""
        results = database.search_teams("Manchester AND United")
        assert isinstance(results, list)

    def test_search_news_with_not(self):
        """Search news with NOT keyword."""
        results = database.search_news("NOT injury")
        assert isinstance(results, list)

    def test_search_all_with_reserved_words(self):
        """Search all with multiple reserved words."""
        results = database.search_all("Arsenal OR Chelsea AND NOT Tottenham")
        assert isinstance(results, dict)
        assert "players" in results
        assert "teams" in results
        assert "news" in results


class TestRealWorldQueries:
    """Test real-world query patterns that might contain reserved words."""

    def test_player_or_position_query(self):
        """User might ask 'striker or forward'."""
        results = database.search_players("striker or forward")
        assert isinstance(results, list)

    def test_this_or_that_query(self):
        """User might ask about alternatives."""
        results = database.search_teams("Arsenal or Tottenham")
        assert isinstance(results, list)

    def test_negation_query(self):
        """User might use 'not' in natural language."""
        results = database.search_news("Chelsea not winning")
        assert isinstance(results, list)

    def test_near_location_query(self):
        """User might use 'near' for location."""
        results = database.search_teams("stadium near London")
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
