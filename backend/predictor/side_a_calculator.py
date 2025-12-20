"""
Side A Calculator: Favorite Weakness Analysis
What conditions make the favorite vulnerable to upset?

Simplified start: 10 key factors
- A01: Rest disadvantage
- A02: Key player missing
- A03: Fixture congestion
- A04: Away from home
- A05: Bad recent form
- A06: Overperforming xG (regression due)
- A07: Weather disadvantage
- A08: Pressure situation
- A09: Post-European hangover
- A10: Squad disruption
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class FactorResult:
    """Result of analyzing a single factor."""
    code: str
    name: str
    value: float  # 0.0 to 1.0 (higher = more weakness)
    raw_value: str  # Original measurement
    explanation: str
    weight: float = 1.0


class SideACalculator:
    """
    Analyzes what makes the favorite vulnerable.
    Each factor returns 0.0 (no weakness) to 1.0 (maximum weakness).
    """

    def __init__(self):
        # Factor weights (learned over time, start equal)
        self.weights = {
            'A01': 1.2,   # Rest disadvantage - high impact
            'A02': 1.5,   # Key player missing - very high
            'A03': 1.1,   # Fixture congestion
            'A04': 0.8,   # Away from home (already in odds)
            'A05': 1.3,   # Bad form
            'A06': 1.0,   # xG regression
            'A07': 0.7,   # Weather
            'A08': 1.2,   # Pressure situation
            'A09': 1.4,   # European hangover
            'A10': 0.9,   # Squad disruption
        }

    def analyze(
        self,
        favorite_team: str,
        opponent_team: str,
        match_date: str,
        match_data: Dict
    ) -> List[FactorResult]:
        """
        Analyze all Side A factors for the favorite.

        Args:
            favorite_team: Name of the favorite
            opponent_team: Name of the underdog
            match_date: Date of match (YYYY-MM-DD)
            match_data: Dict with relevant data:
                - favorite_rest_days: int
                - opponent_rest_days: int
                - favorite_injuries: List[str] (key players out)
                - favorite_recent_games: int (games in last 8 days)
                - is_home: bool
                - favorite_form: str (e.g., 'WDLLW')
                - favorite_xg: float (expected goals per game)
                - favorite_actual_goals: float (actual goals per game)
                - weather: str ('clear', 'rain', 'wind', etc.)
                - favorite_style: str ('possession', 'counter', etc.)
                - pressure_type: str ('title_race', 'relegation', 'normal')
                - days_since_european: int (or None)
                - squad_issues: List[str] (rumors, disputes)

        Returns:
            List of FactorResult for each analyzed factor
        """
        results = []

        # A01: Rest disadvantage
        results.append(self._analyze_rest_disadvantage(match_data))

        # A02: Key player missing
        results.append(self._analyze_key_players(match_data))

        # A03: Fixture congestion
        results.append(self._analyze_congestion(match_data))

        # A04: Away from home
        results.append(self._analyze_home_away(match_data))

        # A05: Bad recent form
        results.append(self._analyze_form(match_data))

        # A06: Overperforming xG
        results.append(self._analyze_xg_regression(match_data))

        # A07: Weather disadvantage
        results.append(self._analyze_weather(match_data))

        # A08: Pressure situation
        results.append(self._analyze_pressure(match_data))

        # A09: Post-European hangover
        results.append(self._analyze_european_hangover(match_data))

        # A10: Squad disruption
        results.append(self._analyze_squad_disruption(match_data))

        return results

    def _analyze_rest_disadvantage(self, data: Dict) -> FactorResult:
        """A01: Fewer rest days than opponent."""
        fav_rest = data.get('favorite_rest_days', 7)
        opp_rest = data.get('opponent_rest_days', 7)
        diff = opp_rest - fav_rest

        if diff <= 0:
            value = 0.0
            explanation = "No rest disadvantage"
        elif diff == 1:
            value = 0.2
            explanation = f"1 day less rest ({fav_rest} vs {opp_rest})"
        elif diff == 2:
            value = 0.4
            explanation = f"2 days less rest ({fav_rest} vs {opp_rest})"
        elif diff == 3:
            value = 0.6
            explanation = f"3 days less rest ({fav_rest} vs {opp_rest})"
        else:
            value = 0.8
            explanation = f"Severe rest disadvantage ({fav_rest} vs {opp_rest})"

        return FactorResult(
            code='A01',
            name='Rest disadvantage',
            value=value,
            raw_value=f"{fav_rest} vs {opp_rest} days",
            explanation=explanation,
            weight=self.weights['A01']
        )

    def _analyze_key_players(self, data: Dict) -> FactorResult:
        """A02: Key players injured/suspended."""
        injuries = data.get('favorite_injuries', [])
        key_players_out = len(injuries)

        if key_players_out == 0:
            value = 0.0
            explanation = "Full strength squad"
        elif key_players_out == 1:
            value = 0.4
            explanation = f"Missing key player: {injuries[0]}"
        elif key_players_out == 2:
            value = 0.6
            explanation = f"Missing 2 key players: {', '.join(injuries[:2])}"
        else:
            value = 0.8
            explanation = f"Major injury crisis: {key_players_out} key players out"

        return FactorResult(
            code='A02',
            name='Key player missing',
            value=value,
            raw_value=str(key_players_out),
            explanation=explanation,
            weight=self.weights['A02']
        )

    def _analyze_congestion(self, data: Dict) -> FactorResult:
        """A03: Too many games in short period."""
        recent_games = data.get('favorite_recent_games', 1)

        if recent_games <= 1:
            value = 0.0
            explanation = "Normal schedule"
        elif recent_games == 2:
            value = 0.3
            explanation = "2 games in 8 days"
        elif recent_games == 3:
            value = 0.6
            explanation = "3 games in 8 days - congestion"
        else:
            value = 0.9
            explanation = f"{recent_games} games in 8 days - severe congestion"

        return FactorResult(
            code='A03',
            name='Fixture congestion',
            value=value,
            raw_value=str(recent_games),
            explanation=explanation,
            weight=self.weights['A03']
        )

    def _analyze_home_away(self, data: Dict) -> FactorResult:
        """A04: Playing away reduces advantage."""
        is_home = data.get('is_home', True)

        if is_home:
            value = 0.0
            explanation = "Playing at home"
        else:
            value = 0.3  # Small factor (already in odds)
            explanation = "Playing away - reduced home advantage"

        return FactorResult(
            code='A04',
            name='Away from home',
            value=value,
            raw_value='home' if is_home else 'away',
            explanation=explanation,
            weight=self.weights['A04']
        )

    def _analyze_form(self, data: Dict) -> FactorResult:
        """A05: Recent poor results."""
        form = data.get('favorite_form', 'WWWWW')
        losses = form.count('L')
        draws = form.count('D')

        if losses == 0 and draws <= 1:
            value = 0.0
            explanation = f"Excellent form: {form}"
        elif losses == 1:
            value = 0.2
            explanation = f"Good form with 1 loss: {form}"
        elif losses == 2:
            value = 0.5
            explanation = f"Inconsistent form: {form}"
        elif losses >= 3:
            value = 0.8
            explanation = f"Poor form with {losses} losses: {form}"
        else:
            value = 0.3
            explanation = f"Mixed form: {form}"

        return FactorResult(
            code='A05',
            name='Bad recent form',
            value=value,
            raw_value=form,
            explanation=explanation,
            weight=self.weights['A05']
        )

    def _analyze_xg_regression(self, data: Dict) -> FactorResult:
        """A06: Scoring above expected goals (regression due)."""
        xg = data.get('favorite_xg', 1.5)
        actual = data.get('favorite_actual_goals', 1.5)

        if xg == 0:
            value = 0.0
            explanation = "No xG data available"
        else:
            overperformance = (actual - xg) / xg

            if overperformance <= 0:
                value = 0.0
                explanation = "Scoring at or below xG"
            elif overperformance < 0.1:
                value = 0.1
                explanation = f"Slightly above xG (+{overperformance:.0%})"
            elif overperformance < 0.2:
                value = 0.3
                explanation = f"Overperforming xG (+{overperformance:.0%})"
            elif overperformance < 0.3:
                value = 0.5
                explanation = f"Significantly above xG (+{overperformance:.0%}) - regression likely"
            else:
                value = 0.7
                explanation = f"Massively overperforming (+{overperformance:.0%}) - regression due"

        return FactorResult(
            code='A06',
            name='Overperforming xG',
            value=value,
            raw_value=f"xG: {xg:.2f}, Actual: {actual:.2f}",
            explanation=explanation,
            weight=self.weights['A06']
        )

    def _analyze_weather(self, data: Dict) -> FactorResult:
        """A07: Weather conditions favor opponent's style."""
        weather = data.get('weather', 'clear').lower()
        fav_style = data.get('favorite_style', 'possession').lower()

        # Possession teams struggle in bad weather
        if weather in ['rain', 'heavy_rain', 'wind', 'storm']:
            if fav_style in ['possession', 'tiki-taka']:
                value = 0.5
                explanation = f"{weather.title()} conditions hurt possession style"
            else:
                value = 0.1
                explanation = f"{weather.title()} conditions - minimal impact"
        elif weather in ['extreme_heat']:
            value = 0.3
            explanation = "Extreme heat - fatigue factor"
        else:
            value = 0.0
            explanation = "Good conditions"

        return FactorResult(
            code='A07',
            name='Weather disadvantage',
            value=value,
            raw_value=weather,
            explanation=explanation,
            weight=self.weights['A07']
        )

    def _analyze_pressure(self, data: Dict) -> FactorResult:
        """A08: High-pressure situation."""
        pressure = data.get('pressure_type', 'normal').lower()

        if pressure == 'normal':
            value = 0.0
            explanation = "Normal match situation"
        elif pressure == 'must_win':
            value = 0.5
            explanation = "Must-win pressure"
        elif pressure == 'title_race':
            value = 0.4
            explanation = "Title race pressure"
        elif pressure == 'champions_league':
            value = 0.3
            explanation = "Champions League qualification pressure"
        elif pressure == 'relegation':
            value = 0.2  # Often galvanizes teams
            explanation = "Relegation battle - could go either way"
        else:
            value = 0.2
            explanation = f"Pressure situation: {pressure}"

        return FactorResult(
            code='A08',
            name='Pressure situation',
            value=value,
            raw_value=pressure,
            explanation=explanation,
            weight=self.weights['A08']
        )

    def _analyze_european_hangover(self, data: Dict) -> FactorResult:
        """A09: Recent European fixture."""
        days_since = data.get('days_since_european')

        if days_since is None:
            value = 0.0
            explanation = "No European football"
        elif days_since <= 3:
            value = 0.7
            explanation = f"European game just {days_since} days ago"
        elif days_since <= 4:
            value = 0.5
            explanation = f"European game {days_since} days ago"
        elif days_since <= 5:
            value = 0.2
            explanation = f"European game {days_since} days ago - minor impact"
        else:
            value = 0.0
            explanation = "Sufficient recovery from European game"

        return FactorResult(
            code='A09',
            name='Post-European hangover',
            value=value,
            raw_value=str(days_since) if days_since else 'N/A',
            explanation=explanation,
            weight=self.weights['A09']
        )

    def _analyze_squad_disruption(self, data: Dict) -> FactorResult:
        """A10: Internal squad issues."""
        issues = data.get('squad_issues', [])
        issue_count = len(issues)

        if issue_count == 0:
            value = 0.0
            explanation = "No known squad issues"
        elif issue_count == 1:
            value = 0.3
            explanation = f"Squad issue: {issues[0]}"
        elif issue_count == 2:
            value = 0.5
            explanation = f"Multiple issues: {', '.join(issues[:2])}"
        else:
            value = 0.7
            explanation = f"Significant disruption: {issue_count} issues"

        return FactorResult(
            code='A10',
            name='Squad disruption',
            value=value,
            raw_value=str(issue_count),
            explanation=explanation,
            weight=self.weights['A10']
        )

    def aggregate_score(self, results: List[FactorResult]) -> Tuple[float, List[Dict]]:
        """
        Calculate aggregate weakness score.

        Returns:
            (aggregate_score, top_factors)
            - aggregate_score: 0.0 to 1.0 (higher = more vulnerable)
            - top_factors: List of top 3 contributing factors
        """
        if not results:
            return 0.0, []

        # Weighted average
        weighted_sum = sum(r.value * r.weight for r in results)
        total_weight = sum(r.weight for r in results)

        if total_weight == 0:
            return 0.0, []

        aggregate = weighted_sum / total_weight

        # Get top factors
        sorted_factors = sorted(results, key=lambda r: r.value * r.weight, reverse=True)
        top_factors = [
            {
                'code': r.code,
                'name': r.name,
                'value': r.value,
                'explanation': r.explanation
            }
            for r in sorted_factors[:3] if r.value > 0
        ]

        return min(aggregate, 1.0), top_factors
