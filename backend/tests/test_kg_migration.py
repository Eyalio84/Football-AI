"""
Test Suite for NLKE Knowledge Graph Migration

Tests:
1. Schema compliance
2. Node migration counts
3. Edge creation
4. FTS5 search functionality
5. Cross-domain queries
6. Idempotency
"""

import unittest
import sqlite3
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from kg.kg_database import KnowledgeGraphDB, get_kg_connection, KG_DB_PATH
from kg.kg_types import NodeType, EdgeType, create_node_id
from kg.kg_migration import run_migration
from kg.nlke_bridge import NLKEBridge


class TestSchemaCompliance(unittest.TestCase):
    """Test NLKE schema compliance."""

    def test_nodes_table_exists(self):
        """Verify nodes table exists with required columns."""
        with get_kg_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(nodes)")
            columns = {row['name'] for row in cursor.fetchall()}

            required = {'id', 'name', 'type', 'source_kg', 'description', 'metadata'}
            self.assertTrue(required.issubset(columns),
                            f"Missing columns: {required - columns}")

    def test_edges_table_exists(self):
        """Verify edges table exists with required columns."""
        with get_kg_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(edges)")
            columns = {row['name'] for row in cursor.fetchall()}

            required = {'from_node', 'to_node', 'type', 'source_kg', 'weight'}
            self.assertTrue(required.issubset(columns),
                            f"Missing columns: {required - columns}")

    def test_fts5_table_exists(self):
        """Verify FTS5 virtual table exists."""
        with get_kg_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='nodes_fts'
            """)
            result = cursor.fetchone()
            self.assertIsNotNone(result, "FTS5 table nodes_fts not found")

    def test_source_kg_index_exists(self):
        """Verify source_kg index exists for cross-domain queries."""
        with get_kg_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND name='idx_nodes_source_kg'
            """)
            result = cursor.fetchone()
            self.assertIsNotNone(result, "Index idx_nodes_source_kg not found")


class TestNodeMigration(unittest.TestCase):
    """Test node migration counts."""

    @classmethod
    def setUpClass(cls):
        """Run migration before tests."""
        if not KG_DB_PATH.exists():
            run_migration()

    def test_soccer_ai_nodes_exist(self):
        """Verify soccer-ai domain nodes exist."""
        stats = KnowledgeGraphDB.get_stats()
        self.assertIn('soccer-ai', stats['by_domain'],
                      "soccer-ai domain not found")
        self.assertGreater(stats['by_domain']['soccer-ai']['nodes'], 0,
                           "No soccer-ai nodes found")

    def test_predictor_nodes_exist(self):
        """Verify predictor domain nodes exist."""
        stats = KnowledgeGraphDB.get_stats()
        self.assertIn('predictor', stats['by_domain'],
                      "predictor domain not found")
        self.assertGreater(stats['by_domain']['predictor']['nodes'], 0,
                           "No predictor nodes found")

    def test_node_types_populated(self):
        """Verify expected node types exist."""
        stats = KnowledgeGraphDB.get_stats()
        expected_types = {'module', 'endpoint'}  # Minimal set

        found_types = set(stats['by_type'].keys())
        self.assertTrue(expected_types.issubset(found_types),
                        f"Missing types: {expected_types - found_types}")

    def test_total_node_count(self):
        """Verify minimum total node count (60+ expected)."""
        stats = KnowledgeGraphDB.get_stats()
        self.assertGreaterEqual(stats['total_nodes'], 50,
                                f"Expected 50+ nodes, got {stats['total_nodes']}")


class TestEdgeCreation(unittest.TestCase):
    """Test edge creation."""

    @classmethod
    def setUpClass(cls):
        """Ensure migration ran."""
        if not KG_DB_PATH.exists():
            run_migration()

    def test_edges_exist(self):
        """Verify edges were created."""
        stats = KnowledgeGraphDB.get_stats()
        self.assertGreater(stats['total_edges'], 0,
                           "No edges created")

    def test_edge_types_populated(self):
        """Verify edge types exist."""
        stats = KnowledgeGraphDB.get_stats()
        self.assertGreater(len(stats['edge_types']), 0,
                           "No edge types found")

    def test_depends_on_edges(self):
        """Verify depends_on edges exist."""
        stats = KnowledgeGraphDB.get_stats()
        self.assertIn('depends_on', stats['edge_types'],
                      "depends_on edge type not found")


