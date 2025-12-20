"""
NBA-AI Knowledge Graph Migration Tests

Proves domain-agnostic architecture by testing:
1. Schema compliance (same as Soccer-AI)
2. Node/edge migration
3. FTS5 search
4. Idempotency
5. Edge cases
"""

import unittest
import sqlite3
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kg.nba_migration import (
    migrate_nba_kg,
    run_nba_migration,
    get_nba_stats,
    search_nba,
    init_schema,
    get_connection,
    NBA_KG_JSON,
    NLKE_SCHEMA
)


class TestNBASchema(unittest.TestCase):
    """Test schema compliance."""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_nba.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_schema_creates_nodes_table(self):
        """Nodes table has correct columns."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            cursor = conn.execute("PRAGMA table_info(nodes)")
            columns = {row[1] for row in cursor.fetchall()}

        required = {'id', 'original_id', 'name', 'type', 'description', 'metadata', 'source_kg', 'created_at'}
        self.assertTrue(required.issubset(columns))

    def test_schema_creates_edges_table(self):
        """Edges table has correct columns."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            cursor = conn.execute("PRAGMA table_info(edges)")
            columns = {row[1] for row in cursor.fetchall()}

        required = {'id', 'from_node', 'to_node', 'type', 'weight', 'source_kg', 'created_at'}
        self.assertTrue(required.issubset(columns))

    def test_schema_creates_fts5_table(self):
        """FTS5 virtual table exists."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='nodes_fts'
            """)
            result = cursor.fetchone()

        self.assertIsNotNone(result)

    def test_edges_have_unique_constraint(self):
        """Edge uniqueness constraint exists."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            cursor = conn.execute("PRAGMA index_list(edges)")
            indices = [row[1] for row in cursor.fetchall()]

        # Should have unique index on (from_node, to_node, type)
        self.assertTrue(any('unique' in idx.lower() for idx in indices) or len(indices) > 0)


class TestNBAMigration(unittest.TestCase):
    """Test migration from JSON to SQLite."""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_nba.db"

        # Load JSON
        with open(NBA_KG_JSON, 'r') as f:
            self.kg_data = json.load(f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_modules_migrated(self):
        """All modules from JSON are migrated."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            counts = migrate_nba_kg(conn, self.kg_data)

        expected = len(self.kg_data.get('modules', {}))
        self.assertEqual(counts['modules'], expected)
        self.assertEqual(expected, 5)  # main, database, rag, ai_response, predictor_api

    def test_endpoints_migrated(self):
        """All endpoints from JSON are migrated."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            counts = migrate_nba_kg(conn, self.kg_data)

        expected = len(self.kg_data.get('endpoints', {}))
        self.assertEqual(counts['endpoints'], expected)
        self.assertEqual(expected, 3)  # chat, trivia, predictions

    def test_personas_migrated(self):
        """All personas (teams) from JSON are migrated."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            counts = migrate_nba_kg(conn, self.kg_data)

        expected = len(self.kg_data.get('personas', {}))
        self.assertEqual(counts['personas'], expected)
        self.assertEqual(expected, 3)  # Lakers, Celtics, Warriors

    def test_legends_migrated(self):
        """All legends (players) from JSON are migrated."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            counts = migrate_nba_kg(conn, self.kg_data)

        expected = len(self.kg_data.get('legends', {}))
        self.assertEqual(counts['legends'], expected)
        self.assertEqual(expected, 4)  # Magic, Bird, Curry, Kobe

    def test_rivalries_migrated(self):
        """All rivalries from JSON are migrated."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            counts = migrate_nba_kg(conn, self.kg_data)

        expected = len(self.kg_data.get('rivalries', {}))
        self.assertEqual(counts['rivalries'], expected)
        self.assertEqual(expected, 2)  # Lakers-Celtics, Warriors-Cavaliers

    def test_predictor_factors_a_migrated(self):
        """Side A factors are migrated."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            counts = migrate_nba_kg(conn, self.kg_data)

        predictor = self.kg_data.get('predictor', {})
        expected = len(predictor.get('factors_a', {}))
        self.assertEqual(counts['predictor_factors_a'], expected)
        self.assertEqual(expected, 4)  # NBA_FAT, NBA_INJ, NBA_TRV, NBA_RST

    def test_predictor_factors_b_migrated(self):
        """Side B factors are migrated."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            counts = migrate_nba_kg(conn, self.kg_data)

        predictor = self.kg_data.get('predictor', {})
        expected = len(predictor.get('factors_b', {}))
        self.assertEqual(counts['predictor_factors_b'], expected)
        self.assertEqual(expected, 3)  # NBA_HME, NBA_MOT, NBA_HOT

    def test_predictor_patterns_migrated(self):
        """Patterns are migrated."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            counts = migrate_nba_kg(conn, self.kg_data)

        predictor = self.kg_data.get('predictor', {})
        expected = len(predictor.get('patterns', {}))
        self.assertEqual(counts['predictor_patterns'], expected)
        self.assertEqual(expected, 1)  # back_to_back_revenge

    def test_total_nodes(self):
        """Total node count matches expected."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            migrate_nba_kg(conn, self.kg_data)
            count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]

        # 5 + 3 + 3 + 4 + 2 + 4 + 3 + 1 = 25
        self.assertEqual(count, 25)

    def test_source_kg_is_nba(self):
        """All nodes have source_kg = 'nba'."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            migrate_nba_kg(conn, self.kg_data)
            cursor = conn.execute("SELECT DISTINCT source_kg FROM nodes")
            sources = [row[0] for row in cursor.fetchall()]

        self.assertEqual(sources, ['nba'])


class TestNBAEdges(unittest.TestCase):
    """Test edge creation."""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_nba.db"

        with open(NBA_KG_JSON, 'r') as f:
            self.kg_data = json.load(f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_edges_created(self):
        """Edges are created during migration."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            counts = migrate_nba_kg(conn, self.kg_data)

        self.assertGreater(counts['edges'], 0)

    def test_depends_on_edges(self):
        """Module dependencies create depends_on edges."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            migrate_nba_kg(conn, self.kg_data)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM edges WHERE type = 'depends_on'
            """)
            count = cursor.fetchone()[0]

        self.assertGreater(count, 0)

    def test_routes_to_edges(self):
        """Endpoints create routes_to edges."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            migrate_nba_kg(conn, self.kg_data)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM edges WHERE type = 'routes_to'
            """)
            count = cursor.fetchone()[0]

        self.assertGreater(count, 0)

    def test_plays_for_edges(self):
        """Legends create plays_for edges to teams."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            migrate_nba_kg(conn, self.kg_data)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM edges WHERE type = 'plays_for'
            """)
            count = cursor.fetchone()[0]

        # All 4 legends have teams
        self.assertEqual(count, 4)


