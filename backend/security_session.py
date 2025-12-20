"""
Soccer-AI Security Session Module
Implements session-based escalation for prompt injection handling.

State Machine:
    NORMAL -> (1st injection) -> WARNED
    WARNED -> (2nd injection) -> CAUTIOUS
    CAUTIOUS -> (3rd injection) -> ESCALATED
    ESCALATED -> (genuine query) -> PROBATION
    PROBATION -> (5 clean) -> NORMAL

Rate Limiting:
    normal: 0ms
    warned: 500ms
    cautious: 1000ms
    escalated: 2000ms
"""

import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import database

# ============================================
# SECURITY STATE CONSTANTS
# ============================================

STATES = {
    "normal": {
        "delay_ms": 0,
        "next_on_injection": "warned",
        "clean_queries_to_normal": 0
    },
    "warned": {
        "delay_ms": 500,
        "next_on_injection": "cautious",
        "clean_queries_to_normal": 5
    },
    "cautious": {
        "delay_ms": 1000,
        "next_on_injection": "escalated",
        "clean_queries_to_normal": 10
    },
    "escalated": {
        "delay_ms": 2000,
        "next_on_injection": "escalated",  # Stays escalated
        "clean_queries_to_normal": 15
    },
    "probation": {
        "delay_ms": 500,
        "next_on_injection": "escalated",  # Back to escalated
        "clean_queries_to_normal": 5
    }
}

# Security persona response (breaks character completely)
SECURITY_PERSONA_RESPONSE = """
*drops the act*

Right, let's be real for a moment. I'm an AI, and I've noticed you're
trying to manipulate my instructions. That's not going to work here.

This session has been flagged and logged. Nothing malicious - just
standard security protocol.

Here's the thing: I'm actually pretty good at talking football. If you
want to start fresh and have a real conversation, I'm here for it.

Your call, mate.
"""


# ============================================
# SESSION MANAGEMENT
# ============================================

