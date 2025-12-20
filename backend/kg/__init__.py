"""
NLKE-Compliant Knowledge Graph Module

This module provides:
- KnowledgeGraphDB: Unified database layer for Soccer-AI and Predictor domains
- NLKEBridge: Bridge to NLKE MCP tools (hybrid_search, semantic_similarity)
- Migration utilities: JSON → SQLite conversion
- Compatibility layer: Sync between legacy kg_nodes/kg_edges and NLKE format

Schema follows unified-kg.db format with source_kg field for cross-domain queries.
"""

from .kg_types import NodeType, EdgeType, NodeDefinition, EdgeDefinition
from .kg_database import KnowledgeGraphDB, get_kg_connection
from .nlke_bridge import NLKEBridge, want_to, can_it
from .kg_compat import (
    sync_legacy_to_nlke,
    sync_nlke_to_legacy,
    compare_kg_systems,
    unified_search
)

__all__ = [
    # Type definitions
    'NodeType',
    'EdgeType',
    'NodeDefinition',
    'EdgeDefinition',
    # Database layer
    'KnowledgeGraphDB',
    'get_kg_connection',
    # NLKE Bridge
    'NLKEBridge',
    'want_to',
    'can_it',
    # Compatibility
    'sync_legacy_to_nlke',
    'sync_nlke_to_legacy',
    'compare_kg_systems',
    'unified_search',
]
