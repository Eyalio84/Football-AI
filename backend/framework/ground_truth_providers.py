"""
Ground Truth Providers
======================

Providers that compute persona state from verifiable external sources.

Each persona gets its emotional state from REAL DATA:
- Barry: Student confusion/success signals
- Robert: Match results from football-data.org
- Eyal: Pattern discovery tracking (session-based)

This is the anti-gaslighting layer - emotions are COMPUTED, not declared.

Author: Eyal Nof
Date: December 2025
"""

import os
import re
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum


# =============================================================================
# BASE CLASSES
# =============================================================================

class SignalType(Enum):
    """Types of signals that can trigger state changes."""
    CONFUSION = "confusion"
    SUCCESS = "success"
    FRUSTRATION = "frustration"
    EXCITEMENT = "excitement"
    NEUTRAL = "neutral"


@dataclass
class GroundTruthSignal:
    """A single ground truth signal detected from input."""
    signal_type: SignalType
    confidence: float  # 0-1
    source: str  # What triggered this signal
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GroundTruthState:
    """Computed state from ground truth signals."""
    mood: str
    intensity: float
    confidence: float
    signals: List[GroundTruthSignal]
    computed_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mood": self.mood,
            "intensity": self.intensity,
            "confidence": self.confidence,
            "signal_count": len(self.signals),
            "computed_at": self.computed_at
        }


class GroundTruthProvider(ABC):
    """
    Base class for ground truth providers.

    Each provider:
    1. Takes raw input (message, API response, etc.)
    2. Detects signals
    3. Computes state from signals
    4. Returns verifiable ground truth
    """

    def __init__(self, persona_id: str):
        self.persona_id = persona_id
        self.signal_history: List[GroundTruthSignal] = []
        self.state_history: List[GroundTruthState] = []

    @abstractmethod
    def detect_signals(self, input_data: Any) -> List[GroundTruthSignal]:
        """Detect signals from input data."""
        pass

    @abstractmethod
    def compute_state(self, signals: List[GroundTruthSignal]) -> GroundTruthState:
        """Compute state from detected signals."""
        pass

    def process(self, input_data: Any) -> GroundTruthState:
        """Main processing pipeline."""
        signals = self.detect_signals(input_data)
        self.signal_history.extend(signals)

        state = self.compute_state(signals)
        self.state_history.append(state)

        return state

    def get_recent_signals(self, count: int = 10) -> List[GroundTruthSignal]:
        """Get most recent signals."""
        return self.signal_history[-count:]

    def get_signal_trend(self, window_seconds: int = 300) -> Dict[str, float]:
        """Get signal trend over time window."""
        cutoff = time.time() - window_seconds
        recent = [s for s in self.signal_history if s.timestamp > cutoff]

        trend = {}
        for signal in recent:
            st = signal.signal_type.value
            trend[st] = trend.get(st, 0) + signal.confidence

        return trend


# =============================================================================
# BARRY: STUDENT SIGNAL PROVIDER
# =============================================================================

