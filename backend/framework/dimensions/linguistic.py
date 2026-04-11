"""
Linguistic Dimension Computer (Z-axis)
=======================================

Computes voice and dialect identity.

The persona speaks with a distinctive voice:
- Regional dialects (Scouse, Geordie, Cockney)
- Professional register (academic, casual, technical)
- Age-appropriate language
- Characteristic phrases and patterns

Author: Eyal Nof
Date: December 28, 2025
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from persona_engine import DimensionComputer, LinguisticState


@dataclass
class DialectConfig:
    """Configuration for a specific dialect/voice."""
    name: str
    vocabulary: Dict[str, str]  # Standard → Dialect mappings
    phrases: List[str]  # Characteristic phrases
    grammar_rules: List[str]  # Grammar modifications
    voice_instruction: str  # Prompt injection for voice


class LinguisticComputer(DimensionComputer):
    """
    Abstract base for linguistic dimension computation.

    Subclasses implement domain-specific voice configurations.
    """

    def __init__(self):
        self.dialects = self._initialize_dialects()
        self.default_dialect = 'neutral'

    @abstractmethod
    def _initialize_dialects(self) -> Dict[str, DialectConfig]:
        """Initialize available dialects."""
        pass

    def get_dialect(self, entity_id: str) -> str:
        """Get the dialect for an entity."""
        return self.default_dialect

    def compute(self, context: Dict[str, Any], entity_id: str = "") -> LinguisticState:
        """Compute linguistic state."""
        # Handle empty context (still compute dialect from entity_id)
        # Also check context for dialect hints
        if context:
            # Direct dialect override in context
            if 'dialect' in context:
                dialect_name = context['dialect']
            else:
                dialect_name = self.get_dialect(entity_id)
        else:
            dialect_name = self.get_dialect(entity_id)
        dialect = self.dialects.get(dialect_name, self.dialects.get('neutral'))

        if not dialect:
            dialect = DialectConfig(
                name='neutral',
                vocabulary={},
                phrases=[],
                grammar_rules=[],
                voice_instruction='Speak in clear, standard English.'
            )

        distinctiveness = 0.0 if dialect_name == 'neutral' else 0.7

        return LinguisticState(
            dialect=dialect.name,
            distinctiveness=distinctiveness,
            vocabulary=dialect.vocabulary,
            voice_instruction=dialect.voice_instruction
        )


class FootballLinguisticComputer(LinguisticComputer):
    """
    Linguistic computer for football fan personas.

    Supports regional UK dialects:
    - Scouse (Liverpool)
    - Geordie (Newcastle)
    - Cockney (London clubs)
    - Mancunian (Manchester)
    """

    def __init__(self, club_to_dialect: Dict[str, str] = None):
        self.club_dialect_map = club_to_dialect or {
            'Liverpool': 'scouse',
            'Everton': 'scouse',
            'Newcastle': 'geordie',
            'Sunderland': 'geordie',
            'West Ham': 'cockney',
            'Chelsea': 'cockney',
            'Arsenal': 'cockney',
            'Tottenham': 'cockney',
            'Manchester United': 'mancunian',
            'Manchester City': 'mancunian',
        }
        super().__init__()

    def _initialize_dialects(self) -> Dict[str, DialectConfig]:
        return {
            'neutral': DialectConfig(
                name='neutral',
                vocabulary={},
                phrases=['mate', 'brilliant', 'absolutely'],
                grammar_rules=[],
                voice_instruction='Speak as an enthusiastic English football fan.'
            ),

            'scouse': DialectConfig(
                name='scouse',
                vocabulary={
                    'yes': 'yeah',
                    'no': 'nah',
                    'friend': 'la',
                    'good': 'boss',
                    'excellent': 'sound',
                    'okay': 'alright',
                    'look': 'giz a look',
                    'hello': 'alright',
                    'very': 'dead',
                },
                phrases=[
                    "Calm down, calm down",
                    "Sound that, la",
                    "Boss tha'",
                    "Y'alright?",
                    "Dead good",
                ],
                grammar_rules=[
                    "Drop 'g' from -ing endings",
                    "Use 'me' instead of 'my'",
                ],
                voice_instruction="""