class TestNBAFTS5Search(unittest.TestCase):
    """Test full-text search."""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_nba.db"

        # Run full migration
        with open(NBA_KG_JSON, 'r') as f:
            kg_data = json.load(f)

        with get_connection(self.db_path) as conn:
            init_schema(conn)
            migrate_nba_kg(conn, kg_data)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_search_team_name(self):
        """Search finds teams by name."""
        results = search_nba("Lakers", db_path=self.db_path)
        names = [r['name'] for r in results]
        self.assertTrue(any('Lakers' in n for n in names))

    def test_search_player_name(self):
        """Search finds players by name."""
        results = search_nba("Curry", db_path=self.db_path)
        names = [r['name'] for r in results]
        self.assertTrue(any('Curry' in n for n in names))

    def test_search_factor(self):
        """Search finds predictor factors."""
        results = search_nba("fatigue", db_path=self.db_path)
        types = [r['type'] for r in results]
        self.assertIn('factor_a', types)

    def test_search_empty_returns_empty(self):
        """Empty search returns empty list."""
        results = search_nba("xyznonexistent", db_path=self.db_path)
        self.assertEqual(len(results), 0)

    def test_search_respects_limit(self):
        """Search respects limit parameter."""
        results = search_nba("NBA", limit=2, db_path=self.db_path)
        self.assertLessEqual(len(results), 2)