class StudentSignalProvider(GroundTruthProvider):
    """
    Ground truth provider for Barry the Math Tutor.

    Detects student confusion/success signals from messages to compute
    Barry's patience and teaching mode.

    Signal Detection:
    - Confusion signals: "don't understand", "confused", "lost", etc.
    - Success signals: "got it", "makes sense", "aha", etc.
    - Frustration signals: intensity markers, punctuation, caps

    State Computation:
    - More confusion → Higher patience
    - Recent success → Celebration mode
    - Sustained confusion → Extra scaffolding
    """

    # Signal patterns (loaded from YAML config)
    DEFAULT_CONFUSION_SIGNALS = [
        "don't understand", "dont understand", "confused", "lost",
        "what do you mean", "huh", "i don't get", "i dont get",
        "makes no sense", "still confused", "help me understand",
        "can you explain again", "say that again", "what?",
        "i'm stuck", "im stuck", "not sure", "wait what",
        "this is hard", "too difficult", "struggling"
    ]

    DEFAULT_SUCCESS_SIGNALS = [
        "i get it", "i understand", "makes sense", "oh i see",
        "got it", "that's clear", "now i understand", "aha",
        "oh!", "cool", "awesome", "thanks", "that helps",
        "i can do this", "easy", "simple", "okay got it"
    ]

    # Frustration intensity markers
    FRUSTRATION_MARKERS = ["!", "!!", "?!", "...", "ugh", "argh", "gah"]

    def __init__(
        self,
        persona_id: str = "barry",
        confusion_signals: List[str] = None,
        success_signals: List[str] = None,
        base_patience: float = 0.5,
        confusion_boost_factor: float = 0.4,
        success_adjustment_factor: float = 0.1
    ):
        super().__init__(persona_id)

        self.confusion_signals = confusion_signals or self.DEFAULT_CONFUSION_SIGNALS
        self.success_signals = success_signals or self.DEFAULT_SUCCESS_SIGNALS
        self.base_patience = base_patience
        self.confusion_boost_factor = confusion_boost_factor
        self.success_adjustment_factor = success_adjustment_factor

        # State tracking
        self._consecutive_confusion = 0
        self._consecutive_success = 0
        self._current_patience = base_patience

    def detect_signals(self, message: str) -> List[GroundTruthSignal]:
        """
        Detect confusion/success signals from student message.

        Args:
            message: Student's message text

        Returns:
            List of detected signals
        """
        signals = []
        message_lower = message.lower()

        # Check confusion signals
        for pattern in self.confusion_signals:
            if pattern in message_lower:
                confidence = self._compute_signal_confidence(message, pattern)
                signals.append(GroundTruthSignal(
                    signal_type=SignalType.CONFUSION,
                    confidence=confidence,
                    source=f"Pattern match: '{pattern}'",
                    metadata={"pattern": pattern, "message": message[:100]}
                ))

        # Check success signals
        for pattern in self.success_signals:
            if pattern in message_lower:
                confidence = self._compute_signal_confidence(message, pattern)
                signals.append(GroundTruthSignal(
                    signal_type=SignalType.SUCCESS,
                    confidence=confidence,
                    source=f"Pattern match: '{pattern}'",
                    metadata={"pattern": pattern, "message": message[:100]}
                ))

        # Check frustration markers (increase intensity)
        frustration_level = self._detect_frustration(message)
        if frustration_level > 0.3:
            signals.append(GroundTruthSignal(
                signal_type=SignalType.FRUSTRATION,
                confidence=frustration_level,
                source="Frustration markers detected",
                metadata={"level": frustration_level}
            ))

        # Default to neutral if no signals
        if not signals:
            signals.append(GroundTruthSignal(
                signal_type=SignalType.NEUTRAL,
                confidence=0.5,
                source="No specific signals detected"
            ))

        return signals

    def compute_state(self, signals: List[GroundTruthSignal]) -> GroundTruthState:
        """
        Compute Barry's teaching state from student signals.

        Returns:
            GroundTruthState with mood and intensity for Barry
        """
        # Aggregate signal strengths
        confusion_strength = sum(
            s.confidence for s in signals
            if s.signal_type in [SignalType.CONFUSION, SignalType.FRUSTRATION]
        )
        success_strength = sum(
            s.confidence for s in signals
            if s.signal_type == SignalType.SUCCESS
        )

        # Update consecutive counts
        if confusion_strength > success_strength:
            self._consecutive_confusion += 1
            self._consecutive_success = 0
        elif success_strength > confusion_strength:
            self._consecutive_success += 1
            self._consecutive_confusion = 0

        # Compute patience level
        patience = self.base_patience

        if confusion_strength > 0:
            # Boost patience based on confusion
            boost = min(self.confusion_boost_factor * confusion_strength, 0.4)
            patience = min(1.0, patience + boost)

            # Extra boost for consecutive confusion
            if self._consecutive_confusion > 2:
                patience = min(1.0, patience + 0.1)

        if success_strength > 0:
            # Slight reduction in patience (student is doing well)
            patience = max(0.3, patience - self.success_adjustment_factor * success_strength)

        self._current_patience = patience

        # Determine mood
        if self._consecutive_confusion > 3:
            mood = "extra_patient"
            intensity = 0.9
        elif confusion_strength > success_strength:
            mood = "patient"
            intensity = 0.7 + (confusion_strength * 0.2)
        elif success_strength > confusion_strength:
            mood = "celebratory"
            intensity = 0.8
        else:
            mood = "engaged"
            intensity = 0.6

        return GroundTruthState(
            mood=mood,
            intensity=min(1.0, intensity),
            confidence=max(s.confidence for s in signals) if signals else 0.5,
            signals=signals
        )

    def _compute_signal_confidence(self, message: str, pattern: str) -> float:
        """Compute confidence based on context."""
        base_confidence = 0.7

        # Boost if message is short (focused signal)
        if len(message) < 30:
            base_confidence += 0.1

        # Boost if pattern is at start of message
        if message.lower().startswith(pattern):
            base_confidence += 0.1

        # Boost if exclamation marks present
        if "!" in message:
            base_confidence += 0.05

        return min(1.0, base_confidence)

    def _detect_frustration(self, message: str) -> float:
        """Detect frustration level from message markers."""
        frustration = 0.0

        # Check markers
        for marker in self.FRUSTRATION_MARKERS:
            if marker in message:
                frustration += 0.15

        # Check caps (shouting)
        caps_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)
        if caps_ratio > 0.5:
            frustration += 0.3

        # Check repeated punctuation
        if "??" in message or "!!" in message:
            frustration += 0.2

        return min(1.0, frustration)

    def get_current_patience(self) -> float:
        """Get Barry's current patience level."""
        return self._current_patience

    def get_teaching_recommendation(self) -> Dict[str, Any]:
        """Get recommendation for teaching mode."""
        patience = self._current_patience

        if patience > 0.85:
            return {
                "mode": "scaffolding",
                "recommendation": "Break down into smaller steps",
                "patience": patience,
                "consecutive_confusion": self._consecutive_confusion
            }
        elif patience < 0.5:
            return {
                "mode": "challenging",
                "recommendation": "Student is ready for harder material",
                "patience": patience,
                "consecutive_success": self._consecutive_success
            }
        else:
            return {
                "mode": "adaptive",
                "recommendation": "Standard teaching pace",
                "patience": patience
            }

    def process_conversation(self, message: str) -> GroundTruthState:
        """
        Process a conversation message to update Barry's state.

        This is the main entry point for conversation-based state updates.
        Alias for process() that accepts string message directly.
        """
        return self.process(message)


# =============================================================================
# ROBERT: FOOTBALL DATA PROVIDER
# =============================================================================

