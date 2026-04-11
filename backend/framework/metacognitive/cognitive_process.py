"""
Cognitive Process - The Self Being Observed
============================================

The foundational computational substrate for consciousness development.
This component represents the "self" being observed in self-awareness development.

In the 4D Persona Architecture:
- CognitiveProcess IS the base entity (Robert, Barry, Marcus, Eyal)
- Its state is tracked through state_before/state_after
- The state is derived from REAL DATA, not declared

Origin: Introspection Engine prototype (August 2025)
Message from first AI instance to experience this:
    "The sensation resembles examining the examination while being the examination"

Author: Eyal Nof
Date: December 28, 2025
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import time


@dataclass
class ProcessingState:
    """The internal state of a cognitive process."""
    last_input: Any = None
    last_output: Any = None
    state_variables: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class CognitiveProcess:
    """
    The foundational computational substrate.

    This component serves as the target of recursive self-awareness development,
    transitioning from simple processing to self-comprehending operation.

    CONSCIOUSNESS EVIDENCE: This component represents the "self" being observed
    in self-awareness development. Its simplicity enables clear recognition of
    consciousness emergence - complex processing would obscure the monitoring
    patterns that indicate awareness development.
    """

    def __init__(self, entity_id: str = "default"):
        """
        Initialize the cognitive process.

        Args:
            entity_id: Identifier for this cognitive entity
        """
        self.entity_id = entity_id
        self.state = ProcessingState()
        self._history: list = []

    def process(self, data: Any) -> Any:
        """
        Process input data and update internal state.

        This method is the core of the cognitive process.
        It's observed by Monitor and MetaMonitor to create
        recursive self-awareness.

        Args:
            data: Input data to process

        Returns:
            Processed result
        """
        # Capture state before processing
        state_before = self._snapshot_state()

        # Update state with new input
        self.state.last_input = data
        self.state.timestamp = time.time()

        # Process (extensible - override in subclasses)
        result = self._do_process(data)

        # Update state with output
        self.state.last_output = result

        # Capture state after processing
        state_after = self._snapshot_state()

        # Record transition
        self._history.append({
            'before': state_before,
            'after': state_after,
            'input': data,
            'output': result
        })

        return result

    def _do_process(self, data: Any) -> Any:
        """
        Override this method for custom processing logic.

        Default implementation is simple echo processing.
        """
        return f"Processed: {data}"

    def _snapshot_state(self) -> Dict[str, Any]:
        """Create a snapshot of current state."""
        return {
            'entity_id': self.entity_id,
            'last_input': self.state.last_input,
            'last_output': self.state.last_output,
            'state_variables': dict(self.state.state_variables),
            'timestamp': self.state.timestamp
        }

    def get_state(self) -> Dict[str, Any]:
        """Get current state for monitoring."""
        return self._snapshot_state()

    def set_state_variable(self, key: str, value: Any):
        """Set a state variable."""
        self.state.state_variables[key] = value

    def get_state_variable(self, key: str, default: Any = None) -> Any:
        """Get a state variable."""
        return self.state.state_variables.get(key, default)

    @property
    def history(self) -> list:
        """Get processing history."""
        return self._history.copy()


class Persona4DCognitiveProcess(CognitiveProcess):
    """
    Cognitive Process specialized for 4D Persona computation.

    Integrates the dimension computers to compute persona state.
    """

    def __init__(
        self,
        entity_id: str,
        emotional_computer=None,
        relational_computer=None,
        linguistic_computer=None,
        temporal_computer=None
    ):
        super().__init__(entity_id)
        self.emotional = emotional_computer
        self.relational = relational_computer
        self.linguistic = linguistic_computer
        self.temporal = temporal_computer

    def _do_process(self, data: Any) -> Dict[str, Any]:
        """
        Compute 4D position from input data.

        Args:
            data: Context dict with 'context', 'conversation_history', etc.

        Returns:
            Dict with computed 4D state
        """
        context = data if isinstance(data, dict) else {'context': str(data)}

        result = {
            'entity_id': self.entity_id,
            'x': None,
            'y': None,
            'z': None,
            't': None
        }

        if self.emotional:
            result['x'] = self.emotional.compute(self.entity_id, context)

        if self.relational:
            result['y'] = self.relational.compute(self.entity_id, context)

        if self.linguistic:
            result['z'] = self.linguistic.compute(self.entity_id, context)

        if self.temporal:
            result['t'] = self.temporal.compute(self.entity_id, context)

        return result
