"""
Web Search Enrichment for Soccer-AI

Uses web search to enrich KB facts when local data is sparse.
Adds discovered facts to the KB for future use.
"""

import json
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import urllib.request
import urllib.parse

# KB Database path
KB_DB = Path(__file__).parent / "unified_soccer_ai_kg.db"


class WebEnrichment:
    """
    Enriches the KB with web search results.

    Strategy:
    1. Check if KB has sufficient facts for entity
    2. If not, search web for entity + context
    3. Extract key facts from search results
    4. Store in KB for future use
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(KB_DB)
        self.min_facts_threshold = 2  # Minimum facts before web search

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def count_entity_facts(self, entity_name: str) -> int:
        """Count existing facts for an entity."""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Search in related_entities JSON
        cursor.execute("""
            SELECT COUNT(*) FROM kb_facts
            WHERE related_entities LIKE ?
        """, (f'%{entity_name}%',))

        count = cursor.fetchone()[0]
        conn.close()
        return count

    def needs_enrichment(self, entity_name: str) -> bool:
        """Check if entity needs web enrichment."""
        return self.count_entity_facts(entity_name) < self.min_facts_threshold

    def add_fact(self, content: str, fact_type: str,
                 source_url: str, related_entities: List[str],
                 confidence: float = 0.8):
        """Add a web-sourced fact to KB."""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Check if fact already exists
        cursor.execute("SELECT 1 FROM kb_facts WHERE content = ?", (content,))
        if cursor.fetchone():
            conn.close()
            return False

        cursor.execute("""
            INSERT INTO kb_facts (content, fact_type, confidence, source_type, source_url, related_entities)
            VALUES (?, ?, ?, 'web_search', ?, ?)
        """, (content, fact_type, confidence, source_url, json.dumps(related_entities)))

        conn.commit()
        conn.close()
        return True

    def extract_facts_from_text(self, text: str, entity_name: str) -> List[Dict]:
        """Extract facts from search result text."""
        facts = []

        # Patterns for football facts
        patterns = [
            # Trophy/achievement patterns
            (r'won (?:the )?(\d+) ([A-Z][a-z]+ (?:League|Cup|Trophy|Championship))', 'trophy'),
            (r'(\d+) ([A-Z][a-z]+ (?:League|Cup)) titles?', 'trophy'),

            # Goal scoring patterns
            (r'scored (\d+) goals? in (\d+) (?:appearances?|games?|matches?)', 'statistic'),
            (r'top scorer with (\d+) goals?', 'statistic'),

            # Date/era patterns
            (r'from (\d{4}) to (\d{4})', 'timeline'),
            (r'joined (?:the club )?in (\d{4})', 'transfer'),

            # Match facts
            (r'(\d+)[–-](\d+) (?:victory|win|defeat|draw) against ([A-Z][a-z]+)', 'match'),

            # Manager facts
            (r'managed (?:the club )?for (\d+) years?', 'tenure'),
            (r'won (\d+) trophies? (?:as manager|during (?:his|her) tenure)', 'achievement'),
        ]

        for pattern, fact_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                fact_text = match.group(0)
                # Make it a complete sentence
                if entity_name.lower() not in fact_text.lower():
                    fact_text = f"{entity_name} {fact_text}"

                facts.append({
                    'content': fact_text,
                    'type': fact_type,
                    'match': match.group(0)
                })

        return facts

    def enrich_from_predefined(self, entity_name: str, entity_type: str) -> int:
        """Add predefined facts for well-known entities."""

        # Curated facts for key entities
        predefined_facts = {
            # Managers
            "Alex Ferguson": [
                ("Alex Ferguson won 38 trophies during his 26 years at Manchester United (1986-2013)", "achievement"),
                ("Ferguson's Manchester United won 13 Premier League titles, a record", "trophy"),
                ("The Class of '92 including Beckham, Scholes, Giggs emerged under Ferguson", "legacy"),
                ("Ferguson won the treble in 1999: Premier League, FA Cup, Champions League", "trophy"),
            ],
            "Pep Guardiola": [
                ("Pep Guardiola won 6 Premier League titles with Manchester City", "trophy"),
                ("Guardiola won the Champions League in 2023, completing City's treble", "trophy"),
                ("Guardiola's Barcelona won 14 trophies including 2 Champions Leagues", "achievement"),
            ],
            "Jurgen Klopp": [
                ("Jurgen Klopp won Liverpool's first league title in 30 years in 2020", "trophy"),
                ("Klopp won the Champions League with Liverpool in 2019", "trophy"),
                ("Klopp's 'gegenpressing' style transformed Liverpool into European elite", "style"),
            ],

            # Historic matches
            "Liverpool 3-3 AC Milan 2005": [
                ("Liverpool came back from 3-0 down at halftime to win on penalties", "match_detail"),
                ("Steven Gerrard's header started Liverpool's incredible comeback", "moment"),
                ("Jerzy Dudek's save from Shevchenko in penalties was crucial", "moment"),
                ("The match is known as the 'Miracle of Istanbul'", "legacy"),
            ],
            "Manchester City 3-2 QPR 2012": [
                ("Sergio Aguero scored in 93:20 to win City's first title in 44 years", "moment"),
                ("Martin Tyler's 'AGUEROOOO' commentary became iconic", "legacy"),
                ("City trailed QPR 2-1 with minutes to go", "match_detail"),
            ],
            "Liverpool 4-0 Barcelona 2019": [
                ("Liverpool overturned a 3-0 first leg deficit to reach Champions League final", "match_detail"),
                ("Trent Alexander-Arnold's quick corner to Origi is one of the greatest moments", "moment"),
                ("Divock Origi scored twice in the comeback win", "statistic"),
            ],
            "Manchester United 2-1 Bayern Munich 1999": [
                ("Teddy Sheringham and Ole Gunnar Solskjaer scored in injury time", "moment"),
                ("United completed the treble with this Champions League final win", "trophy"),
                ("The Camp Nou witnessed one of football's greatest comebacks", "legacy"),
            ],

            # Players
            "Steven Gerrard": [
                ("Steven Gerrard scored 186 goals in 710 appearances for Liverpool", "statistic"),
                ("Gerrard captained Liverpool to Champions League glory in 2005", "achievement"),
                ("Gerrard is widely regarded as one of the greatest midfielders in Premier League history", "legacy"),
            ],
            "Wayne Rooney": [
                ("Wayne Rooney is Manchester United's all-time top scorer with 253 goals", "statistic"),
                ("Rooney won 5 Premier League titles and 1 Champions League with United", "trophy"),
                ("Rooney made his England debut aged 17 against Australia in 2003", "milestone"),
            ],
            "Sergio Aguero": [
                ("Sergio Aguero scored 260 goals for Manchester City, the club's all-time top scorer", "statistic"),
                ("Aguero won 5 Premier League titles with Manchester City", "trophy"),
                ("His goal against QPR in 2012 is considered the most dramatic in Premier League history", "legacy"),
            ],
        }

        added = 0
        if entity_name in predefined_facts:
            for content, fact_type in predefined_facts[entity_name]:
                if self.add_fact(content, fact_type, "curated", [entity_name]):
                    added += 1

        return added

    def enrich_entity(self, entity_name: str, entity_type: str = "person") -> Dict:
        """
        Enrich KB with facts about an entity.

        Returns dict with enrichment results.
        """
        result = {
            "entity": entity_name,
            "facts_before": self.count_entity_facts(entity_name),
            "facts_added": 0,
            "source": None
        }

        # First try predefined facts (most reliable)
        added = self.enrich_from_predefined(entity_name, entity_type)
        if added > 0:
            result["facts_added"] = added
            result["source"] = "curated"
            result["facts_after"] = self.count_entity_facts(entity_name)
            return result

        # Could add web search here in the future
        # For now, return with predefined only

        result["facts_after"] = self.count_entity_facts(entity_name)
        return result


# Singleton
_enrichment_instance = None

def get_enrichment() -> WebEnrichment:
    global _enrichment_instance
    if _enrichment_instance is None:
        _enrichment_instance = WebEnrichment()
    return _enrichment_instance


def enrich_sparse_entities(entities: List[tuple]) -> int:
    """
    Enrich entities that have sparse KB facts.
    Called after KG entity extraction.

    Returns: number of facts added
    """
    enrichment = get_enrichment()
    total_added = 0

    for name, entity_type in entities:
        if enrichment.needs_enrichment(name):
            result = enrichment.enrich_entity(name, entity_type)
            total_added += result.get("facts_added", 0)

    return total_added


# Quick test
if __name__ == "__main__":
    enrichment = get_enrichment()

    # Test enrichment
    test_entities = [
        ("Alex Ferguson", "person"),
        ("Liverpool 3-3 AC Milan 2005", "match"),
        ("Steven Gerrard", "person"),
    ]

    for name, etype in test_entities:
        print(f"\n=== Enriching: {name} ===")
        result = enrichment.enrich_entity(name, etype)
        print(f"  Facts before: {result['facts_before']}")
        print(f"  Facts added: {result['facts_added']}")
        print(f"  Facts after: {result.get('facts_after', 'N/A')}")
