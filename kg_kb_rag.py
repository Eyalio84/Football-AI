#!/usr/bin/env python3
"""
KG-KB-RAG Query Engine for Soccer-AI

Architecture:
- KG (Knowledge Graph): Structured relationships (nodes, edges)
- KB (Knowledge Base): Unstructured facts with FTS5 search
- RAG (Retrieval-Augmented Generation): Query → Retrieve → Generate

Query Flow:
1. Parse query for entities and intent
2. KG traversal: Find related entities via edges
3. KB search: FTS5 search for relevant facts
4. Combine: Merge KG structure + KB content
5. Return: Context ready for LLM generation
"""

import sqlite3
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class QueryResult:
    """Result from KG-KB-RAG query."""
    query: str
    entities_found: List[str]
    kg_context: List[Dict]  # Related nodes and edges
    kb_facts: List[Dict]    # Relevant facts from KB
    combined_context: str   # Ready for LLM


class SoccerAIRAG:
    """
    KG-KB-RAG engine for soccer knowledge retrieval.

    Usage:
        rag = SoccerAIRAG()
        result = rag.query("Who won more Premier League titles, United or City?")
        print(result.combined_context)
    """

    def __init__(self, db_path: str = "soccer_ai_architecture_kg.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        # Load entity names for matching
        self.cursor.execute("SELECT node_id, name, type FROM kg_nodes")
        self.entities = {row[1].lower(): (row[0], row[1], row[2]) for row in self.cursor.fetchall()}

        # Common aliases
        self.aliases = {
            "united": "manchester united",
            "man utd": "manchester united",
            "man united": "manchester united",
            "city": "manchester city",
            "man city": "manchester city",
            "liverpool": "liverpool",
            "arsenal": "arsenal",
            "chelsea": "chelsea",
            "spurs": "tottenham hotspur",
            "tottenham": "tottenham hotspur",
            "fergie": "alex ferguson",
            "ferguson": "alex ferguson",
            "sir alex": "alex ferguson",
            "pl": "premier league",
        }

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entity mentions from query."""
        query_lower = query.lower()
        found = []

        # Check aliases first
        for alias, canonical in self.aliases.items():
            if alias in query_lower:
                if canonical in self.entities:
                    found.append(self.entities[canonical][1])  # Return proper name

        # Check full entity names
        for name_lower, (node_id, name, node_type) in self.entities.items():
            if name_lower in query_lower and name not in found:
                found.append(name)

        return found

    def _kg_traverse(self, entity_names: List[str], depth: int = 1) -> List[Dict]:
        """Traverse KG from given entities."""
        context = []

        for entity_name in entity_names:
            # Get node info
            self.cursor.execute("""
                SELECT node_id, name, type, description, properties
                FROM kg_nodes WHERE name = ?
            """, (entity_name,))
            node = self.cursor.fetchone()
            if not node:
                continue

            node_id, name, node_type, desc, props = node
            props_dict = json.loads(props) if props else {}

            context.append({
                "type": "entity",
                "name": name,
                "entity_type": node_type,
                "description": desc,
                "properties": props_dict
            })

            # Get outgoing edges
            self.cursor.execute("""
                SELECT e.relationship, e.properties, n.name, n.type
                FROM kg_edges e
                JOIN kg_nodes n ON e.to_node = n.node_id
                WHERE e.from_node = ?
            """, (node_id,))

            for rel, rel_props, target_name, target_type in self.cursor.fetchall():
                rel_props_dict = json.loads(rel_props) if rel_props else {}
                context.append({
                    "type": "relationship",
                    "from": name,
                    "relationship": rel,
                    "to": target_name,
                    "target_type": target_type,
                    "properties": rel_props_dict
                })

            # Get incoming edges
            self.cursor.execute("""
                SELECT e.relationship, e.properties, n.name, n.type
                FROM kg_edges e
                JOIN kg_nodes n ON e.from_node = n.node_id
                WHERE e.to_node = ?
            """, (node_id,))

            for rel, rel_props, source_name, source_type in self.cursor.fetchall():
                rel_props_dict = json.loads(rel_props) if rel_props else {}
                context.append({
                    "type": "relationship",
                    "from": source_name,
                    "relationship": rel,
                    "to": name,
                    "source_type": source_type,
                    "properties": rel_props_dict
                })

        return context

    def _kb_search(self, query: str, entity_names: List[str], limit: int = 10) -> List[Dict]:
        """Search KB for relevant facts."""
        facts = []

        # FTS5 search on query terms
        # Clean query for FTS
        search_terms = re.sub(r'[^\w\s]', '', query)

        try:
            self.cursor.execute("""
                SELECT f.fact_id, f.content, f.fact_type, f.confidence, f.source_type
                FROM kb_facts f
                JOIN kb_facts_fts fts ON f.fact_id = fts.rowid
                WHERE kb_facts_fts MATCH ?
                ORDER BY f.confidence DESC
                LIMIT ?
            """, (search_terms, limit))

            for row in self.cursor.fetchall():
                facts.append({
                    "fact_id": row[0],
                    "content": row[1],
                    "type": row[2],
                    "confidence": row[3],
                    "source": row[4]
                })
        except:
            pass  # FTS might fail on complex queries

        # Also get facts linked to mentioned entities
        for entity_name in entity_names:
            self.cursor.execute("""
                SELECT f.fact_id, f.content, f.fact_type, f.confidence, f.source_type
                FROM kb_facts f
                JOIN kb_entity_facts ef ON f.fact_id = ef.fact_id
                JOIN kg_nodes n ON ef.entity_id = n.node_id
                WHERE n.name = ?
                AND f.fact_id NOT IN (SELECT fact_id FROM kb_facts WHERE fact_id IN (%s))
                LIMIT ?
            """ % ','.join(['?']*len(facts) if facts else ['0']),
            (entity_name, *[f['fact_id'] for f in facts], limit))

            for row in self.cursor.fetchall():
                facts.append({
                    "fact_id": row[0],
                    "content": row[1],
                    "type": row[2],
                    "confidence": row[3],
                    "source": row[4],
                    "linked_entity": entity_name
                })

        return facts[:limit]

    def _build_context(self, query: str, entities: List[str],
                       kg_context: List[Dict], kb_facts: List[Dict]) -> str:
        """Build combined context for LLM."""
        lines = []
        lines.append(f"Query: {query}")
        lines.append(f"Entities mentioned: {', '.join(entities)}")
        lines.append("")

        # KG context
        lines.append("=== Knowledge Graph Context ===")
        for item in kg_context:
            if item["type"] == "entity":
                lines.append(f"• {item['name']} ({item['entity_type']}): {item.get('description', '')}")
                if item.get('properties'):
                    for k, v in item['properties'].items():
                        if k not in ['created']:
                            lines.append(f"  - {k}: {v}")
            elif item["type"] == "relationship":
                props_str = ""
                if item.get('properties'):
                    props_str = f" [{item['properties']}]"
                lines.append(f"• {item['from']} --{item['relationship']}--> {item['to']}{props_str}")

        lines.append("")
        lines.append("=== Knowledge Base Facts ===")
        for fact in kb_facts:
            conf = f"[{fact['confidence']:.0%}]" if fact.get('confidence') else ""
            lines.append(f"• {conf} {fact['content']}")

        return "\n".join(lines)

    def query(self, query: str, kg_depth: int = 1, kb_limit: int = 10) -> QueryResult:
        """
        Execute KG-KB-RAG query.

        Args:
            query: Natural language question
            kg_depth: How deep to traverse KG
            kb_limit: Max facts to retrieve from KB

        Returns:
            QueryResult with combined context
        """
        # 1. Extract entities
        entities = self._extract_entities(query)

        # 2. KG traversal
        kg_context = self._kg_traverse(entities, depth=kg_depth)

        # 3. KB search
        kb_facts = self._kb_search(query, entities, limit=kb_limit)

        # 4. Build combined context
        combined = self._build_context(query, entities, kg_context, kb_facts)

        return QueryResult(
            query=query,
            entities_found=entities,
            kg_context=kg_context,
            kb_facts=kb_facts,
            combined_context=combined
        )

    def close(self):
        self.conn.close()


def main():
    """Test the RAG engine."""
    rag = SoccerAIRAG()

    test_queries = [
        "Who has won more Premier League titles, Manchester United or Manchester City?",
        "Tell me about the 4-3 Manchester derby",
        "What did Ferguson achieve at United?",
        "What are the biggest rivalries in English football?",
    ]

    for query in test_queries:
        print("\n" + "="*60)
        result = rag.query(query)
        print(result.combined_context)

    rag.close()


if __name__ == "__main__":
    main()
