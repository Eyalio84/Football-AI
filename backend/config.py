"""
Soccer-AI 4D Persona Configuration

This module centralizes configuration for the 4D Persona Architecture integration.
Set USE_4D_PERSONA = False to use legacy fan_enhancements behavior.

Club registry (CLUB_DISPLAY_NAMES, CLUB_API_NAMES, DIALECT_REGIONS, CLUB_TO_REGION)
is now loaded dynamically from Leagues/*/league_config.json via league_loader.
Adding a new league requires only dropping a league_config.json file — no code changes.
"""

from pathlib import Path

# =============================================================================
# FEATURE FLAG
# =============================================================================

USE_4D_PERSONA = True  # Set False to use legacy fan_enhancements path


# =============================================================================
# 4D PERSONA SETTINGS
# =============================================================================

PERSONA_4D_CONFIG = {
    "cache_ttl": 300,           # Cache ground truth for 5 minutes
    "max_trajectory_length": 10, # Track last 10 4D positions
    "default_dialect_region": "neutral"
}


# =============================================================================
# DYNAMIC CLUB REGISTRY  (loaded from Leagues/ directory)
# =============================================================================

from league_loader import (
    CLUB_DISPLAY_NAMES,
    CLUB_API_NAMES,
    CLUB_TO_REGION,
    DIALECT_REGIONS,
    ALL_LEAGUES,
)

# Re-export for backward compatibility with code that imports from config
__all__ = [
    "USE_4D_PERSONA",
    "PERSONA_4D_CONFIG",
    "CLUB_DISPLAY_NAMES",
    "CLUB_API_NAMES",
    "CLUB_TO_REGION",
    "DIALECT_REGIONS",
    "ALL_LEAGUES",
    "ARIEL_FRAMEWORK_PATH",
]


# =============================================================================
# ARIEL FRAMEWORK PATH
# =============================================================================

ARIEL_FRAMEWORK_PATH = str(Path(__file__).parent.parent / "robert")