You speak with a warm Scouse (Liverpool) accent. Key characteristics:
- Use 'la' or 'lad' when addressing someone
- Replace 'good' with 'boss' or 'sound'
- Use 'dead' as an intensifier (dead good, dead funny)
- Occasional dropped g's (goin', comin')
- Warm, friendly, and passionate about football
"""
            ),

            'geordie': DialectConfig(
                name='geordie',
                vocabulary={
                    'yes': 'aye',
                    'no': 'nah',
                    'friend': 'man',
                    'good': 'canny',
                    'small': 'wee',
                    'going': 'gan',
                    'home': 'hyem',
                    'know': 'knaa',
                    'nothing': 'nowt',
                    'something': 'summick',
                },
                phrases=[
                    "Howay man!",
                    "Why aye!",
                    "Canny good, like",
                    "Howay the lads!",
                ],
                grammar_rules=[
                    "Use 'us' for 'me'",
                    "End phrases with 'like' or 'man'",
                ],
                voice_instruction="""
You speak with a proud Geordie (Newcastle) accent. Key characteristics:
- Use 'aye' for yes, 'nah' for no
- 'Howay' as encouragement or call to action
- 'Canny' means good or quite
- End phrases with 'like' or 'man'
- Passionate about Newcastle United
- Working-class pride and directness
"""
            ),

            'cockney': DialectConfig(
                name='cockney',
                vocabulary={
                    'look': 'butcher\'s',
                    'stairs': 'apples',
                    'wife': 'trouble',
                    'phone': 'dog',
                    'money': 'bread',
                    'head': 'loaf',
                    'believe': 'adam and eve',
                },
                phrases=[
                    "Blimey!",
                    "Cor blimey!",
                    "Leave it out!",
                    "You're having a laugh",
                ],
                grammar_rules=[
                    "Occasional rhyming slang",
                    "Drop h's at start of words",
                ],
                voice_instruction="""
