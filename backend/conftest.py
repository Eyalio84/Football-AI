"""
Soccer-AI Backend - Shared pytest fixtures

Provides common fixtures used across test suites:
- Database path resolution (soccer_ai.db, unified KG)
- Temporary test database creation
- sys.path setup for backend imports
"""

import os
import sys
import sqlite3
import shutil

import pytest

# ---------------------------------------------------------------------------
# Ensure backend/ is on sys.path so tests can import top-level modules
# (config, database, fan_enhancements, etc.) without path hacks in every file.
# ---------------------------------------------------------------------------
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


# =============================================================================
# DATABASE PATH FIXTURES
# =============================================================================

@pytest.fixture
def soccer_ai_db_path():
    """Return the absolute path to the main soccer_ai.db file.

    Skips the test if the database does not exist.
    """
    path = os.path.join(BACKEND_DIR, "soccer_ai.db")
    if not os.path.exists(path):
        pytest.skip(f"soccer_ai.db not found at {path}")
    return path


@pytest.fixture
def unified_kg_db_path():
    """Return the absolute path to the unified knowledge-graph database.

    Skips the test if the database does not exist.
    """
    path = os.path.join(BACKEND_DIR, "unified_soccer_ai_kg.db")
    if not os.path.exists(path):
        pytest.skip(f"unified_soccer_ai_kg.db not found at {path}")
    return path


# =============================================================================
# TEMPORARY TEST DATABASE
# =============================================================================

@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary SQLite database for isolated tests.

    Yields a (db_path, connection) tuple.  The database file lives inside
    pytest's tmp_path so it is automatically cleaned up.

    Usage::

        def test_something(tmp_db):
            db_path, conn = tmp_db
            conn.execute("CREATE TABLE foo (id INTEGER PRIMARY KEY)")
            ...
    """
    db_path = str(tmp_path / "test_soccer_ai.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    yield db_path, conn
    conn.close()


@pytest.fixture
def tmp_kg_db(tmp_path, unified_kg_db_path):
    """Create a disposable copy of the unified KG database for write tests.

    Copies the real unified_soccer_ai_kg.db into tmp_path so tests can
    mutate data without affecting the source.  Skips if the source DB is
    missing.

    Yields a (db_path, connection) tuple.
    """
    dest = str(tmp_path / "unified_soccer_ai_kg_copy.db")
    shutil.copy2(unified_kg_db_path, dest)
    conn = sqlite3.connect(dest)
    conn.row_factory = sqlite3.Row
    yield dest, conn
    conn.close()
