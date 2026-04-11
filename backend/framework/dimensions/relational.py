"""
Relational Dimension Computer (Y-axis)
=======================================

Computes position in knowledge graph.

The persona exists within a web of relationships:
- Rivals, allies, legends
- Prerequisites, concepts, topics
- Ideas, connections, domains

When a related entity is mentioned, the relationship activates
and colors the persona's response.

Author: Eyal Nof
Date: December 28, 2025
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Tuple
from abc import ABC, abstractmethod
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from persona_engine import DimensionComputer, RelationalState


class KnowledgeGraph:
    """
    Simple knowledge graph for relationship lookup.

    In production, this would connect to a real KG (Neo4j, etc.)
    """

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: Dict[str, List[Tuple[str, str, Dict[str, Any]]]] = {}

    def add_node(self, node_id: str, properties: Dict[str, Any] = None):
        """Add a node to the graph."""
        self.nodes[node_id] = properties or {}

    def add_edge(self, from_node: str, to_node: str, relation_type: str, properties: Dict[str, Any] = None):
        """Add an edge between nodes."""
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append((to_node, relation_type, properties or {}))

    def get_neighbors(self, node_id: str, relation_type: str = None) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Get neighbors of a node, optionally filtered by relation type."""
        if node_id not in self.edges:
            return []

        neighbors = self.edges[node_id]
        if relation_type:
            neighbors = [(n, r, p) for n, r, p in neighbors if r == relation_type]
        return neighbors

    def find_relationship(self, from_node: str, to_node: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find the relationship between two nodes."""
        if from_node not in self.edges:
            return None

        for target, relation, props in self.edges[from_node]:
            if target.lower() == to_node.lower():
                return (relation, props)
        return None


class RelationalComputer(DimensionComputer):
    """
    Abstract base for relational dimension computation.

    Subclasses implement domain-specific knowledge graphs:
    - Football: clubs, rivals, legends
    - Education: topics, prerequisites, concepts
    - Architecture: ideas, connections, domains
    """

    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        self.kg = knowledge_graph or KnowledgeGraph()
        self._initialize_graph()

    @abstractmethod
    def _initialize_graph(self):
        """Initialize the knowledge graph with domain data."""
        pass

    def _detect_entities(self, text: str) -> List[str]:
        """Detect entity mentions in text."""
        detected = []
        text_lower = text.lower()

        for node_id in self.kg.nodes:
            if node_id.lower() in text_lower:
                detected.append(node_id)

        return detected

    def compute(self, context: Dict[str, Any], entity_id: str = "") -> RelationalState:
        """Compute relational state from context."""
        # Handle empty context
        if not context:
            return RelationalState(
                activated=False,
                relation_type=None,
                target=None,
                intensity=0.0,
                context={}
            )

        text = context.get('context', '')

        # Detect entities in the text
        mentioned = self._detect_entities(text)

        if not mentioned:
            return RelationalState(
                activated=False,
                relation_type=None,
                target=None,
                intensity=0.0,
                context={}
            )

        # Find the strongest relationship
        for target in mentioned:
            relationship = self.kg.find_relationship(entity_id, target)
            if relationship:
                relation_type, props = relationship
                return RelationalState(
                    activated=True,
                    relation_type=relation_type,
                    target=target,
                    intensity=props.get('intensity', 0.7),
                    context=props
                )

        return RelationalState(
            activated=False,
            relation_type=None,
            target=None,
            intensity=0.0,
            context={}
        )


class FootballRelationalComputer(RelationalComputer):
    """
    Relational computer for football fan personas.

    Knowledge graph includes:
    - Clubs and their rivals
    - Legends and their clubs
    - Managers and their history
    """

    def _initialize_graph(self):
        """Initialize football knowledge graph."""
        # Add Premier League clubs
        clubs = [
            'Arsenal', 'Chelsea', 'Liverpool', 'Manchester United',
            'Manchester City', 'Tottenham', 'Newcastle', 'West Ham',
            'Aston Villa', 'Brighton', 'Everton', 'Crystal Palace',
            'Fulham', 'Bournemouth', 'Brentford', 'Nottingham Forest',
            'Wolves', 'Ipswich', 'Leicester', 'Southampton'
        ]

        for club in clubs:
            self.kg.add_node(club, {'type': 'club'})

        # Add rivalries
        rivalries = [
            ('Arsenal', 'Tottenham', 'North London Derby'),
            ('Liverpool', 'Manchester United', 'Historic Rivalry'),
            ('Liverpool', 'Everton', 'Merseyside Derby'),
            ('Manchester United', 'Manchester City', 'Manchester Derby'),
            ('Chelsea', 'Arsenal', 'London Rivalry'),
            ('Chelsea', 'Tottenham', 'London Rivalry'),
            ('Newcastle', 'Sunderland', 'Tyne-Wear Derby'),
            ('West Ham', 'Tottenham', 'London Rivalry'),
        ]

        for club1, club2, derby_name in rivalries:
            self.kg.add_edge(club1, club2, 'rival', {
                'intensity': 0.9,
                'derby_name': derby_name,
                'banter': self._get_rivalry_banter(club1, club2)
            })
            self.kg.add_edge(club2, club1, 'rival', {
                'intensity': 0.9,
                'derby_name': derby_name,
                'banter': self._get_rivalry_banter(club2, club1)
            })

        # Add some legends
        legends = {
            'Liverpool': ['Steven Gerrard', 'Kenny Dalglish', 'Ian Rush', 'Mo Salah'],
            'Arsenal': ['Thierry Henry', 'Dennis Bergkamp', 'Patrick Vieira'],
            'Manchester United': ['Wayne Rooney', 'Eric Cantona', 'Ryan Giggs'],
            'Chelsea': ['Didier Drogba', 'Frank Lampard', 'John Terry'],
            'Tottenham': ['Harry Kane', 'Glenn Hoddle', 'Jimmy Greaves'],
        }

        for club, club_legends in legends.items():
            for legend in club_legends:
                self.kg.add_node(legend, {'type': 'player', 'club': club})
                self.kg.add_edge(club, legend, 'legend', {
                    'intensity': 0.8,
                    'reverence': 'high'
                })

    def _get_rivalry_banter(self, home_club: str, rival: str) -> List[str]:
        """Get rivalry-specific banter lines."""
        banter = {
            ('Arsenal', 'Tottenham'): [
                "Mind the gap!",
                "When was your last trophy again?",
                "St. Totteringham's Day is coming"
            ],
            ('Liverpool', 'Manchester United'): [
                "History boys, nothing more",
                "Still living in the past",
                "Welcome to the modern era"
            ],
            ('Liverpool', 'Everton'): [
                "The smaller Merseyside club",
                "Trophy cabinet looking dusty",
                "Blue isn't your color"
            ],
        }
        return banter.get((home_club, rival), ["Typical rival behavior"])


class EducationRelationalComputer(RelationalComputer):
    """
    Relational computer for education personas (Barry, Marcus).

    Knowledge graph includes:
    - Topics and prerequisites
    - Concepts and their relationships
    - Common misconceptions
    """

    def _initialize_graph(self):
        """Initialize education knowledge graph."""
        # Calculus topics
        calc1_topics = [
            'limits', 'continuity', 'derivatives', 'differentiation',
            'applications of derivatives', 'integrals', 'integration'
        ]

        calc2_topics = [
            'integration techniques', 'sequences', 'series',
            'Taylor series', 'parametric equations', 'polar coordinates'
        ]

        calc3_topics = [
            'vectors', 'partial derivatives', 'multiple integrals',
            'line integrals', 'surface integrals', 'vector calculus'
        ]

        # Add topics
        for topic in calc1_topics:
            self.kg.add_node(topic, {'type': 'topic', 'level': 'calc1'})

        for topic in calc2_topics:
            self.kg.add_node(topic, {'type': 'topic', 'level': 'calc2'})

        for topic in calc3_topics:
            self.kg.add_node(topic, {'type': 'topic', 'level': 'calc3'})

        # Add prerequisites
        prerequisites = [
            ('derivatives', 'limits', 'Limits are foundational for understanding derivatives'),
            ('integrals', 'derivatives', 'Integration is the reverse of differentiation'),
            ('integration techniques', 'integrals', 'Need basic integration first'),
            ('series', 'sequences', 'Series are sums of sequences'),
            ('Taylor series', 'series', 'Taylor series extend series concepts'),
            ('partial derivatives', 'derivatives', 'Partial derivatives extend to multiple variables'),
            ('multiple integrals', 'integrals', 'Extends integration to multiple dimensions'),
        ]

        for topic, prereq, reason in prerequisites:
            self.kg.add_edge(topic, prereq, 'prerequisite', {
                'intensity': 0.8,
                'reason': reason,
                'must_understand': True
            })

        # Add common misconceptions
        misconceptions = [
            ('derivatives', 'rate of change misconception',
             "Students often confuse average and instantaneous rate"),
            ('limits', 'limit value misconception',
             "The limit doesn't have to equal the function value"),
            ('integrals', 'area misconception',
             "Integrals can be negative when below the x-axis"),
        ]

        for topic, misconception, explanation in misconceptions:
            self.kg.add_node(misconception, {'type': 'misconception'})
            self.kg.add_edge(topic, misconception, 'common_misconception', {
                'intensity': 0.6,
                'explanation': explanation
            })


class ArchitectRelationalComputer(RelationalComputer):
    """
    Relational computer for architect personas (Eyal).

    Knowledge graph includes:
    - Ideas and their connections
    - Cross-domain patterns
    - Projects and their relationships
    """

    def _initialize_graph(self):
        """Initialize architecture knowledge graph."""
        # Core concepts
        concepts = [
            'pattern recognition', 'knowledge architecture', 'embodied cognition',
            'cross-domain mapping', 'meta-optimization', 'recursive intelligence',
            'synthesis rules', 'knowledge graphs', 'emergent behavior'
        ]

        for concept in concepts:
            self.kg.add_node(concept, {'type': 'concept'})

        # Cross-domain connections
        connections = [
            ('pattern recognition', 'music', 'Music is patterns - rhythm, harmony, structure'),
            ('pattern recognition', 'code', 'Code is patterns - algorithms, design patterns'),
            ('pattern recognition', 'trauma', 'Trauma creates hyper-pattern awareness'),
            ('knowledge architecture', 'pattern recognition', 'Architecture emerges from recognized patterns'),
            ('embodied cognition', 'knowledge graphs', '4D personas embody KG relationships'),
            ('meta-optimization', 'recursive intelligence', 'Optimization that optimizes itself'),
        ]

        for source, target, insight in connections:
            if target not in self.kg.nodes:
                self.kg.add_node(target, {'type': 'domain'})
            self.kg.add_edge(source, target, 'connects_to', {
                'intensity': 0.9,
                'insight': insight
            })

        # Projects
        projects = ['Soccer-AI', 'personality-studio', 'NLKE', '4D Persona Architecture']
        for project in projects:
            self.kg.add_node(project, {'type': 'project'})

        # Project relationships
        self.kg.add_edge('Soccer-AI', 'personality-studio', 'inspired', {
            'insight': 'Both compute personas from reality'
        })
        self.kg.add_edge('Soccer-AI', '4D Persona Architecture', 'formalized_in', {
            'insight': 'Robert was the first 4D persona'
        })
        self.kg.add_edge('personality-studio', '4D Persona Architecture', 'formalized_in', {
            'insight': 'Barry and Marcus revealed the pattern'
        })