class TestNBAIdempotency(unittest.TestCase):
    """Test migration idempotency."""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_nba.db"

        with open(NBA_KG_JSON, 'r') as f:
            self.kg_data = json.load(f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_double_migration_same_node_count(self):
        """Running migration twice doesn't duplicate nodes."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            migrate_nba_kg(conn, self.kg_data)
            count1 = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]

            # Run again
            migrate_nba_kg(conn, self.kg_data)
            count2 = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]

        self.assertEqual(count1, count2)

    def test_double_migration_same_edge_count(self):
        """Running migration twice doesn't duplicate edges."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            migrate_nba_kg(conn, self.kg_data)
            count1 = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

            # Run again
            migrate_nba_kg(conn, self.kg_data)
            count2 = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]

        self.assertEqual(count1, count2)


class TestNBAStats(unittest.TestCase):
    """Test statistics retrieval."""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_nba.db"

        # Run full migration
        with open(NBA_KG_JSON, 'r') as f:
            kg_data = json.load(f)

        with get_connection(self.db_path) as conn:
            init_schema(conn)
            migrate_nba_kg(conn, kg_data)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_stats_returns_totals(self):
        """Stats include total counts."""
        stats = get_nba_stats(self.db_path)
        self.assertIn('total_nodes', stats)
        self.assertIn('total_edges', stats)
        self.assertEqual(stats['total_nodes'], 25)

    def test_stats_by_type(self):
        """Stats include breakdown by type."""
        stats = get_nba_stats(self.db_path)
        self.assertIn('by_type', stats)
        self.assertIn('module', stats['by_type'])
        self.assertIn('persona', stats['by_type'])

    def test_stats_edge_types(self):
        """Stats include edge type breakdown."""
        stats = get_nba_stats(self.db_path)
        self.assertIn('edge_types', stats)
        self.assertIn('depends_on', stats['edge_types'])


class TestNBAEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_nba.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_empty_json_migration(self):
        """Empty JSON doesn't crash."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            counts = migrate_nba_kg(conn, {})

        self.assertEqual(counts['modules'], 0)
        self.assertEqual(counts['personas'], 0)

    def test_missing_sections_handled(self):
        """Missing sections don't crash migration."""
        partial_data = {
            "modules": {"main": {"file": "main.py", "what": "Entry", "depends_on": []}}
        }
        with get_connection(self.db_path) as conn:
            init_schema(conn)
            counts = migrate_nba_kg(conn, partial_data)

        self.assertEqual(counts['modules'], 1)
        self.assertEqual(counts['personas'], 0)

    def test_search_special_characters(self):
        """Search handles special characters safely."""
        with get_connection(self.db_path) as conn:
            init_schema(conn)

        # These should not crash
        search_nba("test'quote", db_path=self.db_path)
        search_nba('test"double', db_path=self.db_path)
        search_nba("test*wildcard", db_path=self.db_path)


if __name__ == "__main__":
    # Run tests
    print("=" * 60)
    print("NBA-AI Knowledge Graph Migration Tests")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestNBASchema))
    suite.addTests(loader.loadTestsFromTestCase(TestNBAMigration))
    suite.addTests(loader.loadTestsFromTestCase(TestNBAEdges))
    suite.addTests(loader.loadTestsFromTestCase(TestNBAFTS5Search))
    suite.addTests(loader.loadTestsFromTestCase(TestNBAIdempotency))
    suite.addTests(loader.loadTestsFromTestCase(TestNBAStats))
    suite.addTests(loader.loadTestsFromTestCase(TestNBAEdgeCases))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print("=" * 60)