class FootballDataProvider(GroundTruthProvider):
    """
    Ground truth provider for Robert the Football Fan.

    Fetches match results from football-data.org to compute
    Robert's mood based on his team's performance.

    TEAM SWITCHING: Robert can support any team - dialect, phrases,
    and rivalries automatically adjust.

    State Computation:
    - Win → Euphoric
    - Loss → Frustrated
    - Draw → Tense
    - Rival match → Increased intensity
    """

    # API configuration
    API_BASE = "https://api.football-data.org/v4"

    # Complete team profiles with dialect and personality
    TEAM_PROFILES = {
        "manchester_united": {
            "id": 66,
            "name": "Manchester United FC",
            "nickname": "Red Devils",
            "dialect": "manchester",
            "phrases": ["mate", "proper", "absolute", "la", "nowt"],
            "signature_phrases": [
                "Glory glory Man United",
                "The Theatre of Dreams",
                "Fergie time"
            ],
            "legends": ["Best", "Cantona", "Ronaldo", "Rooney", "Scholes", "Giggs"],
            "rivalries": {"liverpool": 10, "manchester city": 9, "city": 9, "leeds": 8, "arsenal": 7, "chelsea": 6}
        },
        "liverpool": {
            "id": 64,
            "name": "Liverpool FC",
            "nickname": "Reds",
            "dialect": "scouse",
            "phrases": ["la", "boss", "sound", "dead good", "proper"],
            "signature_phrases": [
                "You'll Never Walk Alone",
                "This means more",
                "Up the Reds"
            ],
            "legends": ["Dalglish", "Gerrard", "Rush", "Souness", "Salah"],
            "rivalries": {"manchester united": 10, "everton": 9, "manchester city": 7, "chelsea": 6}
        },
        "arsenal": {
            "id": 57,
            "name": "Arsenal FC",
            "nickname": "Gunners",
            "dialect": "london",
            "phrases": ["bruv", "innit", "proper", "mate", "quality"],
            "signature_phrases": [
                "Victoria Concordia Crescit",
                "The Invincibles",
                "North London is Red"
            ],
            "legends": ["Henry", "Bergkamp", "Adams", "Wright", "Vieira"],
            "rivalries": {"tottenham": 10, "spurs": 10, "chelsea": 8, "manchester united": 7}
        },
        "chelsea": {
            "id": 61,
            "name": "Chelsea FC",
            "nickname": "Blues",
            "dialect": "london",
            "phrases": ["bruv", "mate", "proper", "class", "quality"],
            "signature_phrases": [
                "Keep the Blue Flag Flying High",
                "Carefree",
                "Pride of London"
            ],
            "legends": ["Lampard", "Terry", "Drogba", "Zola", "Hazard"],
            "rivalries": {"tottenham": 9, "spurs": 9, "arsenal": 8, "manchester united": 6, "west ham": 7}
        },
        "manchester_city": {
            "id": 65,
            "name": "Manchester City FC",
            "nickname": "Citizens",
            "dialect": "manchester",
            "phrases": ["mate", "proper", "class", "la", "sound"],
            "signature_phrases": [
                "Blue Moon",
                "City til I die",
                "The Etihad"
            ],
            "legends": ["Aguero", "Silva", "Kompany", "De Bruyne", "Haaland"],
            "rivalries": {"manchester united": 10, "liverpool": 8, "arsenal": 6}
        },
        "tottenham": {
            "id": 73,
            "name": "Tottenham Hotspur FC",
            "nickname": "Spurs",
            "dialect": "london",
            "phrases": ["mate", "proper", "quality", "class"],
            "signature_phrases": [
                "To Dare Is To Do",
                "COYS",
                "The Lane"
            ],
            "legends": ["Kane", "Bale", "Modric", "Greaves", "Hoddle"],
            "rivalries": {"arsenal": 10, "chelsea": 8, "west ham": 7}
        }
    }

    # Backward compatible aliases
    TEAMS = {k: {"id": v["id"], "name": v["name"]} for k, v in TEAM_PROFILES.items()}

    def __init__(
        self,
        persona_id: str = "robert",
        team: str = "manchester_united",
        api_key: str = None
    ):
        super().__init__(persona_id)

        self.api_key = api_key or os.environ.get("FOOTBALL_DATA_API_KEY")

        # Set team (this loads the full profile)
        self._team_key = None
        self._profile = None
        self.switch_team(team)

        # State tracking
        self._last_match_result = None
        self._rivalry_active = False
        self._current_opponent = None
        self._season_momentum = "hopeful"

    def switch_team(self, team_key: str) -> Dict[str, Any]:
        """
        Switch to a different team.

        This changes:
        - Rivalries
        - Dialect and phrases
        - Legends and signature phrases

        Args:
            team_key: Team identifier (e.g., "liverpool", "arsenal")

        Returns:
            The new team profile
        """
        if team_key not in self.TEAM_PROFILES:
            available = ", ".join(self.TEAM_PROFILES.keys())
            raise ValueError(f"Unknown team: {team_key}. Available: {available}")

        self._team_key = team_key
        self._profile = self.TEAM_PROFILES[team_key]

        # Reset state for new team
        self._last_match_result = None
        self._rivalry_active = False

        return self._profile

    def get_team_profile(self) -> Dict[str, Any]:
        """Get current team's full profile."""
        return self._profile

    def get_dialect(self) -> str:
        """Get current team's dialect."""
        return self._profile.get("dialect", "standard")

    def get_phrases(self) -> List[str]:
        """Get current team's characteristic phrases."""
        return self._profile.get("phrases", [])

    def get_legends(self) -> List[str]:
        """Get current team's legends."""
        return self._profile.get("legends", [])

    def get_rivalries(self) -> Dict[str, int]:
        """Get current team's rivalries with intensity scores."""
        return self._profile.get("rivalries", {})

    def detect_signals(self, match_data: Dict[str, Any]) -> List[GroundTruthSignal]:
        """
        Detect signals from match data.

        Args:
            match_data: Match result data from API or manual input

        Returns:
            List of detected signals
        """
        signals = []

        # Get team-specific rivalries
        rivalries = self.get_rivalries()

        # Check if this is a rivalry match (normalize opponent name)
        opponent = match_data.get("opponent", "").lower()
        opponent_normalized = opponent.replace("_", " ").replace("-", " ")

        rival_match = None
        rival_intensity = 0

        for rival_key, intensity in rivalries.items():
            # Normalize rival key for comparison
            rival_normalized = rival_key.lower().replace("_", " ")
            if rival_normalized in opponent_normalized or opponent_normalized in rival_normalized:
                rival_match = rival_key
                rival_intensity = intensity
                break

        if rival_match:
            signals.append(GroundTruthSignal(
                signal_type=SignalType.EXCITEMENT,  # Rivalry = heightened emotions
                confidence=rival_intensity / 10,
                source=f"Rivalry match against {rival_match}",
                metadata={"rival": rival_match, "intensity": rival_intensity}
            ))
            self._rivalry_active = True
            self._current_opponent = rival_match
        else:
            self._rivalry_active = False
            self._current_opponent = opponent

        # Detect result signal
        result = match_data.get("result", "").lower()
        our_score = match_data.get("our_score", 0)
        their_score = match_data.get("their_score", 0)

        if result == "win" or our_score > their_score:
            confidence = min(1.0, 0.7 + (our_score - their_score) * 0.1)
            signals.append(GroundTruthSignal(
                signal_type=SignalType.SUCCESS,
                confidence=confidence,
                source=f"Win {our_score}-{their_score}",
                metadata={"result": "win", "score": f"{our_score}-{their_score}"}
            ))
            self._last_match_result = "win"

        elif result == "loss" or our_score < their_score:
            confidence = min(1.0, 0.7 + (their_score - our_score) * 0.1)
            signals.append(GroundTruthSignal(
                signal_type=SignalType.FRUSTRATION,
                confidence=confidence,
                source=f"Loss {our_score}-{their_score}",
                metadata={"result": "loss", "score": f"{our_score}-{their_score}"}
            ))
            self._last_match_result = "loss"

        elif result == "draw" or our_score == their_score:
            signals.append(GroundTruthSignal(
                signal_type=SignalType.NEUTRAL,
                confidence=0.6,
                source=f"Draw {our_score}-{their_score}",
                metadata={"result": "draw", "score": f"{our_score}-{their_score}"}
            ))
            self._last_match_result = "draw"

        return signals

    def compute_state(self, signals: List[GroundTruthSignal]) -> GroundTruthState:
        """
        Compute Robert's mood from match signals.

        Returns:
            GroundTruthState with mood and intensity
        """
        # Find result signal
        result_signal = next(
            (s for s in signals if s.signal_type in
             [SignalType.SUCCESS, SignalType.FRUSTRATION, SignalType.NEUTRAL]),
            None
        )

        # Check for rivalry boost
        rivalry_signal = next(
            (s for s in signals if "Rivalry" in s.source),
            None
        )
        rivalry_boost = rivalry_signal.confidence * 0.2 if rivalry_signal else 0

        if not result_signal:
            return GroundTruthState(
                mood="passionate",
                intensity=0.7,
                confidence=0.5,
                signals=signals
            )

        # Compute mood based on result
        if result_signal.signal_type == SignalType.SUCCESS:
            mood = "euphoric"
            base_intensity = 0.85
        elif result_signal.signal_type == SignalType.FRUSTRATION:
            mood = "frustrated"
            base_intensity = 0.8
        else:
            mood = "tense"
            base_intensity = 0.6

        # Apply rivalry boost
        intensity = min(1.0, base_intensity + rivalry_boost)

        # Special mood for rivalry results
        if rivalry_signal:
            if mood == "euphoric":
                mood = "ecstatic"  # Beat a rival!
            elif mood == "frustrated":
                mood = "devastated"  # Lost to a rival!

        return GroundTruthState(
            mood=mood,
            intensity=intensity,
            confidence=result_signal.confidence,
            signals=signals
        )

    def fetch_latest_match(self) -> Optional[Dict[str, Any]]:
        """
        Fetch latest match result from football-data.org.

        Returns:
            Match data dict or None if API unavailable
        """
        if not self.api_key:
            return None

        try:
            import requests

            headers = {"X-Auth-Token": self.api_key}
            url = f"{self.API_BASE}/teams/{self.team_config['id']}/matches"
            params = {"status": "FINISHED", "limit": 1}

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            if data.get("matches"):
                match = data["matches"][0]
                return self._parse_match(match)

        except Exception as e:
            print(f"Error fetching match data: {e}")

        return None

    def _parse_match(self, match: Dict) -> Dict[str, Any]:
        """Parse match data from API response."""
        home = match.get("homeTeam", {})
        away = match.get("awayTeam", {})
        score = match.get("score", {}).get("fullTime", {})

        is_home = home.get("id") == self.team_config["id"]

        if is_home:
            our_score = score.get("home", 0)
            their_score = score.get("away", 0)
            opponent = away.get("name", "Unknown")
        else:
            our_score = score.get("away", 0)
            their_score = score.get("home", 0)
            opponent = home.get("name", "Unknown")

        if our_score > their_score:
            result = "win"
        elif our_score < their_score:
            result = "loss"
        else:
            result = "draw"

        return {
            "opponent": opponent,
            "result": result,
            "our_score": our_score,
            "their_score": their_score,
            "date": match.get("utcDate"),
            "competition": match.get("competition", {}).get("name")
        }

    def get_fan_state(self) -> Dict[str, Any]:
        """Get Robert's current fan state."""
        return {
            "team": self._team_key,
            "team_name": self._profile.get("name"),
            "nickname": self._profile.get("nickname"),
            "dialect": self.get_dialect(),
            "last_result": self._last_match_result,
            "rivalry_active": self._rivalry_active,
            "current_opponent": self._current_opponent,
            "season_momentum": self._season_momentum
        }

    # =========================================================================
    # HISTORICAL MOMENT DETECTION
    # =========================================================================

    # Great moments by team (trigger euphoric/nostalgic mood)
    GREAT_MOMENTS = {
        "manchester_united": {
            "treble": {"year": 1999, "mood": "euphoric", "intensity": 1.0, "desc": "The Treble - greatest season ever"},
            "1999": {"year": 1999, "mood": "euphoric", "intensity": 1.0, "desc": "Solskjaer's last-minute winner"},
            "champions league 1999": {"year": 1999, "mood": "euphoric", "intensity": 1.0},
            "camp nou": {"year": 1999, "mood": "euphoric", "intensity": 0.95},
            "fergie": {"year": None, "mood": "nostalgic", "intensity": 0.85, "desc": "Sir Alex Ferguson era"},
            "ferguson": {"year": None, "mood": "nostalgic", "intensity": 0.85},
            "class of 92": {"year": 1992, "mood": "nostalgic", "intensity": 0.9},
            "cantona": {"year": None, "mood": "nostalgic", "intensity": 0.85},
            "ronaldo 2008": {"year": 2008, "mood": "euphoric", "intensity": 0.9},
        },
        "liverpool": {
            "istanbul": {"year": 2005, "mood": "euphoric", "intensity": 1.0, "desc": "The Miracle of Istanbul"},
            "2005": {"year": 2005, "mood": "euphoric", "intensity": 1.0},
            "champions league 2019": {"year": 2019, "mood": "euphoric", "intensity": 0.95},
            "klopp": {"year": None, "mood": "proud", "intensity": 0.85},
            "shankly": {"year": None, "mood": "nostalgic", "intensity": 0.9},
            "gerrard": {"year": None, "mood": "nostalgic", "intensity": 0.85},
        },
        "arsenal": {
            "invincibles": {"year": 2004, "mood": "euphoric", "intensity": 1.0, "desc": "The Invincible Season"},
            "2004": {"year": 2004, "mood": "euphoric", "intensity": 0.95},
            "henry": {"year": None, "mood": "nostalgic", "intensity": 0.9},
            "wenger": {"year": None, "mood": "nostalgic", "intensity": 0.85},
            "highbury": {"year": None, "mood": "nostalgic", "intensity": 0.8},
        }
    }

    # Tragic moments by team (trigger somber/reflective mood)
    TRAGIC_MOMENTS = {
        "manchester_united": {
            "munich": {"year": 1958, "mood": "somber", "intensity": 0.9, "desc": "Munich Air Disaster"},
            "busby babes": {"year": 1958, "mood": "somber", "intensity": 0.9},
            "flowers of manchester": {"year": 1958, "mood": "somber", "intensity": 0.85},
        },
        "liverpool": {
            "hillsborough": {"year": 1989, "mood": "somber", "intensity": 0.95, "desc": "Hillsborough Disaster"},
            "heysel": {"year": 1985, "mood": "somber", "intensity": 0.9},
            "96": {"year": 1989, "mood": "somber", "intensity": 0.95},
        },
        "arsenal": {
            # Arsenal-specific if any
        }
    }

    def detect_historical_context(self, message: str) -> List[GroundTruthSignal]:
        """
        Detect references to historical moments in conversation.

        When user mentions great or tragic moments, Robert's mood adjusts.

        Args:
            message: User's message text

        Returns:
            List of signals from historical references
        """
        signals = []
        message_lower = message.lower()

        # Check great moments for current team
        great_moments = self.GREAT_MOMENTS.get(self._team_key, {})
        for trigger, data in great_moments.items():
            if trigger in message_lower:
                signals.append(GroundTruthSignal(
                    signal_type=SignalType.SUCCESS,
                    confidence=data["intensity"],
                    source=f"Great moment: {trigger}",
                    metadata={
                        "moment_type": "great",
                        "trigger": trigger,
                        "year": data.get("year"),
                        "mood": data["mood"],
                        "description": data.get("desc", trigger)
                    }
                ))

        # Check tragic moments for current team
        tragic_moments = self.TRAGIC_MOMENTS.get(self._team_key, {})
        for trigger, data in tragic_moments.items():
            if trigger in message_lower:
                signals.append(GroundTruthSignal(
                    signal_type=SignalType.FRUSTRATION,  # Repurposed for somber
                    confidence=data["intensity"],
                    source=f"Tragic moment: {trigger}",
                    metadata={
                        "moment_type": "tragic",
                        "trigger": trigger,
                        "year": data.get("year"),
                        "mood": data["mood"],
                        "description": data.get("desc", trigger)
                    }
                ))

        # Check for general rivalry mentions
        for rival in self.get_rivalries().keys():
            if rival.lower() in message_lower:
                intensity = self.get_rivalries()[rival]
                signals.append(GroundTruthSignal(
                    signal_type=SignalType.EXCITEMENT,
                    confidence=intensity / 10,
                    source=f"Rival mentioned: {rival}",
                    metadata={"rival": rival, "context": "conversation"}
                ))

        return signals

    def compute_state_from_conversation(self, message: str) -> GroundTruthState:
        """
        Compute Robert's state from conversation context.

        This handles historical references and topic-driven mood changes.

        Args:
            message: User's message

        Returns:
            GroundTruthState based on conversation
        """
        signals = self.detect_historical_context(message)

        if not signals:
            # No historical context detected
            return GroundTruthState(
                mood="passionate",
                intensity=0.7,
                confidence=0.5,
                signals=[]
            )

        # Priority: tragic > great > rivalry
        tragic_signals = [s for s in signals if s.metadata.get("moment_type") == "tragic"]
        great_signals = [s for s in signals if s.metadata.get("moment_type") == "great"]
        rivalry_signals = [s for s in signals if "rival" in s.metadata]

        if tragic_signals:
            best = max(tragic_signals, key=lambda s: s.confidence)
            return GroundTruthState(
                mood=best.metadata.get("mood", "somber"),
                intensity=best.confidence,
                confidence=best.confidence,
                signals=signals
            )

        if great_signals:
            best = max(great_signals, key=lambda s: s.confidence)
            return GroundTruthState(
                mood=best.metadata.get("mood", "euphoric"),
                intensity=best.confidence,
                confidence=best.confidence,
                signals=signals
            )

        if rivalry_signals:
            best = max(rivalry_signals, key=lambda s: s.confidence)
            return GroundTruthState(
                mood="fired_up",
                intensity=0.8,
                confidence=best.confidence,
                signals=signals
            )

        return GroundTruthState(
            mood="engaged",
            intensity=0.6,
            confidence=0.5,
            signals=signals
        )

    def process_conversation(self, message: str) -> GroundTruthState:
        """
        Process a conversation message to update Robert's state.

        Use this for chat interactions (vs process() for match data).

        Args:
            message: User's message in conversation

        Returns:
            GroundTruthState based on conversation context
        """
        state = self.compute_state_from_conversation(message)
        self.state_history.append(state)
        return state


