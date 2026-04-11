"""
4D Persona Dimension Computers
==============================

Each dimension computes one axis of the 4D persona space:
- X: Emotional (from real-world data)
- Y: Relational (from knowledge graph)
- Z: Linguistic (from dialect configuration)
- T: Temporal (from conversation history)
"""

from .emotional import EmotionalComputer
from .relational import RelationalComputer
from .linguistic import LinguisticComputer
from .temporal import TemporalComputer

__all__ = [
    'EmotionalComputer',
    'RelationalComputer',
    'LinguisticComputer',
    'TemporalComputer'
]
