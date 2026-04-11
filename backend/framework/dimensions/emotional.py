"""
Emotional Dimension Computer (X-axis)
======================================

Computes emotional state from REAL-WORLD DATA.

The key insight: The persona's mood is not declared - it's computed
from the same reality it discusses.

Examples:
- Robert's mood computed from actual match results
- Barry's patience computed from student progress
- Marcus's confidence computed from quiz scores
- Eyal's momentum computed from project progress

Author: Eyal Nof
Date: December 28, 2025
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from persona_engine import DimensionComputer, EmotionalState


class EmotionalComputer(DimensionComputer):
    """
    Abstract base for emotional dimension computation.

    Subclasses implement domain-specific emotional grounding:
    - Football: mood from match results
    - Education: patience from student progress
    - Architecture: momentum from project state
    """

    def __init__(self, data_source: Callable = None):
        """
        Args:
            data_source: Function to fetch real-world data for grounding
        """
        self.data_source = data_source
        self.mood_mappings = self._get_mood_mappings()

    @abstractmethod
    def _get_mood_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Define mood mappings for this domain."""
        pass

    @abstractmethod
    def _extract_emotional_signal(self, entity_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract the raw emotional signal from data."""
        pass

    def compute(self, context: Dict[str, Any], entity_id: str = "") -> EmotionalState:
        """
        Compute emotional state from real data.

        Args:
            context: Context dict containing data to ground emotion in
            entity_id: Optional entity identifier

        Returns:
            EmotionalState with computed values
        """
        # Handle empty context
        if not context:
            return EmotionalState(
                value=0.0,
                mood='neutral',
                intensity=0.5,
                reason='No context provided',
                grounded_in=[]
            )

        signal = self._extract_emotional_signal(entity_id, context)

        return EmotionalState(
            value=signal.get('value', 0.0),
            mood=signal.get('mood', 'neutral'),
            intensity=signal.get('intensity', 0.5),
            reason=signal.get('reason', 'No specific reason'),
            grounded_in=signal.get('grounded_in', [])
        )


class FootballEmotionalComputer(EmotionalComputer):
    """
    Emotional computer for football fan personas (e.g., Robert).

    Grounds emotional state in actual match results:
    - Win → euphoric
    - Loss → frustrated
    - Draw → neutral/conflicted
    - Streak → amplified emotion
    """

    def _get_mood_mappings(self) -> Dict[str, Dict[str, Any]]:
        return {
            'euphoric': {'value': 1.0, 'intensity': 0.9},
            'happy': {'value': 0.8, 'intensity': 0.7},
            'confident': {'value': 0.7, 'intensity': 0.7},
            'neutral': {'value': 0.0, 'intensity': 0.3},
            'anxious': {'value': -0.3, 'intensity': 0.6},
            'disappointed': {'value': -0.6, 'intensity': 0.7},
            'frustrated': {'value': -0.8, 'intensity': 0.8},
            'devastated': {'value': -1.0, 'intensity': 1.0}
        }

    def _extract_emotional_signal(self, entity_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract emotional signal from match data."""
        # Check for match_result in context first (direct passing)
        match_data = context.get('match_result', {})

        # If not in context and we have a data source, try fetching
        if not match_data and self.data_source:
            match_data = self.data_source(entity_id) or {}

        if not match_data:
            return {
                'value': 0.0,
                'mood': 'neutral',
                'intensity': 0.5,
                'reason': 'No match data available',
                'grounded_in': []
            }

        # Compute mood from result
        result = match_data.get('result', 'unknown')
        score = match_data.get('score', {})
        goal_diff = match_data.get('goal_difference', 0)
        opponent = match_data.get('opponent', 'Unknown')

        if result == 'win':
            goals_for = score.get('for', 0)
            goals_against = score.get('against', 0)
            margin = goal_diff if goal_diff else (goals_for - goals_against)

            if margin >= 3:
                mood = 'euphoric'
                reason = f"Demolished {opponent}!" if opponent != 'Unknown' else "Dominant victory!"
            else:
                mood = 'happy'
                reason = f"Beat {opponent}!" if opponent != 'Unknown' else "Good win!"

        elif result == 'loss':
            goals_for = score.get('for', 0)
            goals_against = score.get('against', 0)
            margin = abs(goal_diff) if goal_diff else (goals_against - goals_for)

            if margin >= 3:
                mood = 'devastated'
                reason = f"Hammered by {opponent}" if opponent != 'Unknown' else "Heavy loss"
            else:
                mood = 'disappointed'
                reason = f"Lost to {opponent}" if opponent != 'Unknown' else "Tough loss"

        elif result == 'draw':
            mood = 'neutral'
            reason = f"Drew with {opponent}" if opponent != 'Unknown' else "Draw"
        else:
            mood = 'neutral'
            reason = 'Match result unknown'

        mapping = self.mood_mappings.get(mood, {'value': 0.0, 'intensity': 0.5})

        return {
            'value': mapping['value'],
            'mood': mood,
            'intensity': mapping['intensity'],
            'reason': reason,
            'grounded_in': [match_data]
        }


class TutorEmotionalComputer(EmotionalComputer):
    """
    Emotional computer for tutor personas (e.g., Barry).

    Grounds emotional state in student progress:
    - Student improving → encouraging
    - Student struggling → patient
    - Breakthrough moment → celebratory
    """

    def _get_mood_mappings(self) -> Dict[str, Dict[str, Any]]:
        return {
            'encouraging': {'value': 0.7, 'intensity': 0.7},
            'patient': {'value': 0.3, 'intensity': 0.6},
            'celebratory': {'value': 1.0, 'intensity': 0.9},
            'concerned': {'value': -0.2, 'intensity': 0.5},
            'supportive': {'value': 0.5, 'intensity': 0.6},
            'neutral': {'value': 0.0, 'intensity': 0.3}
        }

    def _extract_emotional_signal(self, entity_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract emotional signal from student progress."""
        # Get student state from context
        student_state = context.get('student_state', {})

        if not student_state:
            return {
                'value': 0.3,
                'mood': 'supportive',
                'intensity': 0.5,
                'reason': 'Ready to help',
                'grounded_in': []
            }

        student_mood = student_state.get('mood', 'neutral')
        student_progress = student_state.get('progress', 0.5)
        recent_success = student_state.get('recent_success', False)

        # Barry adapts to student state
        if recent_success:
            mood = 'celebratory'
            reason = "Student just had a breakthrough!"
        elif student_mood in ['frustrated', 'confused']:
            mood = 'patient'
            reason = "Student needs extra support right now"
        elif student_progress > 0.7:
            mood = 'encouraging'
            reason = "Student is making great progress"
        elif student_progress < 0.3:
            mood = 'concerned'
            reason = "Student may need a different approach"
        else:
            mood = 'supportive'
            reason = "Steady progress"

        mapping = self.mood_mappings.get(mood, {'value': 0.0, 'intensity': 0.5})

        return {
            'value': mapping['value'],
            'mood': mood,
            'intensity': mapping['intensity'],
            'reason': reason,
            'grounded_in': [student_state]
        }


class StudentEmotionalComputer(EmotionalComputer):
    """
    Emotional computer for student personas (e.g., Marcus).

    Grounds emotional state in learning experience:
    - Understanding → confident
    - Confused → frustrated
    - Breakthrough → excited
    """

    def _get_mood_mappings(self) -> Dict[str, Dict[str, Any]]:
        return {
            'confident': {'value': 0.7, 'intensity': 0.7},
            'excited': {'value': 1.0, 'intensity': 0.9},
            'curious': {'value': 0.4, 'intensity': 0.5},
            'confused': {'value': -0.3, 'intensity': 0.6},
            'frustrated': {'value': -0.7, 'intensity': 0.8},
            'neutral': {'value': 0.0, 'intensity': 0.3}
        }

    def _extract_emotional_signal(self, entity_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract emotional signal from learning state."""
        # Get learning metrics from context
        quiz_score = context.get('quiz_score')
        understanding = context.get('understanding_level', 0.5)
        attempts = context.get('problem_attempts', 0)

        if quiz_score is not None:
            if quiz_score >= 0.9:
                mood = 'excited'
                reason = "Aced the quiz!"
            elif quiz_score >= 0.7:
                mood = 'confident'
                reason = "Did well on the quiz"
            elif quiz_score >= 0.5:
                mood = 'neutral'
                reason = "Passed, but could do better"
            else:
                mood = 'frustrated'
                reason = "Struggled with the quiz"
        elif attempts > 3 and understanding < 0.4:
            mood = 'frustrated'
            reason = "Can't figure this out"
        elif understanding > 0.7:
            mood = 'confident'
            reason = "Getting the hang of this"
        else:
            mood = 'curious'
            reason = "Working through it"

        mapping = self.mood_mappings.get(mood, {'value': 0.0, 'intensity': 0.5})

        return {
            'value': mapping['value'],
            'mood': mood,
            'intensity': mapping['intensity'],
            'reason': reason,
            'grounded_in': [{'quiz_score': quiz_score, 'understanding': understanding}]
        }


class ArchitectEmotionalComputer(EmotionalComputer):
    """
    Emotional computer for architect personas (e.g., Eyal).

    Grounds emotional state in creative momentum:
    - Pattern recognized → energized
    - Connection made → flow state
    - Blocked → restless
    """

    def _get_mood_mappings(self) -> Dict[str, Dict[str, Any]]:
        return {
            'flow': {'value': 1.0, 'intensity': 1.0},
            'energized': {'value': 0.8, 'intensity': 0.8},
            'focused': {'value': 0.5, 'intensity': 0.7},
            'contemplative': {'value': 0.2, 'intensity': 0.4},
            'restless': {'value': -0.3, 'intensity': 0.6},
            'blocked': {'value': -0.6, 'intensity': 0.7},
            'neutral': {'value': 0.0, 'intensity': 0.3}
        }

    def _extract_emotional_signal(self, entity_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract emotional signal from creative state."""
        # Get project state from context
        patterns_recognized = context.get('patterns_recognized', 0)
        connections_made = context.get('connections_made', 0)
        blocks_encountered = context.get('blocks', 0)
        flow_indicators = context.get('flow_indicators', [])

        if 'breakthrough' in flow_indicators or patterns_recognized > 3:
            mood = 'flow'
            reason = "Pattern emerging - everything is connecting"
        elif connections_made > 2:
            mood = 'energized'
            reason = "Cross-domain connections firing"
        elif patterns_recognized > 0:
            mood = 'focused'
            reason = "Something is forming"
        elif blocks_encountered > 2:
            mood = 'blocked'
            reason = "Need to approach differently"
        elif blocks_encountered > 0:
            mood = 'restless'
            reason = "Looking for the right angle"
        else:
            mood = 'contemplative'
            reason = "Processing"

        mapping = self.mood_mappings.get(mood, {'value': 0.0, 'intensity': 0.5})

        return {
            'value': mapping['value'],
            'mood': mood,
            'intensity': mapping['intensity'],
            'reason': reason,
            'grounded_in': [{
                'patterns': patterns_recognized,
                'connections': connections_made,
                'flow': flow_indicators
            }]
        }
