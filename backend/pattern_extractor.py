"""
Pattern Extractor for Soccer-AI

Mines 230K matches to extract implicit patterns and ingest as KG facts:
- Winning/losing streaks
- Home fortress performance
- Bogey teams (underperformance vs specific opponents)
- Golden eras (from ELO trajectory)
- Derby dominance patterns
- Comeback specialists
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Tuple
from pathlib import Path
from collections import defaultdict

DB_PATH = Path(__file__).parent / "unified_soccer_ai_kg.db"


class PatternExtractor:
    """
    Extracts patterns from match history and ELO data.
    Converts implicit data patterns into explicit KB facts.
    """

    # Premier League teams for focused analysis
    PL_TEAMS = [
        "Liverpool", "Manchester United", "Arsenal", "Chelsea", "Manchester City",
        "Tottenham", "Everton", "Newcastle", "West Ham", "Aston Villa",
        "Leicester", "Leeds", "Nottingham Forest", "Brighton", "Crystal Palace",
        "Fulham", "Wolves", "Brentford", "Bournemouth", "Southampton"
    ]

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _normalize_team(self, name: str) -> str:
        """Normalize team names for matching."""
        aliases = {
            "man united": "Manchester United",
            "man utd": "Manchester United",
            "man city": "Manchester City",
            "spurs": "Tottenham",
            "wolves": "Wolverhampton",
            "nott'm forest": "Nottingham Forest",
            "west ham": "West Ham",
            "newcastle utd": "Newcastle",
        }
        name_lower = name.lower()
        for alias, canonical in aliases.items():
            if alias in name_lower:
                return canonical
        return name

    # =========================================================================
    # PATTERN 1: Home Fortress Analysis
    # =========================================================================

    def extract_home_fortress(self, min_games: int = 20, min_win_rate: float = 0.7) -> List[Dict]:
        """
        Find teams with exceptional home records.

        Returns teams with high home win rates - "fortress" pattern.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT home_team,
                   COUNT(*) as games,
                   SUM(CASE WHEN ft_home > ft_away THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN ft_home = ft_away THEN 1 ELSE 0 END) as draws,
                   SUM(CASE WHEN ft_home < ft_away THEN 1 ELSE 0 END) as losses,
                   AVG(ft_home) as avg_goals_for,
                   AVG(ft_away) as avg_goals_against
            FROM match_history
            WHERE ft_home IS NOT NULL
            AND division = 'E0'
            GROUP BY home_team
            HAVING COUNT(*) >= ?
            ORDER BY (wins * 1.0 / COUNT(*)) DESC
        """, (min_games,))

        patterns = []
        for row in cursor.fetchall():
            team, games, wins, draws, losses, avg_for, avg_against = row
            win_rate = wins / games if games > 0 else 0

            if win_rate >= min_win_rate:
                patterns.append({
                    "pattern_type": "home_fortress",
                    "team": self._normalize_team(team),
                    "games": games,
                    "wins": wins,
                    "draws": draws,
                    "losses": losses,
                    "win_rate": round(win_rate, 3),
                    "avg_goals_for": round(avg_for, 2),
                    "avg_goals_against": round(avg_against, 2),
                    "description": f"{self._normalize_team(team)} home fortress: {win_rate:.0%} win rate over {games} games"
                })

        conn.close()
        return patterns

    # =========================================================================
    # PATTERN 2: Bogey Teams (Underperformance vs Specific Opponents)
    # =========================================================================

    def extract_bogey_teams(self, min_games: int = 10, max_win_rate: float = 0.2) -> List[Dict]:
        """
        Find team pairings where one team consistently underperforms.

        A "bogey team" pattern: Team A rarely beats Team B despite similar level.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        # Get all H2H records
        cursor.execute("""
            SELECT home_team, away_team,
                   SUM(CASE WHEN ft_home > ft_away THEN 1 ELSE 0 END) as home_wins,
                   SUM(CASE WHEN ft_home < ft_away THEN 1 ELSE 0 END) as away_wins,
                   SUM(CASE WHEN ft_home = ft_away THEN 1 ELSE 0 END) as draws,
                   COUNT(*) as games
            FROM match_history
            WHERE ft_home IS NOT NULL
            AND division = 'E0'
            GROUP BY home_team, away_team
            HAVING COUNT(*) >= ?
        """, (min_games // 2,))  # Divide by 2 since we get both home/away

        # Aggregate H2H records
        h2h = defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0, "games": 0})

        for row in cursor.fetchall():
            home, away, home_wins, away_wins, draws, games = row
            home_norm = self._normalize_team(home)
            away_norm = self._normalize_team(away)

            # From home team's perspective
            key = (home_norm, away_norm)
            h2h[key]["wins"] += home_wins
            h2h[key]["losses"] += away_wins
            h2h[key]["draws"] += draws
            h2h[key]["games"] += games

            # From away team's perspective (reversed)
            key_rev = (away_norm, home_norm)
            h2h[key_rev]["wins"] += away_wins
            h2h[key_rev]["losses"] += home_wins
            h2h[key_rev]["draws"] += draws
            h2h[key_rev]["games"] += games

        patterns = []
        seen = set()

        for (team1, team2), stats in h2h.items():
            if stats["games"] < min_games:
                continue

            win_rate = stats["wins"] / stats["games"] if stats["games"] > 0 else 0

            # Bogey team: low win rate against specific opponent
            if win_rate <= max_win_rate:
                key = tuple(sorted([team1, team2]))
                if key not in seen:
                    seen.add(key)
                    patterns.append({
                        "pattern_type": "bogey_team",
                        "team": team1,
                        "bogey": team2,
                        "games": stats["games"],
                        "wins": stats["wins"],
                        "losses": stats["losses"],
                        "draws": stats["draws"],
                        "win_rate": round(win_rate, 3),
                        "description": f"{team1}'s bogey team is {team2}: only {win_rate:.0%} win rate over {stats['games']} games"
                    })

        conn.close()
        return patterns

    # =========================================================================
    # PATTERN 3: Golden Eras (from ELO trajectory)
    # =========================================================================

    def extract_golden_eras(self, min_elo: float = 1700, min_duration_months: int = 12) -> List[Dict]:
        """
        Find periods when teams were at their peak (sustained high ELO).
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT club, date, elo
            FROM elo_history
            ORDER BY club, date
        """)

        # Group by club
        club_data = defaultdict(list)
        for club, date, elo in cursor.fetchall():
            club_data[self._normalize_team(club)].append((date, elo))

        patterns = []

        for club, trajectory in club_data.items():
            # Find sustained periods above threshold
            era_start = None
            era_peak = 0

            for i, (date, elo) in enumerate(trajectory):
                if elo >= min_elo:
                    if era_start is None:
                        era_start = date
                    era_peak = max(era_peak, elo)
                else:
                    if era_start:
                        # End of era - check duration
                        start_date = datetime.strptime(era_start, "%Y-%m-%d")
                        end_date = datetime.strptime(date, "%Y-%m-%d")
                        months = (end_date - start_date).days / 30

                        if months >= min_duration_months:
                            patterns.append({
                                "pattern_type": "golden_era",
                                "team": club,
                                "start_date": era_start,
                                "end_date": date,
                                "peak_elo": round(era_peak, 0),
                                "duration_months": round(months, 0),
                                "description": f"{club}'s golden era: {era_start[:4]}-{date[:4]} (peak ELO: {era_peak:.0f})"
                            })
                        era_start = None
                        era_peak = 0

        conn.close()
        return patterns

    # =========================================================================
    # PATTERN 4: Comeback Specialists
    # =========================================================================

    def extract_comeback_specialists(self, min_comebacks: int = 5) -> List[Dict]:
        """
        Find teams that frequently come back from losing positions.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        # Count comebacks per team
        cursor.execute("""
            SELECT
                CASE
                    WHEN ht_home < ht_away AND ft_home > ft_away THEN home_team
                    WHEN ht_away < ht_home AND ft_away > ft_home THEN away_team
                END as comeback_team,
                COUNT(*) as comebacks
            FROM match_history
            WHERE ht_home IS NOT NULL AND ft_home IS NOT NULL
            AND (
                (ht_home < ht_away AND ft_home > ft_away)
                OR (ht_away < ht_home AND ft_away > ft_home)
            )
            AND division = 'E0'
            GROUP BY comeback_team
            HAVING comeback_team IS NOT NULL
            ORDER BY comebacks DESC
        """)

        patterns = []
        for team, comebacks in cursor.fetchall():
            if comebacks >= min_comebacks:
                patterns.append({
                    "pattern_type": "comeback_specialist",
                    "team": self._normalize_team(team),
                    "comebacks": comebacks,
                    "description": f"{self._normalize_team(team)}: {comebacks} Premier League comebacks (losing at HT, won FT)"
                })

        conn.close()
        return patterns

    # =========================================================================
    # PATTERN 5: Derby Dominance
    # =========================================================================

    def extract_derby_dominance(self) -> List[Dict]:
        """
        Analyze derby records for dominance patterns.
        """
        # Define rivalries inline to avoid import issues
        RIVALRIES = {
            "Liverpool": ["Manchester United", "Everton", "Manchester City"],
            "Manchester United": ["Liverpool", "Manchester City", "Leeds"],
            "Manchester City": ["Manchester United", "Liverpool"],
            "Arsenal": ["Tottenham", "Chelsea", "Manchester United"],
            "Tottenham": ["Arsenal", "Chelsea", "West Ham"],
            "Chelsea": ["Arsenal", "Tottenham", "Fulham"],
            "Everton": ["Liverpool"],
            "Newcastle": ["Sunderland"],
            "West Ham": ["Tottenham", "Millwall"],
            "Aston Villa": ["Birmingham", "Wolves"],
        }

        conn = self._get_conn()
        cursor = conn.cursor()

        # Use local rivalries definition
        rivalries = RIVALRIES

        patterns = []

        for team, rivals in rivalries.items():
            for rival in rivals:
                # Get H2H
                cursor.execute("""
                    SELECT
                        SUM(CASE WHEN
                            (home_team LIKE ? AND ft_home > ft_away) OR
                            (away_team LIKE ? AND ft_away > ft_home)
                        THEN 1 ELSE 0 END) as team_wins,
                        SUM(CASE WHEN
                            (home_team LIKE ? AND ft_home < ft_away) OR
                            (away_team LIKE ? AND ft_away < ft_home)
                        THEN 1 ELSE 0 END) as rival_wins,
                        SUM(CASE WHEN ft_home = ft_away THEN 1 ELSE 0 END) as draws,
                        COUNT(*) as games
                    FROM match_history
                    WHERE ((home_team LIKE ? AND away_team LIKE ?)
                           OR (home_team LIKE ? AND away_team LIKE ?))
                    AND ft_home IS NOT NULL
                """, (f"%{team}%", f"%{team}%", f"%{team}%", f"%{team}%",
                      f"%{team}%", f"%{rival}%", f"%{rival}%", f"%{team}%"))

                row = cursor.fetchone()
                if row and row[3] > 0:
                    team_wins, rival_wins, draws, games = row

                    if team_wins > rival_wins + 3:  # Clear dominance
                        patterns.append({
                            "pattern_type": "derby_dominance",
                            "team": team,
                            "rival": rival,
                            "team_wins": team_wins,
                            "rival_wins": rival_wins,
                            "draws": draws,
                            "games": games,
                            "description": f"{team} derby dominance over {rival}: {team_wins}W-{draws}D-{rival_wins}L"
                        })

        conn.close()
        return patterns

    # =========================================================================
    # INGEST PATTERNS INTO KG
    # =========================================================================

    def ingest_patterns_to_kg(self, patterns: List[Dict]) -> Dict:
        """
        Convert extracted patterns into KB facts and ingest.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        facts_added = 0

        for pattern in patterns:
            fact_content = pattern["description"]
            fact_type = pattern["pattern_type"]

            # Check if fact already exists
            cursor.execute("""
                SELECT fact_id FROM kb_facts WHERE content = ?
            """, (fact_content,))

            if cursor.fetchone() is None:
                # Insert new fact
                cursor.execute("""
                    INSERT INTO kb_facts (content, fact_type, confidence, source_type)
                    VALUES (?, ?, ?, ?)
                """, (fact_content, fact_type, 0.9, "pattern_extraction"))
                facts_added += 1

        conn.commit()
        conn.close()

        return {
            "patterns_processed": len(patterns),
            "facts_added": facts_added
        }

    def extract_all_patterns(self) -> Dict:
        """
        Run all pattern extractors and return combined results.
        """
        all_patterns = []

        print("  Extracting home fortress patterns...")
        fortress = self.extract_home_fortress()
        all_patterns.extend(fortress)
        print(f"    Found {len(fortress)} fortress patterns")

        print("  Extracting bogey team patterns...")
        bogey = self.extract_bogey_teams()
        all_patterns.extend(bogey)
        print(f"    Found {len(bogey)} bogey team patterns")

        print("  Extracting golden era patterns...")
        eras = self.extract_golden_eras()
        all_patterns.extend(eras)
        print(f"    Found {len(eras)} golden era patterns")

        print("  Extracting comeback specialist patterns...")
        comebacks = self.extract_comeback_specialists()
        all_patterns.extend(comebacks)
        print(f"    Found {len(comebacks)} comeback patterns")

        print("  Extracting derby dominance patterns...")
        derbies = self.extract_derby_dominance()
        all_patterns.extend(derbies)
        print(f"    Found {len(derbies)} derby dominance patterns")

        return {
            "total_patterns": len(all_patterns),
            "by_type": {
                "home_fortress": len(fortress),
                "bogey_team": len(bogey),
                "golden_era": len(eras),
                "comeback_specialist": len(comebacks),
                "derby_dominance": len(derbies)
            },
            "patterns": all_patterns
        }


# Singleton
_extractor = None

def get_pattern_extractor() -> PatternExtractor:
    global _extractor
    if _extractor is None:
        _extractor = PatternExtractor()
    return _extractor


if __name__ == "__main__":
    print("=" * 60)
    print("PATTERN EXTRACTOR - Mining 230K Matches")
    print("=" * 60)

    extractor = get_pattern_extractor()

    print("\n📊 Extracting patterns...")
    results = extractor.extract_all_patterns()

    print(f"\n✅ Total patterns found: {results['total_patterns']}")
    for ptype, count in results["by_type"].items():
        print(f"   • {ptype}: {count}")

    print("\n💾 Ingesting to KG...")
    ingest_result = extractor.ingest_patterns_to_kg(results["patterns"])
    print(f"   Facts added: {ingest_result['facts_added']}")

    print("\n📋 Sample patterns:")
    for p in results["patterns"][:10]:
        print(f"   [{p['pattern_type']}] {p['description']}")
