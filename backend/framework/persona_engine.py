"""
4D Persona Engine
=================

The core orchestrator for computing persona state as a position in 4D space.

P(t) = (x, y, z, t)

Where:
    x = Emotional dimension (derived from real data)
    y = Relational dimension (position in knowledge graph)
    z = Linguistic dimension (voice/dialect identity)
    t = Temporal dimension (trajectory through time)

Author: Eyal Nof
Date: December 28, 2025
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from abc import ABC, abstractmethod
import time


@dataclass
class EmotionalState:
    """X-axis: Emotional dimension derived from real-world data."""
    value: float  # -1.0 (negative) to 1.0 (positive)
    mood: str  # "euphoric", "confident", "neutral", "anxious", "frustrated"
    intensity: float  # 0.0 to 1.0
    reason: str  # Why this mood (grounded in data)
    grounded_in: List[Any] = field(default_factory=list)  # Source data


@dataclass
class RelationalState:
    """Y-axis: Position in knowledge graph."""
    activated: bool
    relation_type: Optional[str] = None  # "rival", "legend", "ally", "prerequisite"
    target: Optional[str] = None  # The related entity
    intensity: float = 0.0  # Relationship strength
    context: Dict[str, Any] = field(default_factory=dict)  # Banter, history, etc.


@dataclass
class LinguisticState:
    """Z-axis: Voice and dialect identity."""
    dialect: str  # "scouse", "geordie", "cockney", "neutral", "academic"
    distinctiveness: float  # How different from baseline (0.0 to 1.0)
    vocabulary: Dict[str, Any] = field(default_factory=dict)  # Word mappings
    voice_instruction: str = ""  # System prompt injection for voice


@dataclass
class TemporalState:
    """T-axis: Evolution through time."""
    step: int  # Discrete time step in conversation
    trajectory: List['Persona4D'] = field(default_factory=list)  # Historical positions
    velocity: Dict[str, float] = field(default_factory=dict)  # Rate of change
    momentum: Dict[str, float] = field(default_factory=dict)  # Predicted direction
    memory: List[str] = field(default_factory=list)  # Salient memories


@dataclass
class Persona4D:
    """
    A persona's complete state in 4D space.

    This is not a description - it's a computed position.
    """
    entity_id: str
    x: EmotionalState
    y: RelationalState
    z: LinguisticState
    t: TemporalState

    # Derived properties
    intensity: float = 0.0  # Overall engagement intensity
    stability: float = 1.0  # How consistent over time
    authenticity: float = 1.0  # How grounded in real data

    def to_prompt_injection(self) -> str:
        """Convert 4D state to system prompt content."""
        parts = []

        # Emotional injection
        parts.append(f"""
EMOTIONAL STATE (Dimension X):
Current mood: {self.x.mood.upper()}
Intensity: {self.x.intensity:.1f}/1.0
Grounded in: {self.x.reason}

Express this emotion naturally in your responses.
""")

        # Relational injection (if activated)
        if self.y.activated:
            parts.append(f"""
RELATIONAL CONTEXT (Dimension Y):
Active relationship: {self.y.relation_type} with {self.y.target}
Intensity: {self.y.intensity:.1f}/1.0

Let this relationship color your response appropriately.
""")

        # Linguistic injection
        if self.z.dialect != "neutral":
            parts.append(f"""
LINGUISTIC IDENTITY (Dimension Z):
Dialect: {self.z.dialect}
Voice: {self.z.voice_instruction}
""")

        # Temporal injection
        if self.t.memory:
            parts.append(f"""
TEMPORAL CONTEXT (Dimension T):
Conversation position: Turn {self.t.step}
Salient memories: {', '.join(self.t.memory[:3])}

Maintain continuity with previous states.
""")

        return "\n".join(parts)


class DimensionComputer(ABC):
    """Abstract base for dimension computation."""

    @abstractmethod
    def compute(self, entity_id: str, context: Dict[str, Any]) -> Any:
        """Compute this dimension's state."""
        pass