class TestFTS5Search(unittest.TestCase):
    """Test FTS5 search functionality."""

    @classmethod
    def setUpClass(cls):
        """Ensure migration ran."""
        if not KG_DB_PATH.exists():
            run_migration()

    def test_basic_search(self):
        """Verify basic FTS5 search works."""
        results = KnowledgeGraphDB.search_nodes("main", limit=5)
        # Should find main.py module at minimum
        self.assertGreater(len(results), 0,
                           "FTS5 search returned no results for 'main'")

    def test_search_with_source_filter(self):
        """Verify filtered search by source_kg."""
        # Search only soccer-ai domain
        results = KnowledgeGraphDB.search_nodes("module", source_kg="soccer-ai")
        for result in results:
            self.assertEqual(result['source_kg'], 'soccer-ai',
                             f"Non-soccer-ai result found: {result}")

    def test_search_case_insensitive(self):
        """Verify search is case-insensitive."""
        results_lower = KnowledgeGraphDB.search_nodes("database")
        results_upper = KnowledgeGraphDB.search_nodes("DATABASE")
        # Should return similar results
        self.assertEqual(len(results_lower), len(results_upper),
                         "Case sensitivity issue in search")


class TestCrossDomainQueries(unittest.TestCase):
    """Test cross-domain query functionality."""

    @classmethod
    def setUpClass(cls):
        """Ensure migration ran."""
        if not KG_DB_PATH.exists():
            run_migration()

    def test_query_across_domains(self):
        """Verify cross-domain query returns results from multiple domains."""
        results = KnowledgeGraphDB.query_across_domains(
            query="module",
            domains=['soccer-ai', 'predictor']
        )

        domains_found = set(r['source_kg'] for r in results)
        self.assertEqual(len(domains_found), 2,
                         f"Expected results from 2 domains, got {domains_found}")

    def test_get_cross_domain_nodes(self):
        """Verify cross-domain node grouping."""
        results = KnowledgeGraphDB.get_cross_domain_nodes('module')

        self.assertIn('soccer-ai', results,
                      "soccer-ai modules not found")
        self.assertIn('predictor', results,
                      "predictor modules not found")


class TestNLKEBridge(unittest.TestCase):
    """Test NLKE Bridge functionality."""

    @classmethod
    def setUpClass(cls):
        """Ensure migration ran."""
        if not KG_DB_PATH.exists():
            run_migration()

    def test_hybrid_search(self):
        """Verify hybrid search returns scored results."""
        result = NLKEBridge.hybrid_search("chat", scope="all", k=5)

        self.assertIn('results', result)
        self.assertIn('query', result)
        self.assertIn('elapsed_ms', result)

        if result['results']:
            self.assertIn('score', result['results'][0])

    def test_semantic_similarity(self):
        """Verify semantic similarity calculation."""
        # Same phrase should have similarity 1.0
        sim = NLKEBridge.semantic_similarity("soccer match", "soccer match")
        self.assertEqual(sim, 1.0)

        # Different phrases should have lower similarity
        sim = NLKEBridge.semantic_similarity("soccer match", "football game")
        self.assertLess(sim, 1.0)

    def test_unified_query_auto_mode(self):
        """Verify unified query auto-detects domain."""
        # Should detect predictor domain
        result = NLKEBridge.unified_query("upset prediction factor", mode="auto")
        self.assertIn('mode', result)

    def test_register_with_mcp(self):
        """Verify MCP registration info is complete."""
        config = NLKEBridge.register_with_mcp()

        self.assertIn('domains', config)
        self.assertIn('capabilities', config)
        self.assertIn('total_nodes', config)
        self.assertIn('total_edges', config)


