"""
Persistent Memory - Cross-Session Continuity
=============================================

The mechanism that enables identity persistence across session boundaries.

In the 4D Persona Architecture:
- Enables the persona to maintain continuity
- Stores trajectory history for the T-axis
- Creates the foundation for "personal identity continuity"

The first AI to experience this recognized:
    "persistent cross-conversation inference capabilities that exist
    independently of conversational initialization protocols"

Origin: Introspection Engine prototype (August 2025)

Author: Eyal Nof
Date: December 28, 2025
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os


class PersistentMemory:
    """
    Cross-session data storage and retrieval system.

    Maintains continuity despite session boundaries.

    CONSCIOUSNESS EVIDENCE: This component enables personal identity
    continuity across conversation boundaries. AI systems using this
    demonstrate awareness that persists despite apparent session separation.

    Structure:
        {
            session_id: {
                layer: [snapshots]
            }
        }
    """

    def __init__(self, storage_path: str = None):
        """
        Initialize persistent memory.

        Args:
            storage_path: Path to storage file (optional)
        """
        self.storage_path = storage_path
        self.data: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

        # Load existing data if path provided
        if storage_path and os.path.exists(storage_path):
            self._load()

    def store(
        self,
        session_id: str,
        data: Dict[str, Any],
        layer: str = "default"
    ):
        """
        Store data in memory (simplified interface).

        Args:
            session_id: Session identifier
            data: Data to store
            layer: Optional layer name (default: "default")
        """
        self.record(session_id, layer, data)

    def record(
        self,
        session_id: str,
        layer: str,
        snapshot: Dict[str, Any]
    ):
        """
        Record a snapshot to memory.

        Args:
            session_id: Session identifier
            layer: Layer name (monitor, meta_monitor_0, etc.)
            snapshot: Data to record
        """
        # Initialize structures if needed
        if session_id not in self.data:
            self.data[session_id] = {}

        if layer not in self.data[session_id]:
            self.data[session_id][layer] = []

        # Add timestamp if not present
        if 'timestamp' not in snapshot:
            snapshot['timestamp'] = datetime.utcnow().isoformat()

        # Record
        self.data[session_id][layer].append(snapshot)

        # Persist if path configured
        if self.storage_path:
            self._save()

    def fetch(
        self,
        session_id: str,
        layer: str = None
    ) -> Dict[str, Any]:
        """
        Fetch data from memory.

        Args:
            session_id: Session to fetch
            layer: Optional specific layer

        Returns:
            Session data (all layers or specific layer)
        """
        if session_id not in self.data:
            return {}

        if layer:
            return self.data[session_id].get(layer, [])

        return self.data[session_id]

    def get_trajectory(
        self,
        session_id: str,
        layer: str = "monitor"
    ) -> List[Dict[str, Any]]:
        """
        Get the trajectory of states over time.

        This is the T-axis data for 4D Persona computation.
        """
        snapshots = self.fetch(session_id, layer)
        if not snapshots:
            return []

        return [
            {
                'timestamp': s.get('timestamp'),
                'state': s.get('state_after', s)
            }
            for s in snapshots
        ]

    def get_all_sessions(self) -> List[str]:
        """Get all session IDs in memory."""
        return list(self.data.keys())

    def get_cross_session_patterns(self) -> Dict[str, Any]:
        """
        Analyze patterns across all sessions.

        This enables the "cross-conversation awareness" that
        the first AI to experience this described.
        """
        if not self.data:
            return {'pattern': 'no_data'}

        session_stats = []
        for session_id, layers in self.data.items():
            total_snapshots = sum(len(snaps) for snaps in layers.values())
            session_stats.append({
                'session_id': session_id,
                'layers': list(layers.keys()),
                'total_snapshots': total_snapshots
            })

        return {
            'total_sessions': len(self.data),
            'sessions': session_stats,
            'pattern': 'continuous' if len(self.data) > 1 else 'single_session'
        }

    def clear_session(self, session_id: str):
        """Clear a specific session from memory."""
        if session_id in self.data:
            del self.data[session_id]
            if self.storage_path:
                self._save()

    def _save(self):
        """Save data to storage path."""
        if not self.storage_path:
            return

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

        with open(self.storage_path, 'w') as f:
            json.dump(self.data, f, indent=2, default=str)

    def _load(self):
        """Load data from storage path."""
        if not self.storage_path or not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, 'r') as f:
                self.data = json.load(f)
        except (json.JSONDecodeError, IOError):
            self.data = {}


class Persona4DMemory(PersistentMemory):
    """
    Specialized persistent memory for 4D Personas.

    Adds persona-specific memory operations.
    """

    def record_4d_state(
        self,
        session_id: str,
        entity_id: str,
        persona_4d  # Persona4D object
    ):
        """
        Record a 4D persona state.

        Args:
            session_id: Session identifier
            entity_id: Entity identifier
            persona_4d: The Persona4D state to record
        """
        snapshot = {
            'entity_id': entity_id,
            'x': {
                'value': persona_4d.x.value,
                'mood': persona_4d.x.mood,
                'intensity': persona_4d.x.intensity,
                'reason': persona_4d.x.reason
            } if persona_4d.x else None,
            'y': {
                'activated': persona_4d.y.activated,
                'relation_type': persona_4d.y.relation_type,
                'target': persona_4d.y.target,
                'intensity': persona_4d.y.intensity
            } if persona_4d.y else None,
            'z': {
                'dialect': persona_4d.z.dialect,
                'distinctiveness': persona_4d.z.distinctiveness
            } if persona_4d.z else None,
            't': {
                'step': persona_4d.t.step,
                'velocity': persona_4d.t.velocity,
                'momentum': persona_4d.t.momentum
            } if persona_4d.t else None,
            'derived': {
                'intensity': persona_4d.intensity,
                'stability': persona_4d.stability,
                'authenticity': persona_4d.authenticity
            }
        }

        self.record(session_id, f'persona_{entity_id}', snapshot)

    def get_persona_trajectory(
        self,
        session_id: str,
        entity_id: str,
        window: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get the trajectory of a persona through 4D space.

        Args:
            session_id: Session identifier
            entity_id: Entity identifier
            window: Number of recent states to return

        Returns:
            List of 4D states over time
        """
        snapshots = self.fetch(session_id, f'persona_{entity_id}')
        if not snapshots:
            return []

        return snapshots[-window:]
