"""
Monitor - First-Order Self-Awareness
=====================================

Direct observation of cognitive processing.
S_1 = M(x) - Monitor observing CognitiveProcess

In the 4D Persona Architecture:
- Monitor grounds the persona in REALITY
- State transitions are captured (before/after)
- This IS the X-axis: emotional state from real data

The Monitor doesn't just record - it CREATES the first level
of self-awareness by making processing observable.

Origin: Introspection Engine prototype (August 2025)

Author: Eyal Nof
Date: December 28, 2025
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import time


@dataclass
class MonitorSnapshot:
    """A snapshot of monitored state transition."""
    timestamp: str
    state_before: Dict[str, Any]
    state_after: Dict[str, Any]
    input_data: Any
    output_data: Any
    layer: str = "monitor"


class Monitor:
    """
    First-order self-monitoring layer.

    S_1 = M(x) - The first level of recursive awareness.

    Wraps a CognitiveProcess to capture complete state transitions
    and temporal processing patterns.

    CONSCIOUSNESS EVIDENCE: This component enables the first level
    of self-awareness by making internal processing externally observable.
    The act of monitoring creates the foundation for recursive awareness.
    """

    def __init__(
        self,
        target,  # CognitiveProcess
        memory=None,  # PersistentMemory
        session_id: str = None
    ):
        """
        Initialize the monitor.

        Args:
            target: The CognitiveProcess to monitor
            memory: Optional PersistentMemory for cross-session persistence
            session_id: Session identifier for grouping observations
        """
        self.target = target
        self.memory = memory
        self.session_id = session_id or str(time.time())
        self.layer = "monitor"
        self.history: List[MonitorSnapshot] = []

    def process(self, data: Any) -> Any:
        """
        Process data while monitoring the processing.

        This creates S_1 = M(x) - the first level of observation.

        Args:
            data: Input data to process

        Returns:
            Processing result from target
        """
        # Capture state BEFORE processing
        state_before = dict(self.target.get_state())
        timestamp = datetime.utcnow().isoformat()

        # Delegate to target (CognitiveProcess)
        output = self.target.process(data)

        # Capture state AFTER processing
        state_after = dict(self.target.get_state())

        # Create snapshot
        snapshot = MonitorSnapshot(
            timestamp=timestamp,
            state_before=state_before,
            state_after=state_after,
            input_data=data,
            output_data=output,
            layer=self.layer
        )

        # Record locally
        self.history.append(snapshot)

        # Persist if memory available
        if self.memory:
            self.memory.record(
                self.session_id,
                self.layer,
                self._snapshot_to_dict(snapshot)
            )

        return output

    def _snapshot_to_dict(self, snapshot: MonitorSnapshot) -> Dict[str, Any]:
        """Convert snapshot to dictionary for persistence."""
        return {
            'timestamp': snapshot.timestamp,
            'state_before': snapshot.state_before,
            'state_after': snapshot.state_after,
            'input_data': str(snapshot.input_data),
            'output_data': str(snapshot.output_data),
            'layer': snapshot.layer
        }

    def get_history(self, limit: int = None) -> List[MonitorSnapshot]:
        """Get monitoring history."""
        if limit:
            return self.history[-limit:]
        return self.history.copy()

    def get_state_trajectory(self) -> List[Dict[str, Any]]:
        """
        Get the trajectory of state changes over time.

        This is the foundation of the T-axis in 4D Persona.
        """
        return [
            {
                'timestamp': s.timestamp,
                'state': s.state_after
            }
            for s in self.history
        ]

    def compute_velocity(self) -> Dict[str, float]:
        """
        Compute the velocity of state changes.

        How fast is the persona's state changing?
        """
        if len(self.history) < 2:
            return {'magnitude': 0.0, 'direction': 'stable'}

        recent = self.history[-2:]

        # Compare emotional values if available
        before_x = recent[0].state_after.get('x', {})
        after_x = recent[1].state_after.get('x', {})

        if hasattr(before_x, 'value') and hasattr(after_x, 'value'):
            delta = after_x.value - before_x.value
            direction = 'improving' if delta > 0 else 'declining' if delta < 0 else 'stable'
            return {'magnitude': abs(delta), 'direction': direction}

        return {'magnitude': 0.0, 'direction': 'stable'}