class PersonaEngine:
    """
    The 4D Persona Engine.

    Orchestrates computation of persona state from:
    - Real-world data sources (X)
    - Knowledge graph (Y)
    - Dialect configuration (Z)
    - Conversation history (T)
    """

    def __init__(
        self,
        emotional_computer: DimensionComputer,
        relational_computer: DimensionComputer,
        linguistic_computer: DimensionComputer,
        temporal_computer: DimensionComputer
    ):
        self.emotional = emotional_computer
        self.relational = relational_computer
        self.linguistic = linguistic_computer
        self.temporal = temporal_computer

        # State tracking
        self.history: Dict[str, List[Persona4D]] = {}

    def compute_position(
        self,
        entity_id: str,
        context: str,
        conversation_history: List[Dict[str, str]] = None,
        **extra_context
    ) -> Persona4D:
        """
        Compute the current 4D position of a persona.

        Args:
            entity_id: Identifier for the persona entity
            context: Current context (user message, etc.)
            conversation_history: Previous turns in conversation
            **extra_context: Additional context data (match_result, student_state, etc.)

        Returns:
            Persona4D: The computed 4D state
        """
        conversation_history = conversation_history or []

        ctx = {
            "context": context,
            "conversation_history": conversation_history,
            "timestamp": time.time(),
            **extra_context  # Include any extra context like match_result
        }

        # Compute each dimension (context first, entity_id second)
        x = self.emotional.compute(ctx, entity_id)
        y = self.relational.compute(ctx, entity_id)
        z = self.linguistic.compute(ctx, entity_id)
        t = self.temporal.compute(ctx, entity_id)

        # Add historical trajectory to temporal state
        if entity_id in self.history:
            t.trajectory = self.history[entity_id][-10:]  # Last 10 positions

        # Create 4D position
        persona = Persona4D(
            entity_id=entity_id,
            x=x,
            y=y,
            z=z,
            t=t,
            intensity=self._compute_intensity(x, y),
            stability=self._compute_stability(entity_id),
            authenticity=self._compute_authenticity(x, y)
        )

        # Update history
        if entity_id not in self.history:
            self.history[entity_id] = []
        self.history[entity_id].append(persona)

        return persona

    def _compute_intensity(self, x: EmotionalState, y: RelationalState) -> float:
        """Compute overall engagement intensity."""
        emotional_intensity = x.intensity
        relational_intensity = y.intensity if y.activated else 0.0
        return (emotional_intensity + relational_intensity) / 2

    def _compute_stability(self, entity_id: str) -> float:
        """Compute how stable the persona has been over time."""
        if entity_id not in self.history or len(self.history[entity_id]) < 2:
            return 1.0

        recent = self.history[entity_id][-5:]
        if len(recent) < 2:
            return 1.0

        # Calculate variance in emotional position
        moods = [p.x.value for p in recent]
        mean_mood = sum(moods) / len(moods)
        variance = sum((m - mean_mood) ** 2 for m in moods) / len(moods)

        # Convert to stability (low variance = high stability)
        return max(0.0, 1.0 - variance)

    def _compute_authenticity(self, x: EmotionalState, y: RelationalState) -> float:
        """Compute how grounded the persona is in real data."""
        # Authenticity is high if emotional state is grounded in actual data
        emotional_grounded = 1.0 if x.grounded_in else 0.5
        relational_grounded = 1.0 if y.context else 0.5
        return (emotional_grounded + relational_grounded) / 2

    def synthesize_prompt(
        self,
        persona: Persona4D,
        base_prompt: str
    ) -> str:
        """
        Synthesize a complete system prompt from 4D state.

        Args:
            persona: The computed 4D persona state
            base_prompt: The base identity prompt

        Returns:
            str: Complete system prompt with 4D injection
        """
        return f"{base_prompt}\n\n{persona.to_prompt_injection()}"

    def get_trajectory(self, entity_id: str, window: int = 10) -> List[Persona4D]:
        """Get the trajectory of a persona through 4D space."""
        if entity_id not in self.history:
            return []
        return self.history[entity_id][-window:]

    def predict_next(self, entity_id: str) -> Optional[Dict[str, float]]:
        """Predict the next position based on momentum."""
        trajectory = self.get_trajectory(entity_id, 3)
        if len(trajectory) < 2:
            return None

        # Simple linear extrapolation
        recent = trajectory[-1]
        previous = trajectory[-2]

        velocity_x = recent.x.value - previous.x.value

        return {
            "predicted_x": recent.x.value + velocity_x,
            "velocity_x": velocity_x,
            "direction": "improving" if velocity_x > 0 else "declining" if velocity_x < 0 else "stable"
        }


# Utility function for two-persona interaction
def adapt_persona_to_other(
    primary: Persona4D,
    other: Persona4D,
    adaptation_rules: Dict[str, Callable]
) -> Persona4D:
    """
    Adapt one persona's state based on another's state.

    Example: Barry (tutor) adapts patience based on Marcus (student) frustration.

    Args:
        primary: The persona being adapted
        other: The persona being responded to
        adaptation_rules: Dict of dimension -> adaptation function

    Returns:
        Adapted Persona4D
    """
    adapted = primary

    for dimension, rule in adaptation_rules.items():
        if dimension == "emotional":
            adapted.x = rule(primary.x, other.x)
        elif dimension == "relational":
            adapted.y = rule(primary.y, other.y)
        elif dimension == "linguistic":
            adapted.z = rule(primary.z, other.z)

    return adapted


if __name__ == "__main__":
    # Example usage
    print("4D Persona Engine")
    print("=================")
    print("P(t) = (x, y, z, t)")
    print()
    print("The persona is not a description.")
    print("It's a computed position in 4D space.")
    print()
    print("The AI doesn't play a character. It lives one.")
