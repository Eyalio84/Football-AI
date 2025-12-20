"""
KG-KB-RAG Integration for Soccer-AI Backend

Bridges the new 500-node knowledge graph with the existing backend.
Provides enhanced context retrieval for fan persona responses.
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Path to the new 500-node KG database
KG_DB_PATH = Path(__file__).parent / "unified_soccer_ai_kg.db"


class KGIntegration:
    """
    Integration layer for the 500-node Soccer-AI Knowledge Graph.

    Provides:
    - Entity lookup (players, managers, clubs, stadiums)
    - Relationship traversal (played_for, managed, rival_of)
    - KB fact retrieval (FTS5 search)
    - Combined context for RAG
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(KG_DB_PATH)
        self._load_entities()

    def _get_conn(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)

    def _load_entities(self):
        """Load entity names for quick matching."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT node_id, name, type FROM kg_nodes")
            self.entities = {row[1].lower(): (row[0], row[1], row[2]) for row in cursor.fetchall()}
            conn.close()
        except:
            self.entities = {}

        # Common aliases
        self.aliases = {
            # Club aliases
            "united": "manchester united",
            "man utd": "manchester united",
            "man u": "manchester united",
            "city": "manchester city",
            "man city": "manchester city",
            "spurs": "tottenham hotspur",
            "tottenham": "tottenham hotspur",
            "the reds": "liverpool",
            "the gunners": "arsenal",
            "the blues": "chelsea",
            "wolves": "wolverhampton wanderers",
            "villa": "aston villa",
            "hammers": "west ham united",
            "west ham": "west ham united",
            "toon": "newcastle united",
            "toffees": "everton",
            # Manager aliases
            "fergie": "alex ferguson",
            "sir alex": "alex ferguson",
            "ferguson": "alex ferguson",
            "pep": "pep guardiola",
            "guardiola": "pep guardiola",
            "klopp": "jurgen klopp",
            "mourinho": "jose mourinho",
            "wenger": "arsene wenger",
            "ancelotti": "carlo ancelotti",
            # Current managers (2024-25)
            "slot": "arne slot",
            "arteta": "mikel arteta",
            "maresca": "enzo maresca",
            "postecoglou": "ange postecoglou",
            "ange": "ange postecoglou",
            "howe": "eddie howe",
            "emery": "unai emery",
            "frank": "thomas frank",
            "dyche": "sean dyche",
            "amorim": "ruben amorim",
            "glasner": "oliver glasner",
            "iraola": "andoni iraola",
            "silva": "marco silva",
            "lopetegui": "julen lopetegui",
            "nuno": "nuno espirito santo",
            # Player aliases
            "ronaldo": "cristiano ronaldo",
            "cr7": "cristiano ronaldo",
            "messi": "lionel messi",
            "becks": "david beckham",
            "king eric": "eric cantona",
            "cantona": "eric cantona",
            "gerrard": "steven gerrard",
            "lampard": "frank lampard",
            "henry": "thierry henry",
            "shearer": "alan shearer",
            "rooney": "wayne rooney",
            "aguero": "sergio aguero",
            "kun": "sergio aguero",
            "salah": "mohamed salah",
            "haaland": "erling haaland",
            # Derby aliases
            "north london derby": "north london derby",
            "nld": "north london derby",
            "merseyside derby": "merseyside derby",
            "manchester derby": "manchester derby",
            "northwest derby": "northwest derby",
            "m23 derby": "m23 derby",
            "tyne-wear derby": "tyne-wear derby",
            "second city derby": "second city derby",
            "east midlands derby": "east midlands derby",
            # Match aliases (matching actual KG node names)
            "6-1 derby": "manchester city 6-1 manchester united 2011",
            "aguero moment": "manchester city 3-2 qpr 2012",
            "93:20": "manchester city 3-2 qpr 2012",
            "qpr": "manchester city 3-2 qpr 2012",
            "istanbul": "liverpool 3-3 ac milan 2005",
            "miracle of istanbul": "liverpool 3-3 ac milan 2005",
            "treble final": "manchester united 2-1 bayern munich 1999",
            "camp nou 1999": "manchester united 2-1 bayern munich 1999",
            "anfield 4-0": "liverpool 4-0 barcelona 2019",
            "corner taken quickly": "liverpool 4-0 barcelona 2019",
            "8-2": "manchester united 8-2 arsenal 2011",
            "4-4 anfield": "arsenal 4-4 liverpool 2009",
        }

    def find_entities(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Find entities mentioned in text.

        Returns: List of (node_id, name, type) tuples
        """
        text_lower = text.lower()
        found = []

        # Check aliases first
        for alias, canonical in self.aliases.items():
            if alias in text_lower and canonical in self.entities:
                node_id, name, node_type = self.entities[canonical]
                if (node_id, name, node_type) not in found:
                    found.append((node_id, name, node_type))

        # Check direct entity names
        for name_lower, (node_id, name, node_type) in self.entities.items():
            if name_lower in text_lower:
                if (node_id, name, node_type) not in found:
                    found.append((node_id, name, node_type))

        return found

    def get_entity_context(self, entity_name: str, include_relationships: bool = True) -> Dict:
        """
        Get full context for an entity.

        Returns dict with:
        - entity: name, type, description, properties
        - relationships: list of connected entities
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        # Get node info
        cursor.execute("""
            SELECT node_id, name, type, description, properties
            FROM kg_nodes WHERE LOWER(name) = LOWER(?)
        """, (entity_name,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        node_id, name, node_type, desc, props = row
        props_dict = json.loads(props) if props else {}

        result = {
            "entity": {
                "name": name,
                "type": node_type,
                "description": desc,
                "properties": props_dict
            },
            "relationships": []
        }

        if include_relationships:
            # Get outgoing relationships
            cursor.execute("""
                SELECT e.relationship, e.properties, n.name, n.type
                FROM kg_edges e
                JOIN kg_nodes n ON e.to_node = n.node_id
                WHERE e.from_node = ?
            """, (node_id,))

            for rel, rel_props, target_name, target_type in cursor.fetchall():
                rel_props_dict = json.loads(rel_props) if rel_props else {}
                result["relationships"].append({
                    "direction": "outgoing",
                    "relationship": rel,
                    "target": target_name,
                    "target_type": target_type,
                    "properties": rel_props_dict
                })

            # Get incoming relationships
            cursor.execute("""
                SELECT e.relationship, e.properties, n.name, n.type
                FROM kg_edges e
                JOIN kg_nodes n ON e.from_node = n.node_id
                WHERE e.to_node = ?
            """, (node_id,))

            for rel, rel_props, source_name, source_type in cursor.fetchall():
                rel_props_dict = json.loads(rel_props) if rel_props else {}
                result["relationships"].append({
                    "direction": "incoming",
                    "relationship": rel,
                    "source": source_name,
                    "source_type": source_type,
                    "properties": rel_props_dict
                })

        conn.close()
        return result

    def search_facts(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search KB facts using FTS5.

        Returns list of matching facts with confidence scores.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        # Clean query for FTS
        import re
        search_terms = re.sub(r'[^\w\s]', '', query)

        facts = []
        try:
            cursor.execute("""
                SELECT f.fact_id, f.content, f.fact_type, f.confidence, f.source_type
                FROM kb_facts f
                JOIN kb_facts_fts fts ON f.fact_id = fts.rowid
                WHERE kb_facts_fts MATCH ?
                ORDER BY f.confidence DESC
                LIMIT ?
            """, (search_terms, limit))

            for row in cursor.fetchall():
                facts.append({
                    "fact_id": row[0],
                    "content": row[1],
                    "type": row[2],
                    "confidence": row[3],
                    "source": row[4]
                })
        except:
            pass  # FTS might fail on complex queries

        conn.close()
        return facts

    def get_club_players(self, club_name: str, current_only: bool = False) -> List[Dict]:
        """Get players for a club."""
        conn = self._get_conn()
        cursor = conn.cursor()

        # Get club node_id
        cursor.execute("SELECT node_id FROM kg_nodes WHERE LOWER(name) = LOWER(?)", (club_name,))
        club_row = cursor.fetchone()
        if not club_row:
            conn.close()
            return []

        club_id = club_row[0]

        # Get players with played_for or plays_for edges
        query = """
            SELECT n.name, n.description, e.relationship, e.properties
            FROM kg_nodes n
            JOIN kg_edges e ON n.node_id = e.from_node
            WHERE e.to_node = ? AND e.relationship IN ('played_for', 'plays_for')
            AND n.type = 'person'
        """

        cursor.execute(query, (club_id,))

        players = []
        for name, desc, rel, props in cursor.fetchall():
            props_dict = json.loads(props) if props else {}
            is_current = rel == 'plays_for' or props_dict.get('current', False)

            if current_only and not is_current:
                continue

            players.append({
                "name": name,
                "description": desc,
                "current": is_current,
                "properties": props_dict
            })

        conn.close()
        return players

    def get_enhanced_context(self, query: str, club: str = None) -> Dict:
        """
        Get enhanced context for a query, combining KG and KB.

        This is the main entry point for RAG enhancement.
        """
        # Find entities in query
        entities = self.find_entities(query)

        # If club specified, add it
        if club and club.lower().replace("_", " ") in self.entities:
            club_name = club.replace("_", " ").title()
            if club_name.lower() in self.entities:
                entity_info = self.entities[club_name.lower()]
                if entity_info not in entities:
                    entities.append(entity_info)

        # Get context for each entity
        entity_contexts = []
        for node_id, name, node_type in entities[:5]:  # Limit to 5 entities
            ctx = self.get_entity_context(name)
            if ctx:
                entity_contexts.append(ctx)

        # Search facts using resolved entity names AND query keywords
        facts = []
        entity_names = [name for _, name, _ in entities]

        # First, search by entity names
        if entity_names:
            for entity_name in entity_names[:3]:  # Top 3 entities
                entity_facts = self.search_facts(entity_name, limit=5)
                for f in entity_facts:
                    if f not in facts:
                        facts.append(f)

        # Also search for important pattern keywords in the query
        # Map query terms to FTS search terms (including plurals)
        pattern_keyword_map = {
            'comeback': 'comebacks',  # Pattern facts use plural
            'comebacks': 'comebacks',
            'golden era': '"golden era"',
            'golden': '"golden era"',
            'bogey': 'bogey',
            'derby': 'derby',
            'dominance': 'dominance',
            'fortress': 'fortress',
            'rivalry': 'rivalry',
            'legend': 'legend',
            'chant': 'chant',
            'streak': 'streak',
        }
        query_lower = query.lower()
        searched_keywords = set()
        for query_term, fts_term in pattern_keyword_map.items():
            if query_term in query_lower and fts_term not in searched_keywords:
                searched_keywords.add(fts_term)
                keyword_facts = self.search_facts(fts_term, limit=5)
                for f in keyword_facts:
                    if f not in facts:
                        facts.append(f)

        # Fallback to raw query if nothing found
        if not facts:
            facts = self.search_facts(query, limit=10)

        # Build combined context string
        context_parts = []

        if entity_contexts:
            context_parts.append("=== Knowledge Graph ===")
            for ctx in entity_contexts:
                e = ctx["entity"]
                context_parts.append(f"• {e['name']} ({e['type']}): {e.get('description', '')}")
                for rel in ctx["relationships"][:5]:  # Limit relationships
                    if rel["direction"] == "outgoing":
                        context_parts.append(f"  → {rel['relationship']} → {rel['target']}")
                    else:
                        context_parts.append(f"  ← {rel['source']} → {rel['relationship']}")

        if facts:
            context_parts.append("\n=== Facts ===")
            for f in facts:
                conf = f"[{f['confidence']:.0%}]" if f.get('confidence') else ""
                context_parts.append(f"• {conf} {f['content']}")

        return {
            "entities_found": [(name, node_type) for _, name, node_type in entities],
            "entity_contexts": entity_contexts,
            "facts": facts,
            "combined_context": "\n".join(context_parts),
            "kg_stats": {
                "entities_matched": len(entities),
                "relationships_found": sum(len(ctx.get("relationships", [])) for ctx in entity_contexts),
                "facts_found": len(facts)
            }
        }

    def get_stats(self) -> Dict:
        """Get KG statistics."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM kg_nodes")
        nodes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM kg_edges")
        edges = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM kb_facts")
        facts = cursor.fetchone()[0]

        cursor.execute("SELECT type, COUNT(*) FROM kg_nodes GROUP BY type ORDER BY COUNT(*) DESC")
        node_types = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            "total_nodes": nodes,
            "total_edges": edges,
            "total_facts": facts,
            "node_types": node_types
        }


# Singleton instance
_kg_instance = None

def get_kg() -> KGIntegration:
    """Get the KG integration singleton."""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = KGIntegration()
    return _kg_instance


# Quick test
if __name__ == "__main__":
    kg = get_kg()

    print("=== KG Stats ===")
    stats = kg.get_stats()
    print(f"Nodes: {stats['total_nodes']}")
    print(f"Edges: {stats['total_edges']}")
    print(f"Facts: {stats['total_facts']}")

    print("\n=== Test Query ===")
    result = kg.get_enhanced_context("Tell me about Liverpool legends", club="liverpool")
    print(result["combined_context"][:1000])
