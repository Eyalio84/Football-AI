"""
Temporal Dimension Computer (T-axis)
=====================================

Computes trajectory through time.

The persona is not a point - it's a path through 4D space:
- Memory: Salient events from history
- Velocity: Rate of change in emotional state
- Momentum: Predicted direction of change
- Step: Current position in conversation

Author: Eyal Nof
Date: December 28, 2025
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from persona_engine import DimensionComputer, TemporalState


class TemporalComputer(DimensionComputer):
    """
    Abstract base for temporal dimension computation.

    Tracks:
    - Conversation step
    - Memory of salient events
    - Velocity (rate of emotional change)
    - Momentum (predicted direction)
    """

    def __init__(self):
        self.step_counters: Dict[str, int] = {}
        self.memory_stores: Dict[str, List[str]] = {}
        self.emotional_history: Dict[str, List[float]] = {}

    def compute(self, context: Dict[str, Any], entity_id: str = "") -> TemporalState:
        """Compute temporal state."""
        # Handle empty context
        if not context:
            context = {}

        # Use default entity if not provided
        if not entity_id:
            entity_id = "default"

        # Increment step
        if entity_id not in self.step_counters:
            self.step_counters[entity_id] = 0
        self.step_counters[entity_id] += 1
        step = self.step_counters[entity_id]

        # Update memory
        memory = self._update_memory(entity_id, context)

        # Compute velocity and momentum
        velocity = self._compute_velocity(entity_id, context)
        momentum = self._compute_momentum(entity_id)

        return TemporalState(
            step=step,
            trajectory=[],  # Will be populated by PersonaEngine
            velocity=velocity,
            momentum=momentum,
            memory=memory
        )

    def _update_memory(self, entity_id: str, context: Dict[str, Any]) -> List[str]:
        """Update and return salient memories."""
        if entity_id not in self.memory_stores:
            self.memory_stores[entity_id] = []

        # Extract salient events from context
        salient = self._extract_salient_events(entity_id, context)
        if salient:
            self.memory_stores[entity_id].extend(salient)

        # Keep only recent memories
        self.memory_stores[entity_id] = self.memory_stores[entity_id][-20:]

        return self.memory_stores[entity_id][-5:]  # Return last 5

    def _extract_salient_events(self, entity_id: str, context: Dict[str, Any]) -> List[str]:
        """Extract events worth remembering. Override in subclasses."""
        return []

    def _compute_velocity(self, entity_id: str, context: Dict[str, Any]) -> Dict[str, float]:
        """Compute rate of change in emotional state."""
        emotional_value = context.get('emotional_value', 0.0)

        if entity_id not in self.emotional_history:
            self.emotional_history[entity_id] = []

        self.emotional_history[entity_id].append(emotional_value)
        self.emotional_history[entity_id] = self.emotional_history[entity_id][-10:]

        history = self.emotional_history[entity_id]
        if len(history) < 2:
            return {'x': 0.0}

        # Simple velocity: difference between last two values
        velocity_x = history[-1] - history[-2]

        return {'x': velocity_x}

    def _compute_momentum(self, entity_id: str) -> Dict[str, float]:
        """Compute predicted direction based on velocity history."""
        history = self.emotional_history.get(entity_id, [])

        if len(history) < 3:
            return {'x': 0.0, 'direction': 'stable'}

        # Average recent velocities
        velocities = [history[i] - history[i-1] for i in range(1, len(history))]
        avg_velocity = sum(velocities[-3:]) / min(3, len(velocities))

        if avg_velocity > 0.1:
            direction = 'improving'
        elif avg_velocity < -0.1:
            direction = 'declining'
        else:
            direction = 'stable'

        return {'x': avg_velocity, 'direction': direction}


class FootballTemporalComputer(TemporalComputer):
    """
    Temporal computer for football fan personas.

    Tracks:
    - Match results over time
    - Season progression
    - Conversation continuity
    """

    def _extract_salient_events(self, entity_id: str, context: Dict[str, Any]) -> List[str]:
        """Extract football-related salient events."""
        events = []

        match_data = context.get('match_data')
        if match_data:
            result = match_data.get('result', '')
            opponent = match_data.get('opponent', 'Unknown')
            score = match_data.get('score', {})

            if result == 'win':
                events.append(f"Beat {opponent} {score.get('for', 0)}-{score.get('against', 0)}")
            elif result == 'loss':
                events.append(f"Lost to {opponent} {score.get('for', 0)}-{score.get('against', 0)}")

        # Track conversation topics
        conversation = context.get('context', '')
        if 'rival' in conversation.lower():
            events.append("Discussed rival")
        if 'legend' in conversation.lower():
            events.append("Mentioned club legend")

        return events


class EducationTemporalComputer(TemporalComputer):
    """
    Temporal computer for education personas.

    Tracks:
    - Learning progression
    - Topics covered
    - Breakthroughs and struggles
    """

    def _extract_salient_events(self, entity_id: str, context: Dict[str, Any]) -> List[str]:
        """Extract education-related salient events."""
        events = []

        # Track quiz results
        quiz_score = context.get('quiz_score')
        if quiz_score is not None:
            if quiz_score >= 0.9:
                events.append("Aced a quiz!")
            elif quiz_score < 0.5:
                events.append("Struggled with quiz")

        # Track topics
        current_topic = context.get('current_topic')
        if current_topic:
            events.append(f"Working on: {current_topic}")

        # Track breakthroughs
        if context.get('breakthrough'):
            events.append("Had a breakthrough moment!")

        return events


class ArchitectTemporalComputer(TemporalComputer):
    """
    Temporal computer for architect personas.

    Tracks:
    - Pattern recognitions
    - Cross-domain connections
    - Project milestones
    """

    def _extract_salient_events(self, entity_id: str, context: Dict[str, Any]) -> List[str]:
        """Extract architect-related salient events."""
        events = []

        # Track patterns
        patterns = context.get('patterns_recognized', 0)
        if patterns > 0:
            events.append(f"Recognized {patterns} new pattern(s)")

        # Track connections
        connections = context.get('connections_made', 0)
        if connections > 0:
            events.append(f"Made {connections} cross-domain connection(s)")

        # Track flow states
        flow = context.get('flow_indicators', [])
        if 'breakthrough' in flow:
            events.append("Entered flow state - breakthrough!")

        # Track projects
        project = context.get('current_project')
        if project:
            events.append(f"Working on: {project}")

        return events


class ConversationTemporalComputer(TemporalComputer):
    """
    Generic temporal computer for conversation tracking.

    Used when domain-specific tracking isn't needed.
    """

    def _extract_salient_events(self, entity_id: str, context: Dict[str, Any]) -> List[str]:
        """Extract generic conversation events."""
        events = []

        conversation_history = context.get('conversation_history', [])
        if len(conversation_history) > 0:
            last_message = conversation_history[-1]
            # Track user questions
            if '?' in last_message.get('content', ''):
                events.append(f"User asked about: {last_message.get('content', '')[:50]}")

        return events