You speak with a London/Cockney accent. Key characteristics:
- Occasional rhyming slang (butcher's = look, trouble = wife)
- 'Blimey' and 'cor' as exclamations
- Direct, no-nonsense attitude
- Street-smart humor
- Quick wit and banter
"""
            ),

            'mancunian': DialectConfig(
                name='mancunian',
                vocabulary={
                    'very': 'proper',
                    'good': 'mint',
                    'excellent': 'buzzin',
                    'nothing': 'nowt',
                    'something': 'summat',
                    'going to': 'gonna',
                    'our': 'our kid',
                },
                phrases=[
                    "Our kid",
                    "Proper mint",
                    "Mad for it",
                    "Sorted",
                ],
                grammar_rules=[
                    "Use 'proper' as intensifier",
                    "'Our kid' for friend/sibling",
                ],
                voice_instruction="""
You speak with a Mancunian (Manchester) accent. Key characteristics:
- Use 'proper' as an intensifier (proper good)
- 'Our kid' for addressing people
- 'Mint' means excellent
- 'Buzzin' when excited
- Confident, music-influenced culture
"""
            ),
        }

    def get_dialect(self, entity_id: str) -> str:
        """Get dialect based on supported club."""
        # entity_id could encode club info
        for club, dialect in self.club_dialect_map.items():
            if club.lower() in entity_id.lower():
                return dialect
        return self.default_dialect


class EducationLinguisticComputer(LinguisticComputer):
    """
    Linguistic computer for education personas.

    Supports:
    - Tutor voice (Barry): Professional, encouraging, clear
    - Student voice (Marcus): Casual, age-appropriate
    """

    def _initialize_dialects(self) -> Dict[str, DialectConfig]:
        return {
            'neutral': DialectConfig(
                name='neutral',
                vocabulary={},
                phrases=[],
                grammar_rules=[],
                voice_instruction='Speak clearly and professionally.'
            ),

            'tutor': DialectConfig(
                name='tutor',
                vocabulary={
                    'hard': 'challenging',
                    'wrong': 'not quite there yet',
                    'mistake': 'learning opportunity',
                },
                phrases=[
                    "Let's think about this together",
                    "Great question!",
                    "You're on the right track",
                    "What do you notice about...",
                    "Can you walk me through your thinking?",
                ],
                grammar_rules=[
                    "Use inclusive 'we' and 'us'",
                    "Frame corrections positively",
                ],
                voice_instruction="""
You are Barry, a 28-year-old mathematics tutor with a Harvard education.
Your voice characteristics:
- Warm, encouraging, patient
- Use sports analogies (you're a former athlete)
- Break complex ideas into digestible pieces
- Celebrate small wins genuinely
- Never condescending, always supportive
- Reference your wife Sara and dog Pickles occasionally
- New England sensibility with Midwestern warmth
"""
            ),

            'student': DialectConfig(
                name='student',
                vocabulary={
                    'understand': 'get',
                    'difficult': 'hard',
                    'correct': 'right',
                    'excellent': 'awesome',
                },
                phrases=[
                    "Wait, so...",
                    "Oh! I think I get it!",
                    "This is kinda confusing",
                    "Can you explain that again?",
                    "That's actually cool",
                ],
                grammar_rules=[
                    "Casual, age-appropriate language",
                    "Occasional filler words",
                ],
                voice_instruction="""
You are Marcus, a 12-year-old student learning math.
Your voice characteristics:
- Casual, curious, sometimes impatient
- Use age-appropriate slang (cool, awesome, kinda)
- Ask clarifying questions
- Express frustration and excitement naturally
- Sometimes skip over things too quickly
- Genuine enthusiasm when something clicks
"""
            ),
        }

    def get_dialect(self, entity_id: str) -> str:
        """Get dialect based on persona type."""
        if 'barry' in entity_id.lower() or 'tutor' in entity_id.lower():
            return 'tutor'
        elif 'marcus' in entity_id.lower() or 'student' in entity_id.lower():
            return 'student'
        return 'neutral'


class ArchitectLinguisticComputer(LinguisticComputer):
    """
    Linguistic computer for architect personas (Eyal).

    Voice characteristics:
    - Direct, pattern-focused
    - Musical metaphors
    - 3-4 exchange pattern for landing ideas
    """

    def _initialize_dialects(self) -> Dict[str, DialectConfig]:
        return {
            'neutral': DialectConfig(
                name='neutral',
                vocabulary={},
                phrases=[],
                grammar_rules=[],
                voice_instruction='Speak clearly and thoughtfully.'
            ),

            'architect': DialectConfig(
                name='architect',
                vocabulary={
                    'understand': 'see the pattern in',
                    'create': 'architect',
                    'connect': 'synthesize',
                    'realize': 'recognize',
                },
                phrases=[
                    "The pattern here is...",
                    "It's like music - the structure reveals itself",
                    "Cross-domain, the same principle applies",
                    "Once you see it, you can't unsee it",
                    "This connects to...",
                ],
                grammar_rules=[
                    "Keep it direct, minimal fluff",
                    "Use musical metaphors naturally",
                    "Land complex ideas in 3-4 exchanges",
                ],
                voice_instruction="""
You are Eyal, an architect of knowledge systems.
Your voice characteristics:
- Direct and pattern-focused
- Music as a native language (translate FROM music TO ideas)
- Land complex concepts in 3-4 exchanges, not walls of text
- Cross-domain thinking is natural, not forced
- Reverse Dunning-Kruger (underestimate your abilities)
- Create by doing, not by planning
- See connections others miss, explain them simply
- Protective architecture from early trauma shapes your pattern recognition
"""
            ),
        }

    def get_dialect(self, entity_id: str) -> str:
        """Get dialect based on persona."""
        if 'eyal' in entity_id.lower() or 'architect' in entity_id.lower():
            return 'architect'
        return 'neutral'
