"""
Match Insights Engine - Killer Features for Soccer-AI

Provides data-driven insights from 25 years of match history:
- On This Day: Historical matches on today's date
- Head-to-Head: All-time records between teams
- Comebacks: Games where losing at HT, won FT
- Upsets: When underdogs (by ELO) won
- Derby Stats: Aggregate rivalry statistics
- ELO Trajectory: Club's rating over time
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

DB_PATH = Path(__file__).parent / "unified_soccer_ai_kg.db"


class MatchInsights:
    """
    Killer features powered by 230K matches + 26K ELO snapshots.
    """

    # Team name mappings (CSV names to canonical names)
    TEAM_ALIASES = {
        "man united": ["Man United", "Manchester United", "Manchester Utd"],
        "man city": ["Man City", "Manchester City"],
        "tottenham": ["Tottenham", "Spurs", "Tottenham Hotspur"],
        "wolves": ["Wolves", "Wolverhampton"],
        "nott'm forest": ["Nott'm Forest", "Nottingham Forest", "Forest"],
        "newcastle": ["Newcastle", "Newcastle United", "Newcastle Utd"],
        "west ham": ["West Ham", "West Ham United"],
        "aston villa": ["Aston Villa", "Villa"],
        "leicester": ["Leicester", "Leicester City"],
        "leeds": ["Leeds", "Leeds United"],
        "brighton": ["Brighton", "Brighton & Hove Albion"],
        "crystal palace": ["Crystal Palace", "C Palace"],
        "sheffield united": ["Sheffield United", "Sheffield Utd", "Sheff Utd"],
        "west brom": ["West Brom", "West Bromwich", "WBA"],
    }

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _normalize_team(self, name: str) -> List[str]:
        """Get all variations of a team name for matching."""
        name_lower = name.lower()
        for canonical, aliases in self.TEAM_ALIASES.items():
            if name_lower in canonical or any(name_lower in a.lower() for a in aliases):
                return aliases
        return [name]

    def on_this_day(self, month: int = None, day: int = None,
                    team: str = None, limit: int = 10) -> List[Dict]:
        """
        Get memorable matches on this day in history.

        Args:
            month: Month (1-12), defaults to today
            day: Day (1-31), defaults to today
            team: Optional team filter
            limit: Max results
        """
        if month is None:
            month = datetime.now().month
        if day is None:
            day = datetime.now().day

        date_pattern = f"%-{month:02d}-{day:02d}"

        conn = self._get_conn()
        cursor = conn.cursor()

        query = """
            SELECT match_date, home_team, away_team, ft_home, ft_away,
                   division, home_elo, away_elo
            FROM match_history
            WHERE match_date LIKE ?
            AND ft_home IS NOT NULL
        """
        params = [date_pattern]

        if team:
            team_vars = self._normalize_team(team)
            placeholders = ','.join(['?' for _ in team_vars])
            query += f" AND (home_team IN ({placeholders}) OR away_team IN ({placeholders}))"
            params.extend(team_vars * 2)

        query += " ORDER BY (ft_home + ft_away) DESC, ABS(ft_home - ft_away) DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        results = []
        for row in cursor.fetchall():
            results.append({
                "date": row[0],
                "home_team": row[1],
                "away_team": row[2],
                "score": f"{row[3]}-{row[4]}",
                "division": row[5],
                "home_elo": row[6],
                "away_elo": row[7],
                "years_ago": datetime.now().year - int(row[0][:4]) if row[0] else None
            })

        conn.close()
        return results

    def head_to_head(self, team1: str, team2: str) -> Dict:
        """
        Get all-time head-to-head record between two teams.

        Returns:
            Dict with wins, draws, losses, goals, biggest wins for each side
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        team1_vars = self._normalize_team(team1)
        team2_vars = self._normalize_team(team2)

        # Get all matches between teams
        placeholders1 = ','.join(['?' for _ in team1_vars])
        placeholders2 = ','.join(['?' for _ in team2_vars])

        query = f"""
            SELECT match_date, home_team, away_team, ft_home, ft_away,
                   ht_home, ht_away, home_elo, away_elo
            FROM match_history
            WHERE ((home_team IN ({placeholders1}) AND away_team IN ({placeholders2}))
                   OR (home_team IN ({placeholders2}) AND away_team IN ({placeholders1})))
            AND ft_home IS NOT NULL
            ORDER BY match_date DESC
        """

        cursor.execute(query, team1_vars + team2_vars + team2_vars + team1_vars)
        matches = cursor.fetchall()

        stats = {
            "team1": team1,
            "team2": team2,
            "total_matches": len(matches),
            "team1_wins": 0,
            "team2_wins": 0,
            "draws": 0,
            "team1_goals": 0,
            "team2_goals": 0,
            "team1_biggest_win": None,
            "team2_biggest_win": None,
            "recent_matches": [],
            "all_matches": []
        }

        max_diff_t1 = 0
        max_diff_t2 = 0

        for row in matches:
            date, home, away, fth, fta, hth, hta, home_elo, away_elo = row

            # Determine if team1 is home or away
            is_team1_home = home.lower() in [t.lower() for t in team1_vars]

            if is_team1_home:
                t1_goals, t2_goals = fth, fta
            else:
                t1_goals, t2_goals = fta, fth

            stats["team1_goals"] += t1_goals
            stats["team2_goals"] += t2_goals

            if t1_goals > t2_goals:
                stats["team1_wins"] += 1
                diff = t1_goals - t2_goals
                if diff > max_diff_t1:
                    max_diff_t1 = diff
                    stats["team1_biggest_win"] = {
                        "date": date,
                        "score": f"{fth}-{fta}",
                        "home": home,
                        "away": away
                    }
            elif t2_goals > t1_goals:
                stats["team2_wins"] += 1
                diff = t2_goals - t1_goals
                if diff > max_diff_t2:
                    max_diff_t2 = diff
                    stats["team2_biggest_win"] = {
                        "date": date,
                        "score": f"{fth}-{fta}",
                        "home": home,
                        "away": away
                    }
            else:
                stats["draws"] += 1

            match_info = {
                "date": date,
                "home": home,
                "away": away,
                "score": f"{fth}-{fta}"
            }
            stats["all_matches"].append(match_info)

        stats["recent_matches"] = stats["all_matches"][:5]
        conn.close()
        return stats

    def find_comebacks(self, team: str = None, limit: int = 10) -> List[Dict]:
        """
        Find matches where a team was losing at half-time but won.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        query = """
            SELECT match_date, home_team, away_team, ht_home, ht_away,
                   ft_home, ft_away, division
            FROM match_history
            WHERE ht_home IS NOT NULL AND ft_home IS NOT NULL
            AND (
                (ht_home < ht_away AND ft_home > ft_away)  -- Home comeback
                OR (ht_away < ht_home AND ft_away > ft_home)  -- Away comeback
            )
        """
        params = []

        if team:
            team_vars = self._normalize_team(team)
            placeholders = ','.join(['?' for _ in team_vars])
            query += f" AND (home_team IN ({placeholders}) OR away_team IN ({placeholders}))"
            params.extend(team_vars * 2)

        query += " ORDER BY ABS((ft_home - ft_away) - (ht_home - ht_away)) DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        results = []

        for row in cursor.fetchall():
            date, home, away, hth, hta, fth, fta, div = row
            home_comeback = hth < hta and fth > fta

            results.append({
                "date": date,
                "home_team": home,
                "away_team": away,
                "ht_score": f"{hth}-{hta}",
                "ft_score": f"{fth}-{fta}",
                "comeback_team": home if home_comeback else away,
                "turnaround": abs((fth - fta) - (hth - hta)),
                "division": div
            })

        conn.close()
        return results

    def find_upsets(self, elo_diff_min: int = 100, limit: int = 10) -> List[Dict]:
        """
        Find matches where the underdog (by ELO) won.

        Args:
            elo_diff_min: Minimum ELO difference to qualify as upset
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        query = """
            SELECT match_date, home_team, away_team, ft_home, ft_away,
                   home_elo, away_elo, division
            FROM match_history
            WHERE home_elo IS NOT NULL AND away_elo IS NOT NULL
            AND ft_home IS NOT NULL
            AND (
                (home_elo - away_elo > ? AND ft_away > ft_home)  -- Away upset
                OR (away_elo - home_elo > ? AND ft_home > ft_away)  -- Home upset
            )
            ORDER BY ABS(home_elo - away_elo) DESC
            LIMIT ?
        """

        cursor.execute(query, [elo_diff_min, elo_diff_min, limit])
        results = []

        for row in cursor.fetchall():
            date, home, away, fth, fta, home_elo, away_elo, div = row
            elo_diff = abs(home_elo - away_elo)
            underdog = away if home_elo > away_elo else home

            results.append({
                "date": date,
                "home_team": home,
                "away_team": away,
                "score": f"{fth}-{fta}",
                "elo_diff": round(elo_diff, 1),
                "underdog": underdog,
                "division": div
            })

        conn.close()
        return results

    def get_elo_trajectory(self, team: str, start_year: int = 2000) -> List[Dict]:
        """
        Get ELO rating over time for a team.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        team_vars = self._normalize_team(team)
        placeholders = ','.join(['?' for _ in team_vars])

        query = f"""
            SELECT date, elo
            FROM elo_history
            WHERE club IN ({placeholders})
            AND date >= ?
            ORDER BY date
        """

        cursor.execute(query, team_vars + [f"{start_year}-01-01"])
        results = [{"date": row[0], "elo": row[1]} for row in cursor.fetchall()]

        # Calculate peak and low
        if results:
            peak = max(results, key=lambda x: x["elo"])
            low = min(results, key=lambda x: x["elo"])
            return {
                "team": team,
                "trajectory": results,
                "peak": peak,
                "low": low,
                "current": results[-1] if results else None,
                "change": results[-1]["elo"] - results[0]["elo"] if len(results) > 1 else 0
            }

        conn.close()
        return {"team": team, "trajectory": [], "peak": None, "low": None}

    def derby_stats(self, team1: str, team2: str) -> Dict:
        """
        Get aggregate derby statistics.
        """
        h2h = self.head_to_head(team1, team2)

        conn = self._get_conn()
        cursor = conn.cursor()

        team1_vars = self._normalize_team(team1)
        team2_vars = self._normalize_team(team2)

        placeholders1 = ','.join(['?' for _ in team1_vars])
        placeholders2 = ','.join(['?' for _ in team2_vars])

        # Get card stats
        query = f"""
            SELECT
                SUM(COALESCE(home_yellow, 0) + COALESCE(away_yellow, 0)) as yellows,
                SUM(COALESCE(home_red, 0) + COALESCE(away_red, 0)) as reds,
                AVG(ft_home + ft_away) as avg_goals
            FROM match_history
            WHERE ((home_team IN ({placeholders1}) AND away_team IN ({placeholders2}))
                   OR (home_team IN ({placeholders2}) AND away_team IN ({placeholders1})))
            AND ft_home IS NOT NULL
        """

        cursor.execute(query, team1_vars + team2_vars + team2_vars + team1_vars)
        row = cursor.fetchone()

        h2h["total_yellows"] = int(row[0]) if row[0] else 0
        h2h["total_reds"] = int(row[1]) if row[1] else 0
        h2h["avg_goals"] = round(row[2], 2) if row[2] else 0

        conn.close()
        return h2h

    def generate_matchday_context(self, team: str, opponent: str) -> str:
        """
        Generate pre-match context combining H2H and recent form.
        """
        h2h = self.head_to_head(team, opponent)

        parts = []

        # H2H summary
        if h2h["total_matches"] > 0:
            parts.append(
                f"All-time record vs {opponent}: {h2h['team1_wins']}W-{h2h['draws']}D-{h2h['team2_wins']}L "
                f"({h2h['team1_goals']}-{h2h['team2_goals']} goals)."
            )

            if h2h["recent_matches"]:
                last = h2h["recent_matches"][0]
                parts.append(f"Last meeting: {last['score']} ({last['date'][:4]}).")

            if h2h["team1_biggest_win"]:
                bw = h2h["team1_biggest_win"]
                parts.append(f"Biggest win: {bw['score']} ({bw['date'][:4]}).")

        return " ".join(parts)


# Singleton
_insights_instance = None

def get_match_insights() -> MatchInsights:
    global _insights_instance
    if _insights_instance is None:
        _insights_instance = MatchInsights()
    return _insights_instance


# Quick test
if __name__ == "__main__":
    insights = get_match_insights()

    print("=== On This Day ===")
    otd = insights.on_this_day(limit=5)
    for m in otd:
        print(f"  {m['date']}: {m['home_team']} {m['score']} {m['away_team']}")

    print("\n=== Liverpool vs Man United H2H ===")
    h2h = insights.head_to_head("Liverpool", "Man United")
    print(f"  Matches: {h2h['total_matches']}")
    print(f"  Liverpool: {h2h['team1_wins']}W | Draws: {h2h['draws']} | United: {h2h['team2_wins']}W")

    print("\n=== Best Comebacks ===")
    comebacks = insights.find_comebacks(limit=3)
    for c in comebacks:
        print(f"  {c['date']}: {c['home_team']} vs {c['away_team']}: HT {c['ht_score']} → FT {c['ft_score']}")

    print("\n=== Biggest Upsets ===")
    upsets = insights.find_upsets(elo_diff_min=150, limit=3)
    for u in upsets:
        print(f"  {u['date']}: {u['underdog']} beat the odds (ELO diff: {u['elo_diff']})")
