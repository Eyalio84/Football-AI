"""
Node and Edge Type Definitions for Soccer-AI Knowledge Graph

Defines all node types and edge types for both domains:
- Soccer-AI: modules, endpoints, personas, security_states
- Predictor: modules, factor_a, factor_b, patterns, equations
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


class NodeType(str, Enum):
    """Node types across Soccer-AI and Predictor domains."""

    # Soccer-AI Domain
    MODULE = "module"                  # Code modules (main.py, database.py, etc.)
    ENDPOINT = "endpoint"              # API endpoints (/api/v1/chat, etc.)
    PERSONA = "persona"                # Fan personas (arsenal, chelsea, analyst)
    SECURITY_STATE = "security_state"  # Security state machine states
    TABLE = "table"                    # Database tables
    CAPABILITY = "capability"          # Module capabilities

    # Predictor Domain
    FACTOR_A = "factor_a"              # Side A weakness factors (FA_*)
    FACTOR_B = "factor_b"              # Side B strength factors (FB_*)
    PATTERN = "pattern"                # Third Knowledge patterns
    EQUATION = "equation"              # Mathematical equations
    CONFIDENCE_LEVEL = "confidence_level"  # Low/Medium/High

    # Shared
    TEAM = "team"                      # Team entities
    INTEGRATION = "integration"        # System integrations


class EdgeType(str, Enum):
    """Edge types for knowledge graph relationships."""

    # Dependency edges
    DEPENDS_ON = "depends_on"          # Module depends on module
    REQUIRES = "requires"              # Feature requires capability

    # Routing edges
    ROUTES_TO = "routes_to"            # Endpoint routes to module
    CALLS = "calls"                    # Module calls module

    # Factor interaction edges (Predictor)
    TRIGGERS = "triggers"              # Pattern triggered by factors
    INFLUENCES = "influences"          # Factor influences prediction
    AMPLIFIES = "amplifies"            # Pattern amplifies factor
    COMBINES_WITH = "combines_with"    # Pattern combines factors

    # Capability edges
    HAS_CAPABILITY = "has_capability"  # Module has capability
    PROVIDES = "provides"              # Endpoint provides capability
    USES = "uses"                      # Module uses another

    # Security edges
    TRANSITIONS_TO = "transitions_to"  # State transitions on clean query
    ESCALATES_FROM = "escalates_from"  # State escalates on injection

    # Persona edges
    REPRESENTS = "represents"          # Persona represents team
    USES_PERSONA = "uses_persona"      # Endpoint uses persona


class SourceKG(str, Enum):
    """Domain identifiers for source_kg field."""
    SOCCER_AI = "soccer-ai"
    PREDICTOR = "predictor"
    CROSS_DOMAIN = "cross-domain"


@dataclass
class NodeDefinition:
    """Definition for a knowledge graph node."""
    id: str                            # Format: "{source_kg}_{type}_{original_id}"
    original_id: str                   # Original ID from source
    name: str                          # Display name
    type: NodeType                     # Node type enum
    description: str = ""              # Node description
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_kg: str = ""                # "soccer-ai" or "predictor"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        import json
        return {
            'id': self.id,
            'original_id': self.original_id,
            'name': self.name,
            'type': self.type.value if isinstance(self.type, NodeType) else self.type,
            'description': self.description,
            'metadata': json.dumps(self.metadata),
            'source_kg': self.source_kg
        }


@dataclass
class EdgeDefinition:
    """Definition for a knowledge graph edge."""
    from_node: str                     # Source node ID
    to_node: str                       # Target node ID
    type: EdgeType                     # Edge type enum
    weight: float = 1.0                # Edge weight
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_kg: str = ""                # "soccer-ai" or "predictor"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        import json
        return {
            'from_node': self.from_node,
            'to_node': self.to_node,
            'type': self.type.value if isinstance(self.type, EdgeType) else self.type,
            'weight': self.weight,
            'metadata': json.dumps(self.metadata),
            'source_kg': self.source_kg
        }


def create_node_id(source_kg: str, node_type: str, original_id: str) -> str:
    """
    Generate NLKE-compliant node ID.

    Format: {source_kg}_{type}_{sanitized_original_id}

    Examples:
    - soccer-ai_module_main
    - predictor_factor_a_fa_fat
    - soccer-ai_persona_arsenal
    """
    # Sanitize original_id for use in composite key
    safe_id = original_id.replace(" ", "_").replace("/", "_").replace("-", "_").lower()
    return f"{source_kg}_{node_type}_{safe_id}"