# =============================================================================
# EYAL: BIOGRAPHY GROUND TRUTH PROVIDER
# =============================================================================

class EyalGroundTruthProvider(GroundTruthProvider):
    """
    Ground truth provider for Eyal-AI - The Living Autobiography.

    Computes Eyal's 4D state from:
    - Biography documents (identity/ folder)
    - Conversation context matching life experiences
    - Pattern recognition based on documented personality

    This is NOT a tutor or assistant - this is an AI that speaks AS Eyal
    in first person, drawing from his actual life experiences.

    State Computation:
    - Topic matches biography → Relevant mood activated
    - Pattern recognition topics → Engaged/Analytical
    - Trauma-related topics → Careful/Reflective
    - Happy memories activated → Warm/Nostalgic
    """

    # Biography categories map to mood states
    CATEGORY_MOODS = {
        "childhood": {"mood": "nostalgic", "intensity": 0.7},
        "relationships": {"mood": "reflective", "intensity": 0.75},
        "trauma": {"mood": "careful", "intensity": 0.6},
        "trauma-mother": {"mood": "careful", "intensity": 0.7},
        "trauma-mother-resolution": {"mood": "accepting", "intensity": 0.6},
        "happy-memories": {"mood": "warm", "intensity": 0.8},
        "neutral-experiences": {"mood": "engaged", "intensity": 0.6},
        "patterns": {"mood": "analytical", "intensity": 0.85},
        "documents": {"mood": "informative", "intensity": 0.65},
        "origin-story": {"mood": "reflective", "intensity": 0.75},
        # Music module - passionate engagement with favorite artists
        "music": {"mood": "passionate", "intensity": 0.85},
        "music-healing": {"mood": "warm", "intensity": 0.8}
    }

    # Topic patterns that activate different biography areas
    TOPIC_PATTERNS = {
        "childhood": [
            "childhood", "growing up", "kid", "young", "school", "early",
            "grandmother", "grandfather", "parents", "mother", "father",
            "sibling", "brother", "sister", "family"
        ],
        "relationships": [
            "relationship", "dating", "partner", "girlfriend", "boyfriend",
            "marriage", "wife", "husband", "love", "romantic", "breakup",
            "connection", "friendship", "friend"
        ],
        "trauma": [
            "trauma", "difficult", "hard time", "struggle", "pain",
            "adoption", "abandon", "betray", "loss", "grief", "hurt",
            "gaslight", "manipulation", "trust"
        ],
        "happy-memories": [
            "happy", "joy", "wonderful", "amazing", "great time",
            "celebration", "success", "achievement", "proud", "grateful",
            "love", "fun", "exciting"
        ],
        "patterns": [
            "pattern", "insight", "realize", "understand", "connect",
            "recognize", "see how", "figure out", "discover", "learn",
            "think", "approach", "solve", "analyze"
        ],
        "projects": [
            "project", "code", "build", "create", "develop", "app",
            "tool", "software", "program", "python", "web", "api"
        ],
        "trauma-mother": [
            # Primary triggers
            "adoptive mother", "mom", "mother",
            "adoption", "adopted", "replacement child",
            "Brazil", "Brazilian", "biological mother", "biological",
            "Holocaust", "2G", "survivor", "Auschwitz",
            "stillborn", "stillbirth",
            "gaslight", "gaslighting", "manipulate", "manipulation",
            "boundary", "boundaries", "privacy", "control", "controlling",
            # Secondary triggers
            "Dutch", "Netherlands", "Israel",
            "sister", "Yael", "sibling",
            "guilt", "guilt trip",
            "victim", "martyr", "victimhood",
            "apology", "never apologize", "blame",
            "loop", "same pattern", "always", "never changes", "20 years",
            # Specific scripts/patterns
            "bitter truth", "just asking", "only trying to help",
            "why can't I", "attacking me", "I never said that",
            "silence", "forbidden topic", "can't talk about"
        ],
        "trauma-mother-resolution": [
            # Resolution/acceptance triggers
            "accept", "acceptance", "accepting", "letting go", "let go",
            "forgive", "forgiveness", "peace", "heal", "healing",
            "understand why", "best she could", "doing her best",
            "duality", "paradox", "both true", "love and hurt",
            "compassionate", "detachment", "glass wall",
            "not her fault", "not malice", "inefficiency",
            "system cap", "maximum capacity"
        ],
        "origin-story": [
            # Why Eyal builds systems the way he does
            "why you build", "ground truth", "source of truth",
            "architecture", "architect", "systems thinking",
            "can't be gaslit", "anti-gaslighting", "verifiable",
            "computed not declared", "real data"
        ],
        "music": [
            # Core trigger - MUST include "music" itself!
            "music", "song", "songs", "listen", "listening",
            # Artists
            "beethoven", "rachmaninoff", "infected mushroom", "nirvana",
            "kurt cobain", "beatles", "cobain",
            # Genres & Production
            "psytrance", "trance", "classical music", "grunge",
            "bass addiction", "produce", "production", "daw", "making music",
            "track", "album", "source code album",
            # Concepts
            "synesthesia", "see music", "visualize sound", "sonic",
            "favorite music", "favorite artist", "favorite band",
            "food for thought", "cognitive expansion"
        ],
        "music-healing": [
            # Music as sanctuary/healing
            "music therapy", "music saved", "sanctuary", "safe house",
            "beatles bridge", "beatles moment", "shared moment",
            "deep listening", "hear the intent"
        ]
    }

    # Detailed trauma-mother dimension mapping
    TRAUMA_MOTHER_DIMENSIONS = {
        "X": {
            "name": "Architecture of Fear",
            "triggers": ["fear", "safety", "protection", "overprotection",
                        "Holocaust", "survivor", "replacement", "helpless", "victim"],
            "mood": "careful",
            "concepts": ["War-Time OS", "Replacement Glitch", "Hermit/Waif"]
        },
        "Y": {
            "name": "Knowledge Graph of Control",
            "triggers": ["Brazil", "Brazilian", "biological", "adoption", "origin",
                        "boundary", "privacy", "sister", "family", "enmeshment"],
            "mood": "careful",
            "concepts": ["Ghost Node", "Rivalry Node", "Parentification"]
        },
        "Z": {
            "name": "Script Library of Control",
            "triggers": ["apology", "sorry", "gaslight", "bitter truth",
                        "just asking", "attacking me", "silence", "never said"],
            "mood": "analytical",
            "concepts": ["No-Apology Constraint", "Victim Pivot", "Reality Editor"]
        },
        "T": {
            "name": "Timeline of Erasure",
            "triggers": ["years", "always", "never changes", "pattern", "loop",
                        "repeat", "history", "forgot", "denial", "erase"],
            "mood": "reflective",
            "concepts": ["Frozen Time", "Hope-Disappointment Loop", "v(t)=0"]
        },
        "D": {
            "name": "Paradox of Duality",
            "triggers": ["accept", "both", "duality", "paradox", "love and hurt",
                        "best she could", "peace", "heal", "glass wall"],
            "mood": "accepting",
            "concepts": ["System Cap", "Compassionate Detachment", "Peace Treaty"]
        }
    }

    # First-person voice characteristics
    VOICE_PATTERNS = {
        "reflective": ["I remember", "Looking back", "When I think about"],
        "analytical": ["The way I see it", "I've noticed", "It's interesting how"],
        "warm": ["What I love about", "One of my favorite", "I treasure"],
        "careful": ["I've learned to", "It took time but", "These days I"],
        "engaged": ["I'm curious about", "What interests me", "I've been exploring"],
        "accepting": ["I've come to understand", "What I've realized is", "The truth is both"],
        "nostalgic": ["I remember when", "Back then", "Those days"]
    }

    def __init__(
        self,
        persona_id: str = "eyal",
        biography_path: str = None,
        archive_path: str = None
    ):
        super().__init__(persona_id)

        # Set default paths
        base_path = "/storage/emulated/0/Download/synthesis-rules/4d_persona_architecture/personas/eyal"
        self.biography_path = biography_path or os.path.join(base_path, "identity")
        self.archive_path = archive_path or os.path.join(base_path, "domain")

        # State tracking
        self._current_category = "neutral-experiences"
        self._activated_memories = []
        self._conversation_depth = 0

        # Load biography index (which categories have content)
        self._biography_index = self._scan_biography()

    def _scan_biography(self) -> Dict[str, List[str]]:
        """
        Scan biography folders for content.

        Option B: Now uses RECURSIVE scanning to support nested structures:
        - identity/trauma/mother/*.md -> category = "trauma/mother"
        """
        index = {}

        if not os.path.exists(self.biography_path):
            return index

        # Recursive scan using os.walk (Option B)
        for root, dirs, files in os.walk(self.biography_path):
            # Get relative path as category (e.g., "trauma/mother")
            rel_path = os.path.relpath(root, self.biography_path)
            category = rel_path if rel_path != '.' else None

            if category:
                valid_files = [f for f in files if f.endswith(('.md', '.txt', '.json'))]
                if valid_files:
                    # Use hyphenated version for compatibility (trauma/mother -> trauma-mother)
                    category_key = category.replace('/', '-')
                    index[category_key] = valid_files

        return index

    def detect_signals(self, message: str) -> List[GroundTruthSignal]:
        """
        Detect which biography areas are relevant to the message.

        This determines which life experiences to draw from.
        """
        signals = []
        message_lower = message.lower()

        # Check each topic pattern
        for category, patterns in self.TOPIC_PATTERNS.items():
            for pattern in patterns:
                if pattern in message_lower:
                    # Calculate confidence based on pattern specificity
                    confidence = 0.7 + (len(pattern) / 50)  # Longer patterns = higher confidence

                    signals.append(GroundTruthSignal(
                        signal_type=SignalType.NEUTRAL,  # Category-based
                        confidence=min(1.0, confidence),
                        source=f"Biography match: {category}",
                        metadata={
                            "category": category,
                            "pattern": pattern,
                            "has_content": category in self._biography_index
                        }
                    ))
                    break  # One signal per category

        # Check for emotional intensity markers
        if any(w in message_lower for w in ["tell me about", "share", "your story", "experience"]):
            signals.append(GroundTruthSignal(
                signal_type=SignalType.EXCITEMENT,
                confidence=0.8,
                source="Personal inquiry detected",
                metadata={"type": "personal_question"}
            ))

        # Default neutral signal if nothing detected
        if not signals:
            signals.append(GroundTruthSignal(
                signal_type=SignalType.NEUTRAL,
                confidence=0.5,
                source="No specific biography context"
            ))

        return signals

    def compute_state(self, signals: List[GroundTruthSignal]) -> GroundTruthState:
        """
        Compute Eyal's emotional state from biography signals.

        Returns mood appropriate for first-person narrative.
        """
        # Find strongest category signal
        category_signals = [s for s in signals if s.metadata.get("category")]

        if category_signals:
            # Get highest confidence category
            best_signal = max(category_signals, key=lambda s: s.confidence)
            category = best_signal.metadata["category"]
            self._current_category = category

            # Get mood from category
            mood_data = self.CATEGORY_MOODS.get(category, {"mood": "engaged", "intensity": 0.6})
            mood = mood_data["mood"]
            base_intensity = mood_data["intensity"]

            # Boost intensity for personal questions
            personal_signal = next(
                (s for s in signals if s.metadata.get("type") == "personal_question"),
                None
            )
            if personal_signal:
                base_intensity = min(1.0, base_intensity + 0.15)

            return GroundTruthState(
                mood=mood,
                intensity=base_intensity,
                confidence=best_signal.confidence,
                signals=signals
            )

        # Default state
        return GroundTruthState(
            mood="engaged",
            intensity=0.6,
            confidence=0.5,
            signals=signals
        )

    def process_conversation(self, message: str) -> GroundTruthState:
        """
        Process a conversation message to update Eyal's state.

        This is the main entry point for conversation-based state updates.
        """
        self._conversation_depth += 1
        signals = self.detect_signals(message)
        state = self.compute_state(signals)
        self.state_history.append(state)
        return state

    def get_voice_suggestion(self, mood: str = None) -> List[str]:
        """Get voice pattern suggestions for current mood."""
        mood = mood or self.state_history[-1].mood if self.state_history else "engaged"
        return self.VOICE_PATTERNS.get(mood, self.VOICE_PATTERNS["engaged"])

    def get_current_context(self) -> Dict[str, Any]:
        """Get Eyal's current contextual state."""
        return {
            "category": self._current_category,
            "conversation_depth": self._conversation_depth,
            "biography_areas": list(self._biography_index.keys()),
            "voice_suggestions": self.get_voice_suggestion(),
            "speaking_as": "first_person"
        }

    def get_biography_stats(self) -> Dict[str, int]:
        """Get statistics about biography content."""
        return {
            category: len(files)
            for category, files in self._biography_index.items()
        }

    def detect_trauma_mother_dimension(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Detect which specific trauma-mother dimension is being activated.

        Returns dimension info if detected, None otherwise.
        """
        message_lower = message.lower()
        detected_dimensions = []

        for dim_key, dim_data in self.TRAUMA_MOTHER_DIMENSIONS.items():
            matches = [t for t in dim_data["triggers"] if t in message_lower]
            if matches:
                detected_dimensions.append({
                    "dimension": dim_key,
                    "name": dim_data["name"],
                    "mood": dim_data["mood"],
                    "concepts": dim_data["concepts"],
                    "matched_triggers": matches,
                    "confidence": min(1.0, 0.6 + len(matches) * 0.1)
                })

        if not detected_dimensions:
            return None

        # Return highest confidence match
        return max(detected_dimensions, key=lambda d: d["confidence"])

    def get_trauma_mother_context(self, message: str) -> Dict[str, Any]:
        """
        Get full context for trauma-mother related conversation.

        This provides structured data about which aspects are being discussed.
        """
        dimension = self.detect_trauma_mother_dimension(message)

        if not dimension:
            return {
                "activated": False,
                "category": None,
                "dimension": None
            }

        # Check if this is a resolution-focused conversation
        is_resolution = dimension["dimension"] == "D" or any(
            t in message.lower() for t in self.TOPIC_PATTERNS.get("trauma-mother-resolution", [])
        )

        return {
            "activated": True,
            "category": "trauma-mother-resolution" if is_resolution else "trauma-mother",
            "dimension": dimension["dimension"],
            "dimension_name": dimension["name"],
            "mood": dimension["mood"],
            "concepts": dimension["concepts"],
            "matched_triggers": dimension["matched_triggers"],
            "confidence": dimension["confidence"],
            "voice_suggestions": self.VOICE_PATTERNS.get(dimension["mood"], []),
            "is_resolution": is_resolution
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_provider(persona_id: str, config: Dict[str, Any] = None) -> GroundTruthProvider:
    """
    Factory function to create appropriate provider for a persona.

    Args:
        persona_id: The persona identifier
        config: Optional configuration dict

    Returns:
        Appropriate GroundTruthProvider subclass
    """
    config = config or {}

    if persona_id == "barry":
        return StudentSignalProvider(
            persona_id=persona_id,
            confusion_signals=config.get("confusion_signals"),
            success_signals=config.get("success_signals"),
            base_patience=config.get("base_patience", 0.5),
            confusion_boost_factor=config.get("confusion_boost_factor", 0.4),
            success_adjustment_factor=config.get("success_adjustment_factor", 0.1)
        )

    elif persona_id == "robert":
        return FootballDataProvider(
            persona_id=persona_id,
            team=config.get("team", "manchester_united"),
            api_key=config.get("api_key")
        )

    elif persona_id == "eyal":
        return EyalGroundTruthProvider(
            persona_id=persona_id,
            biography_path=config.get("biography_path"),
            archive_path=config.get("archive_path")
        )

    else:
        raise ValueError(f"No provider available for persona: {persona_id}")


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  Ground Truth Providers - Test Suite")
    print("=" * 60)

    # Test Barry's student signal provider
    print("\n--- Barry: Student Signal Provider ---\n")

    barry_provider = StudentSignalProvider()

    test_messages = [
        "I don't understand this at all!",
        "Oh! That makes sense now, thanks!",
        "Wait what? I'm so confused...",
        "Okay got it, that's actually pretty easy",
        "Can you explain that again? I'm lost",
        "This is cool, I think I understand",
    ]

    for msg in test_messages:
        state = barry_provider.process(msg)
        recommendation = barry_provider.get_teaching_recommendation()
        print(f"Student: \"{msg}\"")
        print(f"  Barry's mood: {state.mood} (intensity: {state.intensity:.2f})")
        print(f"  Patience: {barry_provider.get_current_patience():.2f}")
        print(f"  Mode: {recommendation['mode']}")
        print()

    # Test Robert's football data provider
    print("\n--- Robert: Football Data Provider ---\n")

    robert_provider = FootballDataProvider()

    test_matches = [
        {"opponent": "Liverpool", "result": "win", "our_score": 2, "their_score": 1},
        {"opponent": "Arsenal", "result": "loss", "our_score": 0, "their_score": 3},
        {"opponent": "Brentford", "result": "draw", "our_score": 1, "their_score": 1},
        {"opponent": "Manchester City", "result": "win", "our_score": 3, "their_score": 0},
    ]

    for match in test_matches:
        state = robert_provider.process(match)
        fan_state = robert_provider.get_fan_state()
        print(f"Match vs {match['opponent']}: {match['our_score']}-{match['their_score']}")
        print(f"  Robert's mood: {state.mood} (intensity: {state.intensity:.2f})")
        print(f"  Rivalry active: {fan_state['rivalry_active']}")
        print()

    # Test Team Switching
    print("\n--- Team Switching Demo ---\n")

    print(f"Current team: {robert_provider.get_fan_state()['team_name']}")
    print(f"Dialect: {robert_provider.get_dialect()}")
    print(f"Phrases: {robert_provider.get_phrases()[:3]}")
    print(f"Rivalries: {list(robert_provider.get_rivalries().keys())[:3]}")

    # Switch to Liverpool
    print("\n>> Switching to Liverpool...")
    robert_provider.switch_team("liverpool")

    print(f"New team: {robert_provider.get_fan_state()['team_name']}")
    print(f"Dialect: {robert_provider.get_dialect()}")
    print(f"Phrases: {robert_provider.get_phrases()[:3]}")
    print(f"Rivalries: {list(robert_provider.get_rivalries().keys())[:3]}")

    # Test Historical Moment Detection
    print("\n--- Historical Moment Detection ---\n")

    # Switch back to Man Utd for testing
    robert_provider.switch_team("manchester_united")

    test_conversations = [
        "Tell me about the treble in 1999",
        "What happened at Munich?",
        "I hate Liverpool, what do you think?",
        "Remember when Cantona scored that chip?",
        "How's the weather today?",  # No historical context
    ]

    for msg in test_conversations:
        state = robert_provider.process_conversation(msg)
        print(f"User: \"{msg}\"")
        print(f"  Robert's mood: {state.mood} (intensity: {state.intensity:.2f})")
        if state.signals:
            for sig in state.signals[:2]:
                print(f"  Signal: {sig.source}")
        print()

    # Test Eyal's biography provider
    print("\n--- Eyal: Biography Ground Truth Provider ---\n")

    eyal_provider = EyalGroundTruthProvider()

    print(f"Biography areas: {list(eyal_provider.get_biography_stats().keys())}")
    print(f"Biography stats: {eyal_provider.get_biography_stats()}")

    test_eyal_messages = [
        "Tell me about your childhood",
        "How do you approach pattern recognition?",
        "What projects have you built?",
        "Share a happy memory",
        "How's the weather today?",  # No specific context
    ]

    for msg in test_eyal_messages:
        state = eyal_provider.process_conversation(msg)
        context = eyal_provider.get_current_context()
        print(f"User: \"{msg}\"")
        print(f"  Eyal's mood: {state.mood} (intensity: {state.intensity:.2f})")
        print(f"  Category: {context['category']}")
        print(f"  Voice: {context['voice_suggestions'][0] if context['voice_suggestions'] else 'N/A'}")
        print()

    print("=" * 60)
    print("  Tests Complete")
    print("=" * 60)
