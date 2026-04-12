"""
League Loader — Universal Football League Extractor-Builder

Dynamically discovers and loads all league configs and club knowledge files
from the Leagues/ directory. Replaces hardcoded dicts in config.py,
fan_enhancements.py, and persona_bridge.py.

Usage:
    from league_loader import CLUB_DISPLAY_NAMES, RIVALRIES, DIALECTS, ...

All mappings are built at import time by walking Leagues/*/league_config.json
and Leagues/*/clubs/*.json.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any


# ============================================================================
# DISCOVERY
# ============================================================================

def _find_leagues_dir() -> Optional[Path]:
    """Find the Leagues/ directory relative to this file or known paths."""
    candidates = [
        # Sibling of backend/ in the repo root
        Path(__file__).parent.parent / "Leagues",
        # Absolute fallback
        Path("/storage/emulated/0/Download/synthesis-rules/soccer-AI/Leagues"),
    ]
    for path in candidates:
        if path.is_dir():
            return path
    return None


LEAGUES_DIR = _find_leagues_dir()


def discover_league_dirs() -> List[Path]:
    """Return list of league directories that have a league_config.json."""
    if not LEAGUES_DIR:
        return []
    return sorted([
        d for d in LEAGUES_DIR.iterdir()
        if d.is_dir() and (d / "league_config.json").exists()
    ])


def load_league_config(league_dir: Path) -> Optional[Dict]:
    """Load and return a league_config.json file."""
    config_path = league_dir / "league_config.json"
    if not config_path.exists():
        return None
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return None


def load_club_data(league_dir: Path, club_id: str) -> Optional[Dict]:
    """Load a single club knowledge JSON file."""
    club_path = league_dir / "clubs" / f"{club_id}.json"
    if not club_path.exists():
        return None
    try:
        return json.loads(club_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return None


def load_all_clubs_for_league(league_dir: Path, league_config: Dict) -> Dict[str, Dict]:
    """Load all available club JSON files for a league. Missing files are skipped."""
    clubs = {}
    clubs_dir = league_dir / "clubs"
    if not clubs_dir.exists():
        return clubs

    for club_entry in league_config.get("clubs", []):
        club_id = club_entry["id"]
        data = load_club_data(league_dir, club_id)
        if data:
            clubs[club_id] = data
    return clubs


# ============================================================================
# MAPPING BUILDERS
# ============================================================================

def build_all_mappings() -> Dict[str, Any]:
    """
    Walk all Leagues/*/league_config.json files and build unified mappings.

    Returns dict with keys:
        club_display_names  — {club_id: display_name}
        club_api_names      — {club_id: api_name}
        club_to_region      — {club_id: dialect_region}
        club_to_db_name     — {club_id: csv_short_name}
        club_to_league      — {club_id: league_id}
        club_api_ids        — {club_id: int api_id}
        club_aliases        — {alias: club_id}   (all aliases → canonical id)
        dialect_regions     — {region: [club_id, ...]}
        leagues             — {league_id: league_config_dict}
        rivalries           — {club_id: {rival_id: {intensity, name, banter}}}
        dialects            — {club_id: {replacements, phrases, vocab_inject}}
    """
    club_display_names: Dict[str, str] = {}
    club_api_names: Dict[str, str] = {}
    club_to_region: Dict[str, str] = {}
    club_to_db_name: Dict[str, str] = {}
    club_to_league: Dict[str, str] = {}
    club_api_ids: Dict[str, int] = {}
    club_aliases: Dict[str, str] = {}  # alias → canonical club_id
    dialect_regions: Dict[str, List[str]] = {}
    leagues: Dict[str, Dict] = {}
    rivalries: Dict[str, Dict] = {}
    dialects: Dict[str, Dict] = {}

    for league_dir in discover_league_dirs():
        config = load_league_config(league_dir)
        if not config:
            continue

        league_id = config.get("league_id", league_dir.name.lower())
        leagues[league_id] = config

        # Build dialect regions for this league
        for region, region_data in config.get("dialect_regions", {}).items():
            region_clubs = region_data.get("clubs", [])
            if region not in dialect_regions:
                dialect_regions[region] = []
            dialect_regions[region].extend(region_clubs)

        # Build per-club mappings from league_config clubs array
        for club_entry in config.get("clubs", []):
            club_id = club_entry["id"]
            club_to_league[club_id] = league_id
            club_display_names[club_id] = club_entry.get("display_name", club_id)
            club_api_names[club_id] = club_entry.get("api_name", club_entry.get("display_name", club_id))
            club_to_region[club_id] = club_entry.get("dialect_region", "neutral")
            club_to_db_name[club_id] = club_entry.get("csv_name", club_entry.get("display_name", club_id))

            api_id = club_entry.get("api_id")
            if api_id is not None:
                club_api_ids[club_id] = api_id

            # Register aliases (alias → club_id)
            club_aliases[club_id] = club_id  # canonical name maps to itself
            for alias in club_entry.get("aliases", []):
                club_aliases[alias.lower()] = club_id

        # Load club knowledge files (dialect + rivalries)
        club_data_map = load_all_clubs_for_league(league_dir, config)
        for club_id, club_data in club_data_map.items():
            # Dialect
            dialect = club_data.get("dialect")
            if dialect:
                dialects[club_id] = dialect

            # Rivalries
            club_rivalries = club_data.get("rivalries")
            if club_rivalries:
                rivalries[club_id] = club_rivalries

    return {
        "club_display_names": club_display_names,
        "club_api_names": club_api_names,
        "club_to_region": club_to_region,
        "club_to_db_name": club_to_db_name,
        "club_to_league": club_to_league,
        "club_api_ids": club_api_ids,
        "club_aliases": club_aliases,
        "dialect_regions": dialect_regions,
        "leagues": leagues,
        "rivalries": rivalries,
        "dialects": dialects,
    }


# ============================================================================
# MODULE-LEVEL MAPPINGS  (built once at import time)
# ============================================================================

_mappings = build_all_mappings()

CLUB_DISPLAY_NAMES: Dict[str, str] = _mappings["club_display_names"]
CLUB_API_NAMES: Dict[str, str] = _mappings["club_api_names"]
CLUB_TO_REGION: Dict[str, str] = _mappings["club_to_region"]
CLUB_TO_DB_NAME: Dict[str, str] = _mappings["club_to_db_name"]
CLUB_TO_LEAGUE: Dict[str, str] = _mappings["club_to_league"]
CLUB_API_IDS: Dict[str, int] = _mappings["club_api_ids"]
CLUB_ALIASES: Dict[str, str] = _mappings["club_aliases"]
DIALECT_REGIONS: Dict[str, List[str]] = _mappings["dialect_regions"]
ALL_LEAGUES: Dict[str, Dict] = _mappings["leagues"]
RIVALRIES: Dict[str, Dict] = _mappings["rivalries"]
DIALECTS: Dict[str, Dict] = _mappings["dialects"]


# ============================================================================
# LOOKUP HELPERS
# ============================================================================

def get_league_for_club(club_id: str) -> Optional[str]:
    """Return the league_id this club belongs to."""
    return _mappings["club_to_league"].get(club_id)


def get_competition_code(league_id: str) -> Optional[str]:
    """Return football-data.org competition code for a league."""
    config = ALL_LEAGUES.get(league_id)
    if config:
        return config.get("competition_code")
    return None


def get_division_code(league_id: str) -> Optional[str]:
    """Return CSV division code (E0, SP1, etc.) for a league."""
    config = ALL_LEAGUES.get(league_id)
    if config:
        return config.get("division_code")
    return None


def resolve_club_alias(alias: str) -> Optional[str]:
    """Resolve an alias or display name to a canonical club_id."""
    normalized = alias.lower().replace(" ", "_").replace("-", "_")
    return CLUB_ALIASES.get(normalized)


def get_all_competition_codes() -> List[str]:
    """Return all football-data.org competition codes for registered leagues."""
    codes = []
    for config in ALL_LEAGUES.values():
        code = config.get("competition_code")
        if code:
            codes.append(code)
    return codes


def get_club_display_name(club_id: str) -> str:
    """Return display name for a club, falling back to title-cased id."""
    return CLUB_DISPLAY_NAMES.get(club_id, club_id.replace("_", " ").title())


def get_clubs_for_league(league_id: str) -> List[Dict]:
    """Return the clubs list from a league config."""
    config = ALL_LEAGUES.get(league_id)
    if config:
        return config.get("clubs", [])
    return []


def get_all_club_ids() -> List[str]:
    """Return all registered club IDs across all leagues."""
    return list(CLUB_DISPLAY_NAMES.keys())


def reload_mappings() -> None:
    """Force reload all mappings from disk. Useful after adding new league files."""
    global _mappings, CLUB_DISPLAY_NAMES, CLUB_API_NAMES, CLUB_TO_REGION
    global CLUB_TO_DB_NAME, CLUB_TO_LEAGUE, CLUB_API_IDS, CLUB_ALIASES
    global DIALECT_REGIONS, ALL_LEAGUES, RIVALRIES, DIALECTS

    _mappings = build_all_mappings()
    CLUB_DISPLAY_NAMES = _mappings["club_display_names"]
    CLUB_API_NAMES = _mappings["club_api_names"]
    CLUB_TO_REGION = _mappings["club_to_region"]
    CLUB_TO_DB_NAME = _mappings["club_to_db_name"]
    CLUB_TO_LEAGUE = _mappings["club_to_league"]
    CLUB_API_IDS = _mappings["club_api_ids"]
    CLUB_ALIASES = _mappings["club_aliases"]
    DIALECT_REGIONS = _mappings["dialect_regions"]
    ALL_LEAGUES = _mappings["leagues"]
    RIVALRIES = _mappings["rivalries"]
    DIALECTS = _mappings["dialects"]


# ============================================================================
# CLI — useful for debugging
# ============================================================================

if __name__ == "__main__":
    print(f"Leagues directory: {LEAGUES_DIR}")
    print(f"Leagues loaded: {list(ALL_LEAGUES.keys())}")
    print(f"Total clubs: {len(CLUB_DISPLAY_NAMES)}")
    print(f"Clubs with dialect data: {len(DIALECTS)}")
    print(f"Clubs with rivalry data: {len(RIVALRIES)}")
    print(f"Total aliases: {len(CLUB_ALIASES)}")
    print()
    for league_id, config in ALL_LEAGUES.items():
        clubs_with_files = sum(
            1 for c in config.get("clubs", [])
            if c["id"] in DIALECTS or c["id"] in RIVALRIES
        )
        total = len(config.get("clubs", []))
        print(f"  {config.get('display_name', league_id)}: {total} clubs "
              f"({clubs_with_files} with knowledge files)")
