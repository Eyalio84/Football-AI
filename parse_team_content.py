"""
Team Content Parser for Soccer-AI KG

Parses markdown files with Wikipedia-extracted content
and ingests into the 500-node KG database.

Usage:
    python parse_team_content.py /path/to/team/folder
"""

import sqlite3
import json
import re
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# KG Database path
KG_DB = Path(__file__).parent / "soccer_ai_architecture_kg.db"


class TeamContentParser:
    """
    Parses markdown content and extracts:
    - Club info
    - Players (legends, current)
    - Managers
    - Historic matches
    - Facts (trophies, records)
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(KG_DB)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # Track what we add
        self.stats = {
            "nodes_added": 0,
            "edges_added": 0,
            "facts_added": 0
        }

    def _node_exists(self, name: str) -> Optional[int]:
        """Check if node exists, return node_id if so."""
        self.cursor.execute("SELECT node_id FROM kg_nodes WHERE LOWER(name) = LOWER(?)", (name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def add_node(self, name: str, node_type: str, description: str = "", properties: dict = None) -> int:
        """Add a node to the KG, return node_id (auto-incremented)."""
        existing = self._node_exists(name)
        if existing:
            return existing

        props_json = json.dumps(properties or {})

        self.cursor.execute("""
            INSERT INTO kg_nodes (name, type, description, properties)
            VALUES (?, ?, ?, ?)
        """, (name, node_type, description, props_json))

        node_id = self.cursor.lastrowid

        self.stats["nodes_added"] += 1
        return node_id

    def add_edge(self, from_node: str, to_node: str, relationship: str, properties: dict = None):
        """Add an edge between nodes."""
        # Check if edge exists
        self.cursor.execute("""
            SELECT 1 FROM kg_edges
            WHERE from_node = ? AND to_node = ? AND relationship = ?
        """, (from_node, to_node, relationship))

        if self.cursor.fetchone():
            return  # Edge exists

        props_json = json.dumps(properties or {})
        self.cursor.execute("""
            INSERT INTO kg_edges (from_node, to_node, relationship, properties)
            VALUES (?, ?, ?, ?)
        """, (from_node, to_node, relationship, props_json))

        self.stats["edges_added"] += 1

    def add_fact(self, content: str, fact_type: str, confidence: float = 0.9,
                 source_type: str = "wikipedia", related_entity: str = None):
        """Add a fact to the KB."""
        # Check if fact exists
        self.cursor.execute("SELECT 1 FROM kb_facts WHERE content = ?", (content,))
        if self.cursor.fetchone():
            return

        entities_json = json.dumps([related_entity]) if related_entity else None

        self.cursor.execute("""
            INSERT INTO kb_facts (content, fact_type, confidence, source_type, related_entities)
            VALUES (?, ?, ?, ?, ?)
        """, (content, fact_type, confidence, source_type, entities_json))

        self.stats["facts_added"] += 1

    def parse_club_info(self, text: str, club_name: str) -> str:
        """Extract club info and add to KG."""
        # Add club node
        description = ""

        # Extract description from first paragraph
        paragraphs = text.split('\n\n')
        if paragraphs:
            description = paragraphs[0][:500]  # First 500 chars

        # Extract properties
        props = {}

        # Stadium
        stadium_match = re.search(r'Ground\s+([A-Z][a-z\s]+)', text)
        if stadium_match:
            props["stadium"] = stadium_match.group(1).strip()

        # Capacity
        capacity_match = re.search(r'Capacity\s+([\d,]+)', text)
        if capacity_match:
            props["capacity"] = capacity_match.group(1).replace(',', '')

        # Founded
        founded_match = re.search(r'Founded\s+(\d{4})', text)
        if founded_match:
            props["founded"] = founded_match.group(1)

        # Nickname
        nickname_match = re.search(r'Nickname[s]?\s+([^\n]+)', text)
        if nickname_match:
            props["nickname"] = nickname_match.group(1).strip()

        club_id = self.add_node(club_name, "club", description, props)

        # Add founding fact
        if props.get("founded"):
            self.add_fact(
                f"{club_name} was founded in {props['founded']}",
                "founding",
                0.95,
                "wikipedia",
                club_id
            )

        return club_id

    def parse_trophies(self, text: str, club_id: str, club_name: str):
        """Extract trophy counts and add facts."""
        # Better patterns that match PDF-extracted format
        # Format: "Trophy Name COUNT YEAR, YEAR..." or "won COUNT Trophy"
        trophy_patterns = [
            # "won X league titles" or "X league titles"
            (r'won\s+(\d{1,2})\s+(?:league|top[- ]flight)\s+titles?', "league titles"),
            (r'(\d{1,2})\s+(?:league|top[- ]flight)\s+titles?', "league titles"),
            # "FA Cup X" followed by years (PDF format: "FA Cup 81965,")
            (r'FA Cup\s+(\d{1,2})(?:19|20)', "FA Cups"),
            # "League Cup X" followed by years
            (r'League Cup\s+(\d{1,2})(?:19|20)', "League Cups"),
            # "Champions League X" or "European Cup X"
            (r'(?:Champions League|European Cup)[^\d]*(\d{1,2})(?:19|20)', "European Cups"),
            # "won the [trophy] X times"
            (r'won the (FA Cup|League Cup|Champions League)[^\d]*(\d{1,2})\s+times', None),
            # Direct count patterns with reasonable bounds (1-25)
            (r'Premier League[/\s]+(\d{1,2})(?:\s|$|[,\[])', "Premier League titles"),
            (r'First Division[/\s]+(\d{1,2})(?:\s|$|[,\[])', "First Division titles"),
        ]

        found_trophies = set()  # Avoid duplicates

        for pattern, trophy_name in trophy_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if trophy_name is None:
                    # Pattern captures trophy name in group 1, count in group 2
                    trophy_name = match.group(1) + "s"
                    count = match.group(2)
                else:
                    count = match.group(1)

                # Sanity check: trophy count should be 1-25
                try:
                    count_int = int(count)
                    if count_int < 1 or count_int > 25:
                        continue
                except:
                    continue

                fact_key = f"{club_name}_{trophy_name}"
                if fact_key not in found_trophies:
                    found_trophies.add(fact_key)
                    self.add_fact(
                        f"{club_name} has won {count} {trophy_name}",
                        "trophy",
                        0.95,
                        "wikipedia",
                        club_id
                    )

    def parse_player_appearances(self, text: str, club_id: str, club_name: str):
        """Extract player appearances and add nodes/edges."""
        # Pattern for player rows
        # Name | Nationality | Position | Years | Apps | Goals
        player_pattern = re.compile(
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(England|Scotland|Wales|Ireland|Northern Ireland)\s+(GK|FB|HB|FW|MF|DF)\s+(\d{4}[–-]\d{4})',
            re.MULTILINE
        )

        for match in player_pattern.finditer(text):
            name = match.group(1).strip()
            nationality = match.group(2)
            position = match.group(3)
            years = match.group(4)

            # Get appearances if available
            line = text[match.start():match.end()+100]
            apps_match = re.search(r'(\d{2,3})\s+\d+\s+\d{2,3}', line)

            props = {
                "nationality": nationality,
                "position": position,
                "years_at_club": years
            }

            if apps_match:
                props["appearances"] = apps_match.group(1)

            # Add player node
            player_id = self.add_node(
                name,
                "person",
                f"{nationality} footballer who played for {club_name}",
                props
            )

            # Add played_for edge
            self.add_edge(player_id, club_id, "played_for", {"years": years})

    def parse_manager_info(self, text: str, club_id: str, club_name: str):
        """Extract manager info from Ferguson-style bios."""
        # Look for manager career section
        manager_pattern = re.compile(
            r'(\d{4}[–-]\d{4})\s+(Manchester United|Liverpool|Chelsea|Arsenal|Manchester City)',
            re.IGNORECASE
        )

        # Find manager name at start
        name_match = re.search(r'^([A-Z][a-z]+\s+(?:[A-Z][a-z]+\s+)?[A-Z][a-z]+)', text)
        if not name_match:
            return

        manager_name = name_match.group(1).strip()

        # Check if this is a manager bio
        if "manager" not in text.lower() and "managed" not in text.lower():
            return

        # Extract key info
        props = {}

        # Birth date
        birth_match = re.search(r'born\s+(\d{1,2}\s+\w+\s+\d{4})', text, re.IGNORECASE)
        if birth_match:
            props["birth_date"] = birth_match.group(1)

        # Trophies won
        trophies_match = re.search(r'(\d+)\s+trophies', text, re.IGNORECASE)
        if trophies_match:
            props["total_trophies"] = trophies_match.group(1)

        # Add manager node
        description = f"Football manager who managed {club_name}"
        manager_id = self.add_node(manager_name, "person", description, props)

        # Add managed edge
        years_match = re.search(r'(\d{4})[–-](\d{4})\s+' + re.escape(club_name), text, re.IGNORECASE)
        if years_match:
            self.add_edge(manager_id, club_id, "managed", {
                "start_year": years_match.group(1),
                "end_year": years_match.group(2)
            })

        # Add key facts
        if "greatest" in text.lower() or "best" in text.lower():
            self.add_fact(
                f"{manager_name} is widely regarded as one of the greatest football managers",
                "achievement",
                0.9,
                "wikipedia",
                manager_id
            )

    def parse_historic_match(self, text: str, club_id: str):
        """Extract historic match info."""
        # Match pattern: "Team A X-X Team B (Year)"
        match_pattern = re.compile(
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(\d)[–-](\d)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\((\d{4})\)'
        )

        for match in match_pattern.finditer(text):
            team1, score1, score2, team2, year = match.groups()

            match_name = f"{team1} {score1}-{score2} {team2} {year}"

            # Get context (100 chars before and after)
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 200)
            context = text[start:end]

            # Add match node
            description = f"Historic match between {team1} and {team2} in {year}"
            match_id = self.add_node(match_name, "match", description, {
                "score": f"{score1}-{score2}",
                "year": year,
                "teams": [team1, team2]
            })

            # Add fact with context
            self.add_fact(
                f"{match_name}: {context[:200]}",
                "match_detail",
                0.9,
                "wikipedia",
                match_id
            )

    def parse_markdown_file(self, filepath: str, club_name: str):
        """Parse a markdown file and extract all content."""
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()

        # Determine club name if not provided
        if not club_name:
            # Try to extract from content
            club_match = re.search(r'([\w\s]+)\s+Football Club', text)
            if club_match:
                club_name = club_match.group(1).strip()
            else:
                club_name = Path(filepath).stem

        print(f"  Parsing for: {club_name}")

        # Add club first
        club_id = self.parse_club_info(text, club_name)

        # Parse different sections
        self.parse_trophies(text, club_id, club_name)
        self.parse_player_appearances(text, club_id, club_name)
        self.parse_manager_info(text, club_id, club_name)
        self.parse_historic_match(text, club_id)

        # Commit after each file
        self.conn.commit()

    def parse_folder(self, folder_path: str, club_name: str = None):
        """Parse all markdown files in a folder."""
        folder = Path(folder_path)

        if not folder.exists():
            print(f"Folder not found: {folder}")
            return

        # Get club name from folder if not provided
        if not club_name:
            club_name = folder.name.title()

        print(f"\n=== Parsing {club_name} ===")

        # Find markdown files
        md_files = list(folder.glob("*.md"))

        for md_file in md_files:
            print(f"  File: {md_file.name}")
            self.parse_markdown_file(str(md_file), club_name)

        print(f"  Stats: +{self.stats['nodes_added']} nodes, +{self.stats['edges_added']} edges, +{self.stats['facts_added']} facts")

    def close(self):
        """Close database connection."""
        self.conn.commit()
        self.conn.close()


def main():
    """Main entry point."""
    parser_path = Path("/storage/emulated/0/Download/Manchester/parser")

    parser = TeamContentParser()

    # Parse the existing markdown files first
    print("=== Parsing part1.md and part2.md ===")
    parser.parse_markdown_file(str(parser_path / "part1.md"), "Manchester United")
    parser.parse_markdown_file(str(parser_path / "part2.md"), "Manchester United")

    # Parse each team folder
    team_folders = [
        ("Liverpool", "Liverpool"),
        ("Manchster city", "Manchester City"),  # Note typo in folder name
        ("arsenal", "Arsenal"),
        ("aston villa", "Aston Villa"),
        ("chelsea", "Chelsea"),
        ("newcastle", "Newcastle United"),
        ("tottenham", "Tottenham Hotspur"),
        ("west ham", "West Ham United"),
        ("leeds", "Leeds United"),
        ("leicester", "Leicester City"),
        ("sunderland", "Sunderland"),
        ("bournemouth", None),
    ]

    for folder_name, club_name in team_folders:
        folder = parser_path / folder_name
        if folder.exists():
            parser.parse_folder(str(folder), club_name)

    print("\n=== Final Stats ===")
    print(f"Total nodes added: {parser.stats['nodes_added']}")
    print(f"Total edges added: {parser.stats['edges_added']}")
    print(f"Total facts added: {parser.stats['facts_added']}")

    parser.close()


if __name__ == "__main__":
    main()
