"""
Side B Calculator: Underdog Strength Analysis
What conditions give the underdog an edge?

Simplified start: 10 key factors
- B01: Nothing to lose (freedom)
- B02: Home fortress
- B03: Rest advantage
- B04: Hot streak
- B05: Counter-attack threat
- B06: Set-piece danger
- B07: Goalkeeper form
- B08: Derby motivation
- B09: Survival fight
- B10: New manager bounce
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class FactorResult:
    """Result of analyzing a single factor."""
    code: str
    name: str
    value: float  # 0.0 to 1.0 (higher = more strength)
    raw_value: str  # Original measurement
    explanation: str
    weight: float = 1.0


class SideBCalculator:
    """
    Analyzes what gives the underdog an edge.
    Each factor returns 0.0 (no advantage) to 1.0 (maximum advantage).
    """

    def __init__(self):
        # Factor weights (learned over time, start equal)
        self.weights = {
            'B01': 1.3,   # Nothing to lose - high impact
            'B02': 1.4,   # Home fortress - very high
            'B03': 1.1,   # Rest advantage
            'B04': 1.2,   # Hot streak
            'B05': 1.3,   # Counter-attack threat
            'B06': 1.0,   # Set-piece danger
            'B07': 1.1,   # Goalkeeper form
            'B08': 1.5,   # Derby motivation - very high
            'B09': 1.4,   # Survival fight
            'B10': 1.2,   # New manager bounce
        }

    def analyze(
        self,
        underdog_team: str,
        favorite_team: str,
        match_date: str,
        match_data: Dict
    ) -> List[FactorResult]:
        """
        Analyze all Side B factors for the underdog.

        Args:
            underdog_team: Name of the underdog
            favorite_team: Name of the favorite
            match_date: Date of match (YYYY-MM-DD)
            match_data: Dict with relevant data:
                - position_gap: int (table positions difference)
                - underdog_home_unbeaten: int (home unbeaten streak)
                - underdog_rest_days: int
                - favorite_rest_days: int
                - underdog_form: str (e.g., 'WWWLW')
                - counter_attack_goals_pct: float (0.0 to 1.0)
                - set_piece_goals_pct: float (0.0 to 1.0)
                - goalkeeper_save_rate: float (0.0 to 1.0)
                - is_derby: bool
                - is_relegation_threatened: bool
                - games_since_manager_change: int (or None)

        Returns:
            List of FactorResult for each analyzed factor
        """
        results = []

        # B01: Nothing to lose
        results.append(self._analyze_nothing_to_lose(match_data))

        # B02: Home fortress
        results.append(self._analyze_home_fortress(match_data))

        # B03: Rest advantage
        results.append(self._analyze_rest_advantage(match_data))

        # B04: Hot streak
        results.append(self._analyze_hot_streak(match_data))

        # B05: Counter-attack threat
        results.append(self._analyze_counter_attack(match_data))

        # B06: Set-piece danger
        results.append(self._analyze_set_pieces(match_data))

        # B07: Goalkeeper form
        results.append(self._analyze_goalkeeper(match_data))

        # B08: Derby motivation
        results.append(self._analyze_derby(match_data))

        # B09: Survival fight
        results.append(self._analyze_survival_fight(match_data))

        # B10: New manager bounce
        results.append(self._analyze_new_manager(match_data))

        return results

    def _analyze_nothing_to_lose(self, data: Dict) -> FactorResult:
        """B01: Large position gap creates freedom to attack."""
        gap = data.get('position_gap', 0)

        if gap <= 3:
            value = 0.0
            explanation = "Close in table - similar pressure"
        elif gap <= 5:
            value = 0.2
            explanation = f"Moderate gap ({gap} places) - some freedom"
        elif gap <= 8:
            value = 0.4
            explanation = f"Significant gap ({gap} places) - playing free"
        elif gap <= 12:
            value = 0.6
            explanation = f"Large gap ({gap} places) - nothing to lose mentality"
        else:
            value = 0.8
            explanation = f"Massive gap ({gap} places) - complete freedom"

        return FactorResult(
            code='B01',
            name='Nothing to lose',
            value=value,
            raw_value=str(gap),
            explanation=explanation,
            weight=self.weights['B01']
        )

    def _analyze_home_fortress(self, data: Dict) -> FactorResult:
        """B02: Strong home record."""
        unbeaten = data.get('underdog_home_unbeaten', 0)
        is_home = data.get('underdog_is_home', True)

        if not is_home:
            value = 0.0
            explanation = "Playing away - no home fortress"
        elif unbeaten == 0:
            value = 0.0
            explanation = "Lost recently at home"
        elif unbeaten <= 2:
            value = 0.2
            explanation = f"Unbeaten {unbeaten} home games"
        elif unbeaten <= 4:
            value = 0.4
            explanation = f"Good home form - {unbeaten} unbeaten"
        elif unbeaten <= 6:
            value = 0.6
            explanation = f"Strong home fortress - {unbeaten} unbeaten"
        else:
            value = 0.8
            explanation = f"Intimidating home record - {unbeaten} unbeaten"

        return FactorResult(
            code='B02',
            name='Home fortress',
            value=value,
            raw_value=str(unbeaten),
            explanation=explanation,
            weight=self.weights['B02']
        )

    def _analyze_rest_advantage(self, data: Dict) -> FactorResult:
        """B03: More rest than opponent."""
        und_rest = data.get('underdog_rest_days', 7)
        fav_rest = data.get('favorite_rest_days', 7)
        diff = und_rest - fav_rest

        if diff <= 0:
            value = 0.0
            explanation = "No rest advantage"
        elif diff == 1:
            value = 0.2
            explanation = f"1 day more rest ({und_rest} vs {fav_rest})"
        elif diff == 2:
            value = 0.4
            explanation = f"2 days more rest ({und_rest} vs {fav_rest})"
        elif diff == 3:
            value = 0.6
            explanation = f"3 days more rest ({und_rest} vs {fav_rest})"
        else:
            value = 0.8
            explanation = f"Major rest advantage ({und_rest} vs {fav_rest})"

        return FactorResult(
            code='B03',
            name='Rest advantage',
            value=value,
            raw_value=f"{und_rest} vs {fav_rest} days",
            explanation=explanation,
            weight=self.weights['B03']
        )

    def _analyze_hot_streak(self, data: Dict) -> FactorResult:
        """B04: Recent winning momentum."""
        form = data.get('underdog_form', 'LLLLL')
        wins = form.count('W')
        recent_3 = form[-3:] if len(form) >= 3 else form

        if wins >= 4:
            value = 0.8
            explanation = f"On fire! {wins} wins in last 5: {form}"
        elif wins == 3:
            value = 0.6
            explanation = f"Hot streak - {wins} wins: {form}"
        elif recent_3.count('W') >= 2:
            value = 0.4
            explanation = f"Recent momentum - {form}"
        elif wins >= 2:
            value = 0.3
            explanation = f"Moderate form - {form}"
        else:
            value = 0.0
            explanation = f"Poor form - {form}"

        return FactorResult(
            code='B04',
            name='Hot streak',
            value=value,
            raw_value=form,
            explanation=explanation,
            weight=self.weights['B04']
        )

    def _analyze_counter_attack(self, data: Dict) -> FactorResult:
        """B05: Effective on the counter."""
        counter_pct = data.get('counter_attack_goals_pct', 0.0)

        if counter_pct < 0.15:
            value = 0.0
            explanation = f"Weak counter-attack ({counter_pct:.0%} goals)"
        elif counter_pct < 0.25:
            value = 0.3
            explanation = f"Average counter-attack ({counter_pct:.0%} goals)"
        elif counter_pct < 0.35:
            value = 0.5
            explanation = f"Good counter-attack threat ({counter_pct:.0%} goals)"
        elif counter_pct < 0.45:
            value = 0.7
            explanation = f"Dangerous on counter ({counter_pct:.0%} goals)"
        else:
            value = 0.9
            explanation = f"Elite counter-attacking ({counter_pct:.0%} goals)"

        return FactorResult(
            code='B05',
            name='Counter-attack threat',
            value=value,
            raw_value=f"{counter_pct:.1%}",
            explanation=explanation,
            weight=self.weights['B05']
        )

    def _analyze_set_pieces(self, data: Dict) -> FactorResult:
        """B06: Set-piece threat (equalizer potential)."""
        set_piece_pct = data.get('set_piece_goals_pct', 0.0)

        if set_piece_pct < 0.15:
            value = 0.0
            explanation = f"Weak set-pieces ({set_piece_pct:.0%} goals)"
        elif set_piece_pct < 0.25:
            value = 0.3
            explanation = f"Average set-pieces ({set_piece_pct:.0%} goals)"
        elif set_piece_pct < 0.35:
            value = 0.5
            explanation = f"Good set-piece threat ({set_piece_pct:.0%} goals)"
        else:
            value = 0.7
            explanation = f"Dangerous set-pieces ({set_piece_pct:.0%} goals)"

        return FactorResult(
            code='B06',
            name='Set-piece danger',
            value=value,
            raw_value=f"{set_piece_pct:.1%}",
            explanation=explanation,
            weight=self.weights['B06']
        )

    def _analyze_goalkeeper(self, data: Dict) -> FactorResult:
        """B07: Goalkeeper in top form."""
        save_rate = data.get('goalkeeper_save_rate', 0.65)

        if save_rate < 0.65:
            value = 0.0
            explanation = f"Goalkeeper struggling ({save_rate:.0%} saves)"
        elif save_rate < 0.70:
            value = 0.2
            explanation = f"Average goalkeeper form ({save_rate:.0%} saves)"
        elif save_rate < 0.75:
            value = 0.4
            explanation = f"Good goalkeeper form ({save_rate:.0%} saves)"
        elif save_rate < 0.80:
            value = 0.6
            explanation = f"Excellent goalkeeper ({save_rate:.0%} saves)"
        else:
            value = 0.8
            explanation = f"Goalkeeper on fire! ({save_rate:.0%} saves)"

        return FactorResult(
            code='B07',
            name='Goalkeeper form',
            value=value,
            raw_value=f"{save_rate:.1%}",
            explanation=explanation,
            weight=self.weights['B07']
        )

    def _analyze_derby(self, data: Dict) -> FactorResult:
        """B08: Local derby extra motivation."""
        is_derby = data.get('is_derby', False)
        rivalry_intensity = data.get('rivalry_intensity', 'normal')

        if not is_derby:
            value = 0.0
            explanation = "Not a derby match"
        elif rivalry_intensity == 'fierce':
            value = 0.8
            explanation = "Fierce local derby - anything can happen!"
        elif rivalry_intensity == 'strong':
            value = 0.6
            explanation = "Strong rivalry - extra motivation"
        else:
            value = 0.4
            explanation = "Derby match - extra edge"

        return FactorResult(
            code='B08',
            name='Derby motivation',
            value=value,
            raw_value='derby' if is_derby else 'normal',
            explanation=explanation,
            weight=self.weights['B08']
        )

    def _analyze_survival_fight(self, data: Dict) -> FactorResult:
        """B09: Relegation desperation."""
        is_threatened = data.get('is_relegation_threatened', False)
        points_from_safety = data.get('points_from_safety', 10)

        if not is_threatened:
            value = 0.0
            explanation = "Not in relegation danger"
        elif points_from_safety <= 0:
            value = 0.8
            explanation = f"In relegation zone - fighting for survival!"
        elif points_from_safety <= 2:
            value = 0.6
            explanation = f"Just above drop ({points_from_safety} pts clear)"
        elif points_from_safety <= 4:
            value = 0.4
            explanation = f"Relegation threatened ({points_from_safety} pts clear)"
        else:
            value = 0.2
            explanation = "Minor relegation concern"

        return FactorResult(
            code='B09',
            name='Survival fight',
            value=value,
            raw_value=str(points_from_safety),
            explanation=explanation,
            weight=self.weights['B09']
        )

    def _analyze_new_manager(self, data: Dict) -> FactorResult:
        """B10: New manager bounce effect."""
        games_since = data.get('games_since_manager_change')

        if games_since is None:
            value = 0.0
            explanation = "No recent manager change"
        elif games_since <= 2:
            value = 0.7
            explanation = f"New manager bounce! Only {games_since} games in"
        elif games_since <= 4:
            value = 0.5
            explanation = f"New manager effect ({games_since} games)"
        elif games_since <= 6:
            value = 0.3
            explanation = f"Manager settling in ({games_since} games)"
        else:
            value = 0.0
            explanation = "Manager bounce worn off"

        return FactorResult(
            code='B10',
            name='New manager bounce',
            value=value,
            raw_value=str(games_since) if games_since else 'N/A',
            explanation=explanation,
            weight=self.weights['B10']
        )

    def aggregate_score(self, results: List[FactorResult]) -> Tuple[float, List[Dict]]:
        """
        Calculate aggregate underdog strength score.

        Returns:
            (aggregate_score, top_factors)
            - aggregate_score: 0.0 to 1.0 (higher = stronger upset potential)
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