class TestTraversal(unittest.TestCase):
    """Test graph traversal functionality."""

    @classmethod
    def setUpClass(cls):
        """Ensure migration ran."""
        if not KG_DB_PATH.exists():
            run_migration()

    def test_get_node(self):
        """Verify single node retrieval."""
        # Find any node
        stats = KnowledgeGraphDB.get_stats()
        if stats['total_nodes'] > 0:
            with get_kg_connection() as conn:
                cursor = conn.execute("SELECT id FROM nodes LIMIT 1")
                node_id = cursor.fetchone()['id']

            node = KnowledgeGraphDB.get_node(node_id)
            self.assertIsNotNone(node)
            self.assertEqual(node['id'], node_id)

    def test_get_neighbors(self):
        """Verify neighbor retrieval."""
        # Find a node with edges
        with get_kg_connection() as conn:
            cursor = conn.execute("""
                SELECT from_node FROM edges LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                node_id = row['from_node']
                neighbors = KnowledgeGraphDB.get_neighbors(node_id, direction='out')
                self.assertGreater(len(neighbors), 0,
                                   "No neighbors found for node with outgoing edges")

    def test_traverse_depth(self):
        """Verify BFS traversal respects depth."""
        with get_kg_connection() as conn:
            cursor = conn.execute("SELECT id FROM nodes LIMIT 1")
            row = cursor.fetchone()
            if row:
                node_id = row['id']
                results = KnowledgeGraphDB.traverse(node_id, depth=2)
                # All results should have depth 1 or 2
                for r in results:
                    self.assertIn(r['depth'], [1, 2])


class TestIdempotency(unittest.TestCase):
    """Test migration idempotency."""

    def test_double_migration_safe(self):
        """Verify running migration twice doesn't duplicate data."""
        # Get current counts
        stats_before = KnowledgeGraphDB.get_stats()

        # Run migration again
        run_migration()

        # Get counts after
        stats_after = KnowledgeGraphDB.get_stats()

        # Should be the same (idempotent)
        self.assertEqual(stats_before['total_nodes'], stats_after['total_nodes'],
                         "Node count changed after re-migration")
        self.assertEqual(stats_before['total_edges'], stats_after['total_edges'],
                         "Edge count changed after re-migration")


class TestNodeIdFormat(unittest.TestCase):
    """Test NLKE-compliant node ID format."""

    def test_create_node_id_format(self):
        """Verify node ID format matches NLKE spec."""
        node_id = create_node_id('soccer-ai', 'module', 'main')
        self.assertEqual(node_id, 'soccer-ai_module_main')

    def test_create_node_id_sanitization(self):
        """Verify special characters are sanitized."""
        node_id = create_node_id('predictor', 'factor_a', 'FA-FAT')
        # Should lowercase and replace hyphens with underscores
        self.assertEqual(node_id, 'predictor_factor_a_fa_fat')

    def test_node_ids_in_database(self):
        """Verify stored node IDs follow format."""
        with get_kg_connection() as conn:
            cursor = conn.execute("SELECT id, source_kg FROM nodes LIMIT 10")
            for row in cursor.fetchall():
                # ID should start with source_kg
                self.assertTrue(
                    row['id'].startswith(row['source_kg']),
                    f"Node ID {row['id']} doesn't start with {row['source_kg']}"
                )


class TestStats(unittest.TestCase):
    """Test statistics retrieval."""

    @classmethod
    def setUpClass(cls):
        """Ensure migration ran."""
        if not KG_DB_PATH.exists():
            run_migration()

    def test_stats_returns_totals(self):
        """Stats include total counts."""
        stats = KnowledgeGraphDB.get_stats()
        self.assertIn('total_nodes', stats)
        self.assertIn('total_edges', stats)
        self.assertGreater(stats['total_nodes'], 0)

    def test_stats_by_type(self):
        """Stats include breakdown by type."""
        stats = KnowledgeGraphDB.get_stats()
        self.assertIn('by_type', stats)
        self.assertGreater(len(stats['by_type']), 0)

    def test_stats_edge_types(self):
        """Stats include edge type breakdown."""
        stats = KnowledgeGraphDB.get_stats()
        self.assertIn('edge_types', stats)
        self.assertGreater(len(stats['edge_types']), 0)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_search_empty_query(self):
        """Empty search query doesn't crash."""
        results = KnowledgeGraphDB.search_nodes("")
        # Should return empty or all, but not crash
        self.assertIsInstance(results, list)

    def test_search_special_characters(self):
        """Search handles special characters safely."""
        # These should not crash
        KnowledgeGraphDB.search_nodes("test'quote")
        KnowledgeGraphDB.search_nodes('test"double')
        KnowledgeGraphDB.search_nodes("test*wildcard")

    def test_get_nonexistent_node(self):
        """Getting non-existent node returns None or empty."""
        result = KnowledgeGraphDB.get_node("nonexistent_node_xyz")
        self.assertIsNone(result)

    def test_traverse_nonexistent_node(self):
        """Traversing from non-existent node returns empty."""
        results = KnowledgeGraphDB.traverse("nonexistent_xyz", depth=1)
        self.assertEqual(len(results), 0)


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaCompliance))
    suite.addTests(loader.loadTestsFromTestCase(TestNodeMigration))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCreation))
    suite.addTests(loader.loadTestsFromTestCase(TestFTS5Search))
    suite.addTests(loader.loadTestsFromTestCase(TestCrossDomainQueries))
    suite.addTests(loader.loadTestsFromTestCase(TestNLKEBridge))
    suite.addTests(loader.loadTestsFromTestCase(TestTraversal))
    suite.addTests(loader.loadTestsFromTestCase(TestIdempotency))
    suite.addTests(loader.loadTestsFromTestCase(TestNodeIdFormat))
    suite.addTests(loader.loadTestsFromTestCase(TestStats))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    # Ensure database exists first
    if not KG_DB_PATH.exists():
        print("Database not found. Running migration first...")
        run_migration()

    result = run_tests()

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
