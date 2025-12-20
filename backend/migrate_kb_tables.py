"""
Add Knowledge Base tables to Unified KG

Migrates from soccer_ai_architecture_kg.db:
- match_history (230k+ records) - for form/mood fallback
- elo_history (26k+ records) - for predictions
- kb_facts (681 records) - Robert's knowledge
- kb_documents (12 records) - Wikipedia content
"""

import sqlite3
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).parent
PROJECT_DIR = BACKEND_DIR.parent

ARCHITECTURE_DB = PROJECT_DIR / "soccer_ai_architecture_kg.db"
UNIFIED_DB = BACKEND_DIR / "unified_soccer_ai_kg.db"


def migrate_kb_tables():
    print("=" * 60)
    print("MIGRATING KB TABLES TO UNIFIED DB")
    print("=" * 60)

    if not ARCHITECTURE_DB.exists():
        print(f"ERROR: Architecture DB not found: {ARCHITECTURE_DB}")
        return

    source = sqlite3.connect(ARCHITECTURE_DB)
    target = sqlite3.connect(UNIFIED_DB)

    # 1. Match History
    print("\n[1/4] Migrating match_history...")
    target.execute("""
        CREATE TABLE IF NOT EXISTS match_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            division TEXT,
            match_date TEXT,
            match_time TEXT,
            home_team TEXT,
            away_team TEXT,
            home_elo REAL,
            away_elo REAL,
            form3_home REAL,
            form5_home REAL,
            form3_away REAL,
            form5_away REAL,
            ft_home INTEGER,
            ft_away INTEGER,
            ft_result TEXT,
            ht_home INTEGER,
            ht_away INTEGER,
            ht_result TEXT,
            home_shots INTEGER,
            away_shots INTEGER,
            home_target INTEGER,
            away_target INTEGER,
            home_fouls INTEGER,
            away_fouls INTEGER,
            home_corners INTEGER,
            away_corners INTEGER,
            home_yellow INTEGER,
            away_yellow INTEGER,
            home_red INTEGER,
            away_red INTEGER,
            odd_home REAL,
            odd_draw REAL,
            odd_away REAL
        )
    """)

    rows = source.execute("SELECT * FROM match_history").fetchall()
    target.executemany("""
        INSERT INTO match_history VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)
    target.commit()
    print(f"  → {len(rows)} match records migrated")

    # 2. ELO History
    print("\n[2/4] Migrating elo_history...")
    target.execute("""
        CREATE TABLE IF NOT EXISTS elo_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            club TEXT,
            country TEXT,
            elo REAL
        )
    """)

    rows = source.execute("SELECT * FROM elo_history").fetchall()
    target.executemany("INSERT INTO elo_history VALUES (?,?,?,?,?)", rows)
    target.commit()
    print(f"  → {len(rows)} ELO records migrated")

    # 3. KB Facts
    print("\n[3/4] Migrating kb_facts...")
    target.execute("""
        CREATE TABLE IF NOT EXISTS kb_facts (
            fact_id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            fact_type TEXT,
            confidence REAL DEFAULT 0.9,
            source_type TEXT,
            source_url TEXT,
            source_date TEXT,
            related_entities TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    rows = source.execute("SELECT * FROM kb_facts").fetchall()
    target.executemany("INSERT INTO kb_facts VALUES (?,?,?,?,?,?,?,?,?)", rows)
    target.commit()
    print(f"  → {len(rows)} facts migrated")

    # 4. KB Documents
    print("\n[4/4] Migrating kb_documents...")
    target.execute("""
        CREATE TABLE IF NOT EXISTS kb_documents (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            doc_type TEXT,
            source_path TEXT,
            word_count INTEGER,
            entities_mentioned TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    rows = source.execute("SELECT * FROM kb_documents").fetchall()
    target.executemany("INSERT INTO kb_documents VALUES (?,?,?,?,?,?,?,?)", rows)
    target.commit()
    print(f"  → {len(rows)} documents migrated")

    # Create FTS for facts
    print("\n[FTS] Creating full-text search index for facts...")
    target.execute("DROP TABLE IF EXISTS kb_facts_fts")
    target.execute("""
        CREATE VIRTUAL TABLE kb_facts_fts USING fts5(
            content,
            content='kb_facts',
            content_rowid='fact_id'
        )
    """)
    target.execute("""
        INSERT INTO kb_facts_fts(rowid, content)
        SELECT fact_id, content FROM kb_facts
    """)
    target.commit()
    print("  → FTS index created")

    # Create indices
    print("\n[INDICES] Creating performance indices...")
    target.execute("CREATE INDEX IF NOT EXISTS idx_match_home ON match_history(home_team)")
    target.execute("CREATE INDEX IF NOT EXISTS idx_match_away ON match_history(away_team)")
    target.execute("CREATE INDEX IF NOT EXISTS idx_match_date ON match_history(match_date)")
    target.execute("CREATE INDEX IF NOT EXISTS idx_elo_club ON elo_history(club)")
    target.execute("CREATE INDEX IF NOT EXISTS idx_elo_date ON elo_history(date)")
    target.commit()
    print("  → Indices created")

    source.close()
    target.close()

    # Report final size
    size_mb = UNIFIED_DB.stat().st_size / (1024 * 1024)
    print(f"\n✓ Unified DB now: {size_mb:.1f} MB")


if __name__ == "__main__":
    migrate_kb_tables()
