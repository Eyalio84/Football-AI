"""
Soccer-AI 4D Persona Configuration

This module centralizes configuration for the 4D Persona Architecture integration.
Set USE_4D_PERSONA = False to use legacy fan_enhancements behavior.
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
# REGIONAL DIALECT GROUPINGS (User Requirement Q2: Option B)
# =============================================================================
# Instead of per-club dialects, clubs are grouped into regional dialects

DIALECT_REGIONS = {
    "north": [
        "liverpool", "everton",
        "manchester_united", "manchester_city",
        "newcastle"
    ],
    "midlands": [
        "aston_villa", "wolves",
        "nottingham_forest", "leicester"
    ],
    "london": [
        "arsenal", "chelsea", "tottenham",
        "west_ham", "crystal_palace",
        "fulham", "brentford"
    ],
    "south": [
        "brighton", "bournemouth", "southampton"
    ],
    "east": [
        "ipswich"
    ]
}

# Reverse mapping: club -> region
CLUB_TO_REGION = {}
for region, clubs in DIALECT_REGIONS.items():
    for club in clubs:
        CLUB_TO_REGION[club] = region


# =============================================================================
# CLUB NORMALIZATION
# =============================================================================
# Map internal club_id to display names and API names

CLUB_DISPLAY_NAMES = {
    "arsenal": "Arsenal",
    "aston_villa": "Aston Villa",
    "bournemouth": "Bournemouth",
    "brentford": "Brentford",
    "brighton": "Brighton & Hove Albion",
    "chelsea": "Chelsea",
    "crystal_palace": "Crystal Palace",
    "everton": "Everton",
    "fulham": "Fulham",
    "ipswich": "Ipswich Town",
    "leicester": "Leicester City",
    "liverpool": "Liverpool",
    "manchester_city": "Manchester City",
    "manchester_united": "Manchester United",
    "newcastle": "Newcastle United",
    "nottingham_forest": "Nottingham Forest",
    "southampton": "Southampton",
    "tottenham": "Tottenham Hotspur",
    "west_ham": "West Ham United",
    "wolves": "Wolverhampton Wanderers"
}

# API team names (football-data.org format)
CLUB_API_NAMES = {
    "arsenal": "Arsenal FC",
    "aston_villa": "Aston Villa FC",
    "bournemouth": "AFC Bournemouth",
    "brentford": "Brentford FC",
    "brighton": "Brighton & Hove Albion FC",
    "chelsea": "Chelsea FC",
    "crystal_palace": "Crystal Palace FC",
    "everton": "Everton FC",
    "fulham": "Fulham FC",
    "ipswich": "Ipswich Town FC",
    "leicester": "Leicester City FC",
    "liverpool": "Liverpool FC",
    "manchester_city": "Manchester City FC",
    "manchester_united": "Manchester United FC",
    "newcastle": "Newcastle United FC",
    "nottingham_forest": "Nottingham Forest FC",
    "southampton": "Southampton FC",
    "tottenham": "Tottenham Hotspur FC",
    "west_ham": "West Ham United FC",
    "wolves": "Wolverhampton Wanderers FC"
}


# =============================================================================
# ARIEL FRAMEWORK PATH
# =============================================================================

ARIEL_FRAMEWORK_PATH = str(Path(__file__).parent.parent / "robert")
