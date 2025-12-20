"""
Rate Limiter & Daily Budget Cap

Per-IP rate limiting for AI-powered endpoints + global daily budget tracker.
No external dependencies — pure in-memory with automatic cleanup.

Limits:
- Chat: 30 requests/minute per IP
- Debate: 5 requests/hour per IP
- Companion simulation: 3 per hour per IP
- Non-AI endpoints (trivia, predictions, standings): 60/minute per IP
- Global daily budget: $5/day (configurable via DAILY_BUDGET_CAP env var)
"""

import os
import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

# ─── Configuration ─────────────────────────────────────────────

DAILY_BUDGET_CAP = float(os.environ.get("DAILY_BUDGET_CAP", "5.0"))

# Cost per endpoint type (approximate Haiku costs)
ENDPOINT_COSTS = {
    "chat": 0.002,        # ~1 Haiku call
    "debate": 0.012,      # ~6 Haiku calls
    "companion": 0.018,   # ~9 Haiku calls
    "free": 0.0,          # No AI cost
}

# Rate limits: (max_requests, window_seconds)
RATE_LIMITS = {
    "chat": (30, 60),          # 30 per minute
    "debate": (5, 3600),       # 5 per hour
    "companion": (3, 3600),    # 3 per hour
    "free": (60, 60),          # 60 per minute
}


# ─── Per-IP Rate Tracker ──────────────────────────────────────

@dataclass
class IPTracker:
    requests: list = field(default_factory=list)  # List of timestamps


class RateLimiter:
    def __init__(self):
        self._trackers: Dict[str, Dict[str, IPTracker]] = defaultdict(
            lambda: defaultdict(IPTracker)
        )
        self._lock = threading.Lock()

    def check(self, ip: str, endpoint_type: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a request from this IP is allowed.
        Returns (allowed, error_message).
        """
        if endpoint_type not in RATE_LIMITS:
            return True, None

        max_requests, window = RATE_LIMITS[endpoint_type]
        now = time.time()

        with self._lock:
            tracker = self._trackers[ip][endpoint_type]
            # Clean old entries
            tracker.requests = [t for t in tracker.requests if now - t < window]

            if len(tracker.requests) >= max_requests:
                retry_after = int(window - (now - tracker.requests[0]))
                return False, f"Rate limit exceeded. Try again in {retry_after}s."

            tracker.requests.append(now)
            return True, None

    def cleanup(self):
        """Remove stale entries (call periodically)."""
        now = time.time()
        with self._lock:
            stale_ips = []
            for ip, types in self._trackers.items():
                all_empty = True
                for etype, tracker in types.items():
                    window = RATE_LIMITS.get(etype, (0, 60))[1]
                    tracker.requests = [t for t in tracker.requests if now - t < window]
                    if tracker.requests:
                        all_empty = False
                if all_empty:
                    stale_ips.append(ip)
            for ip in stale_ips:
                del self._trackers[ip]


# ─── Global Daily Budget Tracker ──────────────────────────────

class BudgetTracker:
    def __init__(self, daily_cap: float = DAILY_BUDGET_CAP):
        self.daily_cap = daily_cap
        self._spend: float = 0.0
        self._reset_date: str = ""
        self._lock = threading.Lock()

    def _maybe_reset(self):
        """Reset spend counter at midnight UTC."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._reset_date:
            self._spend = 0.0
            self._reset_date = today

    def check_and_charge(self, endpoint_type: str) -> Tuple[bool, Optional[str]]:
        """
        Check if we're within budget and charge the cost.
        Returns (allowed, error_message).
        Free endpoints always pass.
        """
        cost = ENDPOINT_COSTS.get(endpoint_type, 0)
        if cost == 0:
            return True, None

        with self._lock:
            self._maybe_reset()

            if self._spend + cost > self.daily_cap:
                remaining = max(0, self.daily_cap - self._spend)
                return False, (
                    f"Daily AI budget reached (${self.daily_cap:.2f}/day). "
                    f"Try the Demo, Trivia, Predictions, or Standings — "
                    f"they work without AI. Budget resets at midnight UTC."
                )

            self._spend += cost
            return True, None

    @property
    def remaining(self) -> float:
        with self._lock:
            self._maybe_reset()
            return max(0, self.daily_cap - self._spend)

    @property
    def spent_today(self) -> float:
        with self._lock:
            self._maybe_reset()
            return self._spend


# ─── Singleton Instances ──────────────────────────────────────

_rate_limiter = RateLimiter()
_budget_tracker = BudgetTracker()


def check_rate_limit(ip: str, endpoint_type: str) -> Tuple[bool, Optional[str]]:
    """
    Combined check: per-IP rate limit + global daily budget.
    Returns (allowed, error_message).
    """
    # Rate limit check
    allowed, msg = _rate_limiter.check(ip, endpoint_type)
    if not allowed:
        return False, msg

    # Budget check
    allowed, msg = _budget_tracker.check_and_charge(endpoint_type)
    if not allowed:
        return False, msg

    return True, None


def get_budget_status() -> Dict:
    """Get current budget status."""
    return {
        "daily_cap": DAILY_BUDGET_CAP,
        "spent_today": round(_budget_tracker.spent_today, 4),
        "remaining": round(_budget_tracker.remaining, 4),
        "currency": "USD",
    }
