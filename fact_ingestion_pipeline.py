#!/usr/bin/env python3
"""
Fact Ingestion Pipeline for Soccer-AI KG-KB-RAG

This pipeline captures facts from various sources and persists them to your local KB.

Sources:
1. WebSearch results (manual input - Claude provides, pipeline stores)
2. PDF documents (automatic extraction)
3. Manual facts (user-provided)

Usage:
    from fact_ingestion_pipeline import FactPipeline

    pipeline = FactPipeline()

    # Ingest facts from web search results
    pipeline.ingest_web_facts(search_results, source_url)

    # Ingest from PDF
    pipeline.ingest_pdf("/path/to/document.pdf")

    # Add manual fact
    pipeline.add_fact("Liverpool won the 2024-25 Premier League",
                      entities=["Liverpool", "Premier League"])
"""

import sqlite3
import json
import re
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import sys

# Add tools path for parser
sys.path.insert(0, '/storage/emulated/0/Download/synthesis-rules/tools')


@dataclass
class Fact:
    """A single fact to be stored in KB."""
    content: str
    fact_type: str  # 'statistic', 'event', 'relationship', 'opinion', 'record'
    entities: List[str]
    confidence: float = 0.9
    source_type: str = "manual"  # 'web_search', 'pdf', 'manual'
    source_url: str = ""


@dataclass
class IngestionResult:
    """Result of ingestion operation."""
    facts_added: int
    facts_skipped: int  # duplicates
    entities_linked: int
    errors: List[str]