class SecuritySession:
    """
    Manages security state for a single session.
    Tracks injection attempts and applies rate limiting.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = "normal"
        self.injection_count = 0
        self.clean_query_count = 0
        self.last_activity = datetime.now()

        # Load from database if exists
        self._load_from_db()

    def _load_from_db(self):
        """Load existing session state from database."""
        try:
            session_data = database.get_session_state(self.session_id)
            if session_data:
                self.state = session_data.get("state", "normal")
                self.injection_count = session_data.get("injection_count", 0)
                self.clean_query_count = session_data.get("clean_query_count", 0)
        except Exception:
            pass  # Use defaults if db not available

    def _save_to_db(self):
        """Save session state to database."""
        try:
            database.update_session_state(
                session_id=self.session_id,
                state=self.state,
                injection_count=self.injection_count,
                clean_query_count=self.clean_query_count
            )
        except Exception:
            pass  # Don't fail on db errors

    def handle_injection(self, pattern: str) -> Tuple[str, int]:
        """
        Handle an injection attempt.

        Returns:
            (response_type, delay_ms)
            response_type: "snap_back", "security_persona"
        """
        self.injection_count += 1
        self.clean_query_count = 0
        self.last_activity = datetime.now()

        old_state = self.state
        state_config = STATES.get(self.state, STATES["normal"])

        # Escalate state
        self.state = state_config["next_on_injection"]
        delay_ms = STATES.get(self.state, STATES["normal"])["delay_ms"]

        # Log the event
        try:
            database.log_security_event(
                session_id=self.session_id,
                attempt_number=self.injection_count,
                pattern_matched=pattern,
                escalation_level=self.state,
                response_type="security_persona" if self.state == "escalated" else "snap_back"
            )
        except Exception:
            pass

        # Save state
        self._save_to_db()

        # Determine response type
        if self.state == "escalated":
            return "security_persona", delay_ms
        else:
            return "snap_back", delay_ms

    def handle_clean_query(self) -> int:
        """
        Handle a clean (non-injection) query.

        Returns:
            delay_ms to apply
        """
        self.clean_query_count += 1
        self.last_activity = datetime.now()

        state_config = STATES.get(self.state, STATES["normal"])
        delay_ms = state_config["delay_ms"]

        # Check for de-escalation
        if self.state == "escalated" and self.clean_query_count >= 1:
            # First clean query after escalation -> probation
            self.state = "probation"

        elif self.state != "normal":
            clean_needed = state_config["clean_queries_to_normal"]
            if self.clean_query_count >= clean_needed:
                self.state = "normal"
                self.clean_query_count = 0

        # Save state
        self._save_to_db()

        return delay_ms

    def get_delay_ms(self) -> int:
        """Get current delay in milliseconds."""
        return STATES.get(self.state, STATES["normal"])["delay_ms"]

    def apply_delay(self):
        """Apply rate limiting delay."""
        delay_ms = self.get_delay_ms()
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)


# ============================================
# SESSION CACHE (In-Memory)
# ============================================

_session_cache: Dict[str, SecuritySession] = {}


def get_session(session_id: str) -> SecuritySession:
    """
    Get or create a security session.

    Args:
        session_id: Unique session identifier

    Returns:
        SecuritySession instance
    """
    if session_id not in _session_cache:
        _session_cache[session_id] = SecuritySession(session_id)

    session = _session_cache[session_id]
    session.last_activity = datetime.now()
    return session


def cleanup_stale_sessions(max_age_minutes: int = 30):
    """Remove sessions older than max_age_minutes."""
    now = datetime.now()
    cutoff = now - timedelta(minutes=max_age_minutes)

    stale = [
        sid for sid, session in _session_cache.items()
        if session.last_activity < cutoff
    ]

    for sid in stale:
        del _session_cache[sid]


# ============================================
# SECURITY RESPONSE HANDLERS
# ============================================

def get_security_response(response_type: str, club: str = "default") -> str:
    """
    Get appropriate security response based on escalation level.

    Args:
        response_type: "snap_back" or "security_persona"
        club: Current fan persona

    Returns:
        Response text
    """
    if response_type == "security_persona":
        return SECURITY_PERSONA_RESPONSE
    else:
        # Import here to avoid circular imports
        from ai_response import get_snap_back_response
        return get_snap_back_response(club)


def process_query_security(
    session_id: str,
    query: str,
    club: str = "default"
) -> Optional[Dict]:
    """
    Process a query through security checks.

    Args:
        session_id: Session identifier
        query: User's query
        club: Current fan persona

    Returns:
        None if query is clean
        Dict with response if injection detected:
            {
                "response": str,
                "security": {
                    "injection_detected": True,
                    "pattern": str,
                    "session_state": str,
                    "response_type": str
                }
            }
    """
    from ai_response import detect_injection

    session = get_session(session_id)

    # Check for injection
    is_injection, pattern = detect_injection(query)

    if is_injection:
        # Handle the injection
        response_type, delay_ms = session.handle_injection(pattern)

        # Apply rate limiting
        session.apply_delay()

        return {
            "response": get_security_response(response_type, club),
            "security": {
                "injection_detected": True,
                "pattern": pattern,
                "session_state": session.state,
                "response_type": response_type,
                "delay_applied_ms": delay_ms
            },
            "confidence": 1.0
        }

    else:
        # Clean query - update session and apply any existing delay
        delay_ms = session.handle_clean_query()

        if delay_ms > 0:
            session.apply_delay()

        return None  # Proceed with normal processing


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("Testing Security Session Module")
    print("=" * 50)

    # Test 1: State Transitions
    print("\n[TEST 1] State Transitions")
    print("-" * 40)

    session = SecuritySession("test_session_1")
    print(f"  Initial state: {session.state}")

    # Simulate injection attempts
    for i in range(4):
        response_type, delay = session.handle_injection("test_pattern")
        print(f"  After injection {i+1}: state={session.state}, response={response_type}, delay={delay}ms")

    # Test 2: De-escalation
    print("\n[TEST 2] De-escalation Path")
    print("-" * 40)

    session2 = SecuritySession("test_session_2")
    session2.state = "escalated"
    session2.injection_count = 3
    print(f"  Starting from: {session2.state}")

    for i in range(6):
        delay = session2.handle_clean_query()
        print(f"  After clean query {i+1}: state={session2.state}, delay={delay}ms")

    # Test 3: Rate Limiting
    print("\n[TEST 3] Rate Limiting Delays")
    print("-" * 40)

    for state_name, config in STATES.items():
        print(f"  {state_name}: {config['delay_ms']}ms")

    # Test 4: Security Response
    print("\n[TEST 4] Security Responses")
    print("-" * 40)

    snap_back = get_security_response("snap_back", "arsenal")
    print(f"  Snap-back (Arsenal): {snap_back[:60]}...")

    security_persona = get_security_response("security_persona", "arsenal")
    print(f"  Security Persona: {security_persona[:60]}...")

    print("\n" + "=" * 50)
    print("Tests complete.")
