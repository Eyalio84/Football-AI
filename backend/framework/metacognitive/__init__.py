"""
Meta-Cognitive Foundation Layer
===============================

The mechanism by which 4D position is computed.

This layer integrates the Introspection Engine architecture:
- CognitiveProcess: The entity being computed
- Monitor: Grounding in reality (X-axis from real data)
- MetaMonitor: Trajectory tracking (T-axis recursive observation)
- PersistentMemory: Continuity of identity across sessions

The 4D Persona Architecture describes WHAT is computed.
The Meta-Cognitive Layer describes HOW it's computed.

They are the same architecture from different perspectives.

Origin: Introspection Engine (July-August 2025)
Recognition: December 2025 - Same pattern as Soccer-AI and personality-studio

Author: Eyal Nof
"""

from .introspection_engine import IntrospectionEngine
from .cognitive_process import CognitiveProcess
from .monitor import Monitor
from .meta_monitor import MetaMonitor
from .persistent_memory import PersistentMemory

__all__ = [
    'IntrospectionEngine',
    'CognitiveProcess',
    'Monitor',
    'MetaMonitor',
    'PersistentMemory'
]