class FactPipeline:
    """
    Pipeline for ingesting facts into Soccer-AI KB.

    Architecture:
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │   Source     │ --> │  Extractor   │ --> │     KB       │
    │ (Web/PDF)    │     │ (Parse/NLP)  │     │  (SQLite)    │
    └──────────────┘     └──────────────┘     └──────────────┘
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = "/storage/emulated/0/Download/synthesis-rules/soccer-AI/soccer_ai_architecture_kg.db"

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        # Load known entities for linking
        self._load_entities()

        # Fact type keywords for auto-detection
        self.fact_type_patterns = {
            'statistic': [r'\d+', r'won', r'scored', r'appearances', r'goals', r'titles', r'capacity', r'founded'],
            'event': [r'on \d+', r'in \d{4}', r'won the', r'beat', r'defeated', r'signed', r'transferred'],
            'relationship': [r'rivalry', r'derby', r'versus', r'between', r'against'],
            'opinion': [r'described', r'said', r'believed', r'considered', r'greatest', r'best', r'worst'],
            'record': [r'most', r'first', r'only', r'longest', r'highest', r'record'],
        }

    def _load_entities(self):
        """Load known entities from KG for linking."""
        self.cursor.execute("SELECT node_id, name, type FROM kg_nodes")
        self.entities = {}
        self.entity_aliases = {}

        for node_id, name, node_type in self.cursor.fetchall():
            self.entities[name.lower()] = (node_id, name, node_type)

            # Create common aliases
            name_lower = name.lower()
            if 'manchester united' in name_lower:
                self.entity_aliases['man utd'] = name
                self.entity_aliases['united'] = name
                self.entity_aliases['man united'] = name
            elif 'manchester city' in name_lower:
                self.entity_aliases['man city'] = name
                self.entity_aliases['city'] = name
            elif 'tottenham' in name_lower:
                self.entity_aliases['spurs'] = name
                self.entity_aliases['tottenham'] = name
            elif 'alex ferguson' in name_lower:
                self.entity_aliases['ferguson'] = name
                self.entity_aliases['fergie'] = name
                self.entity_aliases['sir alex'] = name

    def _detect_fact_type(self, content: str) -> str:
        """Auto-detect fact type from content."""
        content_lower = content.lower()
        scores = {ft: 0 for ft in self.fact_type_patterns}

        for fact_type, patterns in self.fact_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    scores[fact_type] += 1

        best_type = max(scores, key=scores.get)
        return best_type if scores[best_type] > 0 else 'statistic'

    def _extract_entities(self, content: str) -> List[str]:
        """Extract entity mentions from content."""
        content_lower = content.lower()
        found = []

        # Check aliases first
        for alias, canonical in self.entity_aliases.items():
            if alias in content_lower and canonical not in found:
                found.append(canonical)

        # Check full entity names
        for name_lower, (node_id, name, node_type) in self.entities.items():
            if name_lower in content_lower and name not in found:
                found.append(name)

        return found

    def _is_duplicate(self, content: str) -> bool:
        """Check if fact already exists."""
        # Normalize content for comparison
        normalized = ' '.join(content.lower().split())

        self.cursor.execute("""
            SELECT fact_id FROM kb_facts
            WHERE LOWER(content) = ?
        """, (normalized,))

        return self.cursor.fetchone() is not None

    def _add_fact_to_db(self, fact: Fact) -> Optional[int]:
        """Add fact to database and return fact_id."""
        if self._is_duplicate(fact.content):
            return None

        self.cursor.execute("""
            INSERT INTO kb_facts
            (content, fact_type, confidence, source_type, source_url, source_date, related_entities)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fact.content,
            fact.fact_type,
            fact.confidence,
            fact.source_type,
            fact.source_url,
            datetime.now().isoformat(),
            json.dumps(fact.entities)
        ))

        fact_id = self.cursor.lastrowid

        # Update FTS index
        self.cursor.execute("""
            INSERT INTO kb_facts_fts (rowid, content, fact_type, related_entities)
            VALUES (?, ?, ?, ?)
        """, (fact_id, fact.content, fact.fact_type, json.dumps(fact.entities)))

        return fact_id

    def _link_entities(self, fact_id: int, entities: List[str]) -> int:
        """Link fact to KG entities."""
        linked = 0
        for entity_name in entities:
            entity_lower = entity_name.lower()
            if entity_lower in self.entities:
                node_id = self.entities[entity_lower][0]

                # Check if link already exists
                self.cursor.execute("""
                    SELECT id FROM kb_entity_facts
                    WHERE entity_id = ? AND fact_id = ?
                """, (node_id, fact_id))

                if not self.cursor.fetchone():
                    self.cursor.execute("""
                        INSERT INTO kb_entity_facts (entity_id, fact_id, relevance)
                        VALUES (?, ?, 1.0)
                    """, (node_id, fact_id))
                    linked += 1

        return linked

    def add_fact(self, content: str,
                 entities: List[str] = None,
                 fact_type: str = None,
                 confidence: float = 0.9,
                 source_type: str = "manual",
                 source_url: str = "") -> Tuple[bool, str]:
        """
        Add a single fact to KB.

        Args:
            content: The fact text
            entities: List of entity names (auto-detected if None)
            fact_type: Type of fact (auto-detected if None)
            confidence: Confidence score 0-1
            source_type: 'web_search', 'pdf', 'manual'
            source_url: Source URL or path

        Returns:
            (success, message)
        """
        # Auto-detect if not provided
        if entities is None:
            entities = self._extract_entities(content)
        if fact_type is None:
            fact_type = self._detect_fact_type(content)

        fact = Fact(
            content=content,
            fact_type=fact_type,
            entities=entities,
            confidence=confidence,
            source_type=source_type,
            source_url=source_url
        )

        fact_id = self._add_fact_to_db(fact)

        if fact_id is None:
            return (False, "Duplicate fact")

        linked = self._link_entities(fact_id, entities)
        self.conn.commit()

        return (True, f"Added fact #{fact_id}, linked to {linked} entities")

    def ingest_web_facts(self, facts_text: str, source_url: str = "") -> IngestionResult:
        """
        Ingest multiple facts from web search results.

        Args:
            facts_text: Multi-line text with facts (one per line or bullet)
            source_url: Source URL

        Returns:
            IngestionResult with stats
        """
        result = IngestionResult(
            facts_added=0,
            facts_skipped=0,
            entities_linked=0,
            errors=[]
        )

        # Split into individual facts
        lines = facts_text.strip().split('\n')

        for line in lines:
            # Clean up line
            line = line.strip()
            line = re.sub(r'^[-•*]\s*', '', line)  # Remove bullet points
            line = re.sub(r'^\d+\.\s*', '', line)  # Remove numbering

            if len(line) < 10:  # Skip too short lines
                continue

            # Extract entities
            entities = self._extract_entities(line)
            fact_type = self._detect_fact_type(line)

            fact = Fact(
                content=line,
                fact_type=fact_type,
                entities=entities,
                confidence=0.9,
                source_type="web_search",
                source_url=source_url
            )

            try:
                fact_id = self._add_fact_to_db(fact)

                if fact_id is None:
                    result.facts_skipped += 1
                else:
                    result.facts_added += 1
                    linked = self._link_entities(fact_id, entities)
                    result.entities_linked += linked

            except Exception as e:
                result.errors.append(f"Error adding fact: {str(e)}")

        self.conn.commit()
        return result

    def ingest_pdf(self, pdf_path: str) -> IngestionResult:
        """
        Ingest facts from a Wikipedia PDF.

        Uses the wikipedia_football_parser to extract structured data,
        then converts to facts.
        """
        result = IngestionResult(
            facts_added=0,
            facts_skipped=0,
            entities_linked=0,
            errors=[]
        )

        try:
            from pypdf import PdfReader
            from wikipedia_football_parser import WikipediaFootballParser
        except ImportError as e:
            result.errors.append(f"Import error: {e}")
            return result

        try:
            # Extract text from PDF
            reader = PdfReader(pdf_path)
            text = "".join([page.extract_text() + "\n" for page in reader.pages])

            # Store full document in kb_documents
            title = os.path.basename(pdf_path).replace('.PDF', '').replace('.pdf', '')

            self.cursor.execute("""
                INSERT INTO kb_documents (title, content, doc_type, source_path, word_count)
                VALUES (?, ?, 'wikipedia_pdf', ?, ?)
            """, (title, text, pdf_path, len(text.split())))

            doc_id = self.cursor.lastrowid

            # Update documents FTS
            self.cursor.execute("""
                INSERT INTO kb_documents_fts (rowid, title, content)
                VALUES (?, ?, ?)
            """, (doc_id, title, text))

            # Parse for structured data
            parser = WikipediaFootballParser()
            parsed = parser.parse(text, source_file=pdf_path)

            # Convert parsed data to facts
            entity_type = parsed['metadata']['entity_type']

            # Career facts
            for career in parsed.get('career', []):
                fact_content = f"{title} played for {career['team']} from {career['years']}, making {career.get('appearances', '?')} appearances and scoring {career.get('goals', '?')} goals."

                fact = Fact(
                    content=fact_content,
                    fact_type="statistic",
                    entities=[title, career['team']],
                    confidence=1.0,
                    source_type="pdf",
                    source_url=pdf_path
                )

                fact_id = self._add_fact_to_db(fact)
                if fact_id:
                    result.facts_added += 1
                    result.entities_linked += self._link_entities(fact_id, fact.entities)
                else:
                    result.facts_skipped += 1

            # Honours facts
            for honour in parsed.get('honours', []):
                years_str = ', '.join(honour.get('years', [])[:5])
                if len(honour.get('years', [])) > 5:
                    years_str += '...'

                fact_content = f"{title} won the {honour['competition']} {honour['count']} time(s): {years_str}"

                fact = Fact(
                    content=fact_content,
                    fact_type="statistic",
                    entities=[title, honour['competition']],
                    confidence=0.95,
                    source_type="pdf",
                    source_url=pdf_path
                )

                fact_id = self._add_fact_to_db(fact)
                if fact_id:
                    result.facts_added += 1
                    result.entities_linked += self._link_entities(fact_id, fact.entities)
                else:
                    result.facts_skipped += 1

            # Match facts
            if parsed.get('match'):
                match = parsed['match']
                fact_content = f"{match['home_team']} {match['home_score']}-{match['away_score']} {match['away_team']} on {match['date']} at {match['venue']}. Attendance: {match.get('attendance', '?')}."

                fact = Fact(
                    content=fact_content,
                    fact_type="event",
                    entities=[match['home_team'], match['away_team']],
                    confidence=1.0,
                    source_type="pdf",
                    source_url=pdf_path
                )

                fact_id = self._add_fact_to_db(fact)
                if fact_id:
                    result.facts_added += 1
                    result.entities_linked += self._link_entities(fact_id, fact.entities)

            self.conn.commit()

        except Exception as e:
            result.errors.append(f"PDF processing error: {str(e)}")

        return result

    def ingest_all_pdfs(self, folder_path: str) -> Dict[str, IngestionResult]:
        """Ingest all PDFs from a folder."""
        results = {}

        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(folder_path, filename)
                print(f"Processing: {filename}")
                results[filename] = self.ingest_pdf(pdf_path)

        return results

    def get_stats(self) -> Dict[str, int]:
        """Get current KB statistics."""
        stats = {}

        self.cursor.execute("SELECT COUNT(*) FROM kb_facts")
        stats['facts'] = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM kb_documents")
        stats['documents'] = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM kb_entity_facts")
        stats['entity_links'] = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM kg_nodes")
        stats['kg_nodes'] = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM kg_edges")
        stats['kg_edges'] = self.cursor.fetchone()[0]

        return stats

    def search_facts(self, query: str, limit: int = 10) -> List[Dict]:
        """Search facts using FTS5."""
        results = []

        try:
            self.cursor.execute("""
                SELECT f.fact_id, f.content, f.fact_type, f.confidence, f.source_type
                FROM kb_facts f
                JOIN kb_facts_fts fts ON f.fact_id = fts.rowid
                WHERE kb_facts_fts MATCH ?
                ORDER BY f.confidence DESC
                LIMIT ?
            """, (query, limit))

            for row in self.cursor.fetchall():
                results.append({
                    'fact_id': row[0],
                    'content': row[1],
                    'type': row[2],
                    'confidence': row[3],
                    'source': row[4]
                })
        except:
            pass

        return results

    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    """Test the pipeline."""
    pipeline = FactPipeline()

    print("=== Current KB Stats ===")
    stats = pipeline.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n=== Testing Manual Fact Addition ===")
    success, msg = pipeline.add_fact(
        "Wayne Rooney is Manchester United's all-time top scorer with 253 goals.",
        entities=["Manchester United"],
        fact_type="record"
    )
    print(f"  {msg}")

    print("\n=== Testing Web Facts Ingestion ===")
    web_facts = """
    - Arsenal's longest unbeaten run in the Premier League was 49 games from May 2003 to October 2004.
    - Thierry Henry is Arsenal's all-time top scorer with 228 goals.
    - Liverpool won the Champions League in 2005, coming back from 3-0 down against AC Milan.
    - Steven Gerrard made 710 appearances for Liverpool, scoring 186 goals.
    """

    result = pipeline.ingest_web_facts(web_facts, "https://example.com/football-facts")
    print(f"  Added: {result.facts_added}, Skipped: {result.facts_skipped}, Links: {result.entities_linked}")

    print("\n=== Testing Search ===")
    facts = pipeline.search_facts("Liverpool")
    for fact in facts[:3]:
        print(f"  [{fact['type']}] {fact['content'][:60]}...")

    print("\n=== Updated KB Stats ===")
    stats = pipeline.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    pipeline.close()


if __name__ == "__main__":
    main()
