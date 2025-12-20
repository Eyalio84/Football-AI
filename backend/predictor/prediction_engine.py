"""
Prediction Engine: The Analyst's Core
Combines Side A (favorite weakness) + Side B (underdog strength)
+ Third Knowledge (hidden patterns in the gap)

Philosophy:
"The question isn't who SHOULD win.
 The question is: what would make the SHOULD not happen?"

Output: Not a winner prediction, but an UPSET PROBABILITY with confidence.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import sys
import sqlite3
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from predictor.side_a_calculator import SideACalculator, FactorResult
from predictor.side_b_calculator import SideBCalculator
from predictor.data_ingestion import DataIngestion, STADIUM_LOCATIONS

# Database path
PREDICTOR_DB = Path(__file__).parent.parent / "predictor_facts.db"


@dataclass
class ThirdKnowledge:
    """Hidden pattern discovered between Side A and B."""
    pattern_name: str
    description: str
    factor_a_code: str
    factor_b_code: str
    interaction_type: str  # 'multiplicative', 'threshold', 'synergy'
    multiplier: float
    confidence: float


@dataclass
class Prediction:
    """Complete prediction output."""
    match_id: Optional[int]
    match_date: str
    home_team: str
    away_team: str
    favorite: str
    underdog: str

    # Side A analysis
    side_a_score: float  # 0-1 (favorite weakness)
    side_a_top_factors: List[Dict]

    # Side B analysis
    side_b_score: float  # 0-1 (underdog strength)
    side_b_top_factors: List[Dict]

    # Combined
    naive_upset_prob: float  # Simple A + B combination
    interaction_boost: float  # From third knowledge patterns
    third_knowledge_adj: float  # Gap adjustment
    final_upset_prob: float  # Final prediction

    # Confidence
    confidence_level: str  # 'low', 'medium', 'high'
    confidence_score: float

    # Explanation
    explanation: str
    key_insight: str  # The "hidden" insight

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class PredictionEngine:
    """
    The Analyst's brain.

    Analyzes matches from TWO sides:
    1. Side A: What weakens the favorite?
    2. Side B: What strengthens the underdog?
    3. Third Knowledge: What hidden patterns emerge from A + B?
    """

    def __init__(self, use_live_data: bool = True):
        """
        Initialize the prediction engine.

        Args:
            use_live_data: If True, uses DataIngestion for real-time API data.
                          If False, uses manual match_data input only.
        """
        self.side_a = SideACalculator()
        self.side_b = SideBCalculator()
        self.use_live_data = use_live_data

        # Data ingestion for real-time data (weather, form, odds)
        if use_live_data:
            self.data_ingestion = DataIngestion()
        else:
            self.data_ingestion = None

        # Load patterns from database instead of hardcoded
        self.patterns = self._load_patterns_from_db()

        # Load analyst insights for team-specific adjustments
        self.insights = self._load_analyst_insights()

    def _load_patterns_from_db(self) -> List[ThirdKnowledge]:
        """Load validated Third Knowledge patterns from predictor_facts.db."""
        patterns = []

        if not PREDICTOR_DB.exists():
            print(f"Warning: {PREDICTOR_DB} not found, using empty patterns")
            return patterns

        try:
            conn = sqlite3.connect(PREDICTOR_DB)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT pattern_name, description, factor_a_code, factor_b_code,
                       interaction_type, multiplier, confidence
                FROM third_knowledge_patterns
                WHERE is_validated = 1
                ORDER BY confidence DESC
            """)

            for row in cursor.fetchall():
                patterns.append(ThirdKnowledge(
                    pattern_name=row[0],
                    description=row[1] or "",
                    factor_a_code=row[2],
                    factor_b_code=row[3],
                    interaction_type=row[4] or "multiplicative",
                    multiplier=row[5] or 1.0,
                    confidence=row[6] or 0.5
                ))

            conn.close()
            print(f"Loaded {len(patterns)} validated patterns from database")

        except Exception as e:
            print(f"Error loading patterns from DB: {e}")

        return patterns

    def _load_analyst_insights(self) -> Dict[str, List[Dict]]:
        """
        Load analyst insights from database.

        Returns dict keyed by team name with list of applicable insights.
        Example: {"man_united": [{"title": "Collapse Risk", "confidence": 0.78, ...}]}
        """
        insights = {}

        if not PREDICTOR_DB.exists():
            return insights

        try:
            conn = sqlite3.connect(PREDICTOR_DB)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT title, insight_type, description, confidence, success_rate
                FROM analyst_insights
                WHERE actionable = 1
                ORDER BY confidence DESC
            """)

            for row in cursor.fetchall():
                title = row[0]
                insight = {
                    "title": title,
                    "type": row[1],
                    "description": row[2],
                    "confidence": row[3] or 0.5,
                    "success_rate": row[4] or 0.5
                }

                # Parse team from title (e.g., "Liverpool Anfield Fortress" -> "liverpool")
                team_key = self._extract_team_from_insight(title)
                if team_key:
                    if team_key not in insights:
                        insights[team_key] = []
                    insights[team_key].append(insight)

            conn.close()
            total_insights = sum(len(v) for v in insights.values())
            print(f"Loaded {total_insights} analyst insights for {len(insights)} teams")

        except Exception as e:
            print(f"Error loading analyst insights: {e}")

        return insights

    def _extract_team_from_insight(self, title: str) -> Optional[str]:
        """Extract team name from insight title."""
        title_lower = title.lower()

        # Team name mappings
        team_keys = {
            "liverpool": "liverpool",
            "arsenal": "arsenal",
            "chelsea": "chelsea",
            "man united": "man_united",
            "manchester united": "man_united",
            "man city": "man_city",
            "manchester city": "man_city",
            "tottenham": "tottenham",
            "spurs": "tottenham",
            "newcastle": "newcastle",
            "west ham": "west_ham",
            "everton": "everton",
            "brighton": "brighton",
            "villa": "aston_villa",
            "aston villa": "aston_villa",
            "wolves": "wolves",
            "palace": "crystal_palace",
            "crystal palace": "crystal_palace",
            "fulham": "fulham",
            "forest": "nottingham_forest",
            "nottingham forest": "nottingham_forest",
            "brentford": "brentford",
            "bournemouth": "bournemouth",
            "leicester": "leicester",
        }

        for name, key in team_keys.items():
            if name in title_lower:
                return key

        return None

    def get_team_insights(self, team: str) -> List[Dict]:
        """Get analyst insights for a specific team."""
        team_key = team.lower().replace(" ", "_").replace("-", "_")
        return self.insights.get(team_key, [])

    def _apply_insights_adjustment(
        self,
        team: str,
        is_home: bool,
        is_favorite: bool
    ) -> Tuple[float, List[Dict]]:
        """
        Calculate adjustment from analyst insights.

        Returns (adjustment_value, insights_applied)
        """
        insights = self.get_team_insights(team)
        if not insights:
            return 0.0, []

        adjustment = 0.0
        applied = []

        for insight in insights:
            conf = insight["confidence"]
            title = insight["title"].lower()

            # Apply context-specific adjustments
            if "fortress" in title and is_home:
                # Home fortress - reduces upset probability if this team is favorite
                if is_favorite:
                    adjustment -= 0.05 * conf  # Favorite stronger at home
                else:
                    adjustment += 0.05 * conf  # Underdog has fortress advantage
                applied.append(insight)

            elif "collapse" in title or "fade" in title:
                # Collapse risk - increases upset probability if this team is favorite
                if is_favorite:
                    adjustment += 0.08 * conf
                applied.append(insight)

            elif "counter" in title or "physical" in title:
                # Counter/physical edge - helps underdog
                if not is_favorite:
                    adjustment += 0.05 * conf
                applied.append(insight)

            elif "survival" in title or "desperation" in title:
                # Survival mode - increases underdog fight
                if not is_favorite:
                    adjustment += 0.07 * conf
                applied.append(insight)

            elif "fatigue" in title:
                # Fatigue - weakens the team
                if is_favorite:
                    adjustment += 0.06 * conf
                else:
                    adjustment -= 0.04 * conf
                applied.append(insight)

            elif "underrated" in title:
                # Underrated - adds value
                if not is_favorite:
                    adjustment += 0.04 * conf
                applied.append(insight)

        return min(0.15, adjustment), applied  # Cap at 15% adjustment

    def get_live_match_context(self, home_team: str, away_team: str) -> Optional[Dict]:
        """
        Fetch real-time match context from external APIs.

        Returns weather, form, standings, odds data for both teams.
        """
        if not self.data_ingestion:
            return None

        try:
            return self.data_ingestion.get_match_context(home_team, away_team)
        except Exception as e:
            print(f"Error fetching live match context: {e}")
            return None

    def analyze_match_live(
        self,
        home_team: str,
        away_team: str,
        favorite: str,
        underdog: str,
        match_date: str,
        match_id: Optional[int] = None
    ) -> Prediction:
        """
        Analyze match using LIVE data from external APIs.

        Automatically fetches:
        - Weather at venue (OpenWeatherMap)
        - Current form (Football-Data.org)
        - Betting odds (The Odds API)
        - Travel distance (calculated)

        Falls back to defaults if APIs unavailable.
        """
        # Fetch live context
        live_context = self.get_live_match_context(home_team, away_team)

        if live_context:
            # Build match_data from live context
            match_data = self._build_match_data_from_live(
                live_context, home_team, away_team, favorite, underdog
            )
        else:
            # Fallback to empty data
            print("Warning: No live data available, using defaults")
            match_data = {}

        return self.analyze_match(
            home_team=home_team,
            away_team=away_team,
            favorite=favorite,
            underdog=underdog,
            match_date=match_date,
            match_data=match_data,
            match_id=match_id
        )

    def _build_match_data_from_live(
        self,
        live_context: Dict,
        home_team: str,
        away_team: str,
        favorite: str,
        underdog: str
    ) -> Dict:
        """Convert live API context to match_data format for calculators."""
        match_data = {}

        # Weather data
        weather = live_context.get('weather', {})
        if weather:
            match_data['weather'] = weather.get('condition', 'clear')

        # Determine which team is home/away and favorite/underdog
        favorite_is_home = favorite.lower() == home_team.lower()

        # Form data
        home_form = live_context.get('home_form', {})
        away_form = live_context.get('away_form', {})

        if favorite_is_home:
            fav_form = home_form
            und_form = away_form
            match_data['favorite_is_home'] = True
            match_data['underdog_is_home'] = False
        else:
            fav_form = away_form
            und_form = home_form
            match_data['favorite_is_home'] = False
            match_data['underdog_is_home'] = True

        # Map form to match_data
        if fav_form:
            match_data['favorite_form'] = fav_form.get('form', 'DDDDD')
            match_data['favorite_recent_games'] = len(fav_form.get('form', ''))

        if und_form:
            match_data['underdog_form'] = und_form.get('form', 'DDDDD')

        # Odds data
        odds = live_context.get('odds', {})
        if odds:
            match_data['odds_favorite'] = odds.get('home_odds' if favorite_is_home else 'away_odds', 1.5)
            match_data['odds_underdog'] = odds.get('away_odds' if favorite_is_home else 'home_odds', 4.0)

        # Travel distance
        match_data['travel_distance_km'] = live_context.get('travel_distance_km', 0)

        # Active factors from live context
        active_factors = live_context.get('active_factors', {})
        if active_factors:
            # Map active factors to match_data flags
            if 'A12' in active_factors.get('side_a', []):
                match_data['long_travel'] = True
            if 'B14' in active_factors.get('side_b', []):
                match_data['value_odds'] = True

        return match_data

    def analyze_match(
        self,
        home_team: str,
        away_team: str,
        favorite: str,
        underdog: str,
        match_date: str,
        match_data: Dict,
        match_id: Optional[int] = None
    ) -> Prediction:
        """
        Full two-sided analysis with third knowledge discovery.

        Args:
            home_team: Home team name
            away_team: Away team name
            favorite: Which team is favorite
            underdog: Which team is underdog
            match_date: Date (YYYY-MM-DD)
            match_data: Combined data dict for both calculators
            match_id: Optional database reference

        Returns:
            Complete Prediction object
        """
        # Step 1: Analyze Side A (favorite weakness)
        side_a_results = self.side_a.analyze(
            favorite_team=favorite,
            opponent_team=underdog,
            match_date=match_date,
            match_data=self._extract_favorite_data(match_data)
        )
        side_a_score, side_a_top = self.side_a.aggregate_score(side_a_results)

        # Step 2: Analyze Side B (underdog strength)
        side_b_results = self.side_b.analyze(
            underdog_team=underdog,
            favorite_team=favorite,
            match_date=match_date,
            match_data=self._extract_underdog_data(match_data)
        )
        side_b_score, side_b_top = self.side_b.aggregate_score(side_b_results)

        # Step 3: Calculate naive upset probability
        # Simple combination: average of weakness and strength
        naive_prob = (side_a_score + side_b_score) / 2

        # Step 4: Check for Third Knowledge patterns
        interaction_boost, patterns_found = self._find_third_knowledge(
            side_a_results, side_b_results
        )

        # Step 5: Apply gap adjustment (when both sides strong)
        gap_adj = self._calculate_gap_adjustment(side_a_score, side_b_score)

        # Step 5.5: Apply analyst insights adjustment
        favorite_is_home = home_team.lower() == favorite.lower()
        underdog_is_home = home_team.lower() == underdog.lower()

        fav_insight_adj, fav_insights = self._apply_insights_adjustment(
            favorite, is_home=favorite_is_home, is_favorite=True
        )
        und_insight_adj, und_insights = self._apply_insights_adjustment(
            underdog, is_home=underdog_is_home, is_favorite=False
        )
        insights_adj = fav_insight_adj + und_insight_adj
        insights_applied = fav_insights + und_insights

        # Step 6: Calculate final probability
        final_prob = min(0.95, naive_prob + interaction_boost + gap_adj + insights_adj)

        # Step 7: Determine confidence
        confidence_level, confidence_score = self._calculate_confidence(
            side_a_results, side_b_results, patterns_found
        )

        # Step 8: Generate explanation
        explanation, key_insight = self._generate_explanation(
            side_a_top, side_b_top, patterns_found, final_prob, insights_applied
        )

        return Prediction(
            match_id=match_id,
            match_date=match_date,
            home_team=home_team,
            away_team=away_team,
            favorite=favorite,
            underdog=underdog,
            side_a_score=round(side_a_score, 3),
            side_a_top_factors=side_a_top,
            side_b_score=round(side_b_score, 3),
            side_b_top_factors=side_b_top,
            naive_upset_prob=round(naive_prob, 3),
            interaction_boost=round(interaction_boost, 3),
            third_knowledge_adj=round(gap_adj, 3),
            final_upset_prob=round(final_prob, 3),
            confidence_level=confidence_level,
            confidence_score=round(confidence_score, 3),
            explanation=explanation,
            key_insight=key_insight
        )

    def _extract_favorite_data(self, match_data: Dict) -> Dict:
        """Extract data relevant to favorite analysis."""
        return {
            'favorite_rest_days': match_data.get('favorite_rest_days', 7),
            'opponent_rest_days': match_data.get('underdog_rest_days', 7),
            'favorite_injuries': match_data.get('favorite_injuries', []),
            'favorite_recent_games': match_data.get('favorite_recent_games', 1),
            'is_home': match_data.get('favorite_is_home', True),
            'favorite_form': match_data.get('favorite_form', 'WWWWW'),
            'favorite_xg': match_data.get('favorite_xg', 1.5),
            'favorite_actual_goals': match_data.get('favorite_actual_goals', 1.5),
            'weather': match_data.get('weather', 'clear'),
            'favorite_style': match_data.get('favorite_style', 'possession'),
            'pressure_type': match_data.get('pressure_type', 'normal'),
            'days_since_european': match_data.get('days_since_european'),
            'squad_issues': match_data.get('squad_issues', []),
        }

    def _extract_underdog_data(self, match_data: Dict) -> Dict:
        """Extract data relevant to underdog analysis."""
        return {
            'position_gap': match_data.get('position_gap', 0),
            'underdog_home_unbeaten': match_data.get('underdog_home_unbeaten', 0),
            'underdog_is_home': match_data.get('underdog_is_home', False),
            'underdog_rest_days': match_data.get('underdog_rest_days', 7),
            'favorite_rest_days': match_data.get('favorite_rest_days', 7),
            'underdog_form': match_data.get('underdog_form', 'LLLLL'),
            'counter_attack_goals_pct': match_data.get('counter_attack_goals_pct', 0.15),
            'set_piece_goals_pct': match_data.get('set_piece_goals_pct', 0.15),
            'goalkeeper_save_rate': match_data.get('goalkeeper_save_rate', 0.65),
            'is_derby': match_data.get('is_derby', False),
            'rivalry_intensity': match_data.get('rivalry_intensity', 'normal'),
            'is_relegation_threatened': match_data.get('is_relegation_threatened', False),
            'points_from_safety': match_data.get('points_from_safety', 10),
            'games_since_manager_change': match_data.get('games_since_manager_change'),
        }

    def _find_third_knowledge(
        self,
        side_a_results: List[FactorResult],
        side_b_results: List[FactorResult]
    ) -> Tuple[float, List[ThirdKnowledge]]:
        """
        Look for known interaction patterns between Side A and B.

        Returns:
            (total_boost, patterns_found)
        """
        # Build lookup dicts
        a_factors = {r.code: r for r in side_a_results}
        b_factors = {r.code: r for r in side_b_results}

        patterns_found = []
        total_boost = 0.0

        for pattern in self.patterns:
            a_factor = a_factors.get(pattern.factor_a_code)
            b_factor = b_factors.get(pattern.factor_b_code)

            if not a_factor or not b_factor:
                continue

            # Check if both factors are active (above threshold)
            a_active = a_factor.value >= 0.3
            b_active = b_factor.value >= 0.3

            if a_active and b_active:
                # Pattern detected!
                patterns_found.append(pattern)

                # Calculate boost based on interaction type
                if pattern.interaction_type == 'multiplicative':
                    boost = (a_factor.value * b_factor.value) * (pattern.multiplier - 1)
                elif pattern.interaction_type == 'synergy':
                    boost = ((a_factor.value + b_factor.value) / 2) * (pattern.multiplier - 1)
                else:  # threshold
                    boost = 0.1 * pattern.multiplier

                # Weight by pattern confidence
                boost *= pattern.confidence
                total_boost += boost

        return min(total_boost, 0.25), patterns_found  # Cap at 25% boost

    def _calculate_gap_adjustment(
        self,
        side_a_score: float,
        side_b_score: float
    ) -> float:
        """
        When BOTH sides are strong, there's extra upset potential.
        This is the "gap" - the hidden knowledge between them.
        """
        if side_a_score >= 0.4 and side_b_score >= 0.4:
            # Both sides strong - synergy bonus
            gap = min(side_a_score, side_b_score) * 0.15
            return gap
        elif side_a_score >= 0.5 and side_b_score < 0.2:
            # Favorite very weak but underdog not capitalizing
            return 0.05  # Small adjustment
        elif side_b_score >= 0.5 and side_a_score < 0.2:
            # Underdog very strong but favorite solid
            return 0.05  # Small adjustment
        return 0.0

    def _calculate_confidence(
        self,
        side_a_results: List[FactorResult],
        side_b_results: List[FactorResult],
        patterns_found: List[ThirdKnowledge]
    ) -> Tuple[str, float]:
        """
        Calculate confidence in the prediction.

        Based on:
        - Number of active factors
        - Strength of factors
        - Validated patterns found
        """
        # Count active factors
        a_active = sum(1 for r in side_a_results if r.value >= 0.3)
        b_active = sum(1 for r in side_b_results if r.value >= 0.3)

        # Base confidence from active factors
        active_ratio = (a_active + b_active) / 20  # 20 total factors
        base_confidence = 0.3 + (active_ratio * 0.4)

        # Boost from patterns
        pattern_boost = len(patterns_found) * 0.1

        # Calculate final confidence
        confidence_score = min(0.95, base_confidence + pattern_boost)

        # Determine level
        if confidence_score >= 0.7:
            level = 'high'
        elif confidence_score >= 0.5:
            level = 'medium'
        else:
            level = 'low'

        return level, confidence_score

    def _generate_explanation(
        self,
        side_a_top: List[Dict],
        side_b_top: List[Dict],
        patterns_found: List[ThirdKnowledge],
        final_prob: float,
        insights_applied: List[Dict] = None
    ) -> Tuple[str, str]:
        """
        Generate natural language explanation and key insight.
        """
        # Build explanation
        parts = []

        if side_a_top:
            top_a = side_a_top[0]
            parts.append(f"The favorite shows vulnerability: {top_a['explanation']}")

        if side_b_top:
            top_b = side_b_top[0]
            parts.append(f"The underdog has an edge: {top_b['explanation']}")

        if patterns_found:
            pattern_names = [p.pattern_name for p in patterns_found[:2]]
            parts.append(f"Hidden patterns detected: {', '.join(pattern_names)}")

        if insights_applied:
            insight_titles = [i['title'] for i in insights_applied[:2]]
            parts.append(f"Analyst insights: {', '.join(insight_titles)}")

        explanation = " ".join(parts) if parts else "Limited data for analysis."

        # Generate key insight
        if final_prob >= 0.4:
            key_insight = "HIGH UPSET ALERT: Multiple factors aligning against the favorite."
        elif final_prob >= 0.25:
            key_insight = "UPSET RISK: Conditions favor the underdog more than odds suggest."
        elif final_prob >= 0.15:
            key_insight = "MODERATE RISK: Some factors could cause variance."
        else:
            key_insight = "LOW UPSET RISK: Favorite should handle this."

        return explanation, key_insight

    def to_dict(self, prediction: Prediction) -> Dict:
        """Convert prediction to dictionary for storage/API."""
        return {
            'match_id': prediction.match_id,
            'match_date': prediction.match_date,
            'home_team': prediction.home_team,
            'away_team': prediction.away_team,
            'favorite': prediction.favorite,
            'underdog': prediction.underdog,
            'side_a_score': prediction.side_a_score,
            'side_a_top_factors': prediction.side_a_top_factors,
            'side_b_score': prediction.side_b_score,
            'side_b_top_factors': prediction.side_b_top_factors,
            'naive_upset_prob': prediction.naive_upset_prob,
            'interaction_boost': prediction.interaction_boost,
            'third_knowledge_adj': prediction.third_knowledge_adj,
            'final_upset_prob': prediction.final_upset_prob,
            'confidence_level': prediction.confidence_level,
            'confidence_score': prediction.confidence_score,
            'explanation': prediction.explanation,
            'key_insight': prediction.key_insight,
            'created_at': prediction.created_at,
        }


# ============================================
# DEMO / TEST
# ============================================

if __name__ == "__main__":
    engine = PredictionEngine()

    # Example: Crystal Palace (underdog) vs Manchester City (favorite)
    test_data = {
        # Favorite (Man City) data
        'favorite_rest_days': 3,  # Just played Champions League
        'favorite_injuries': ['Rodri'],  # Key player out
        'favorite_recent_games': 3,  # 3 games in 8 days
        'favorite_is_home': False,  # Away at Selhurst Park
        'favorite_form': 'WDWLW',
        'favorite_xg': 2.3,
        'favorite_actual_goals': 2.8,  # Overperforming
        'favorite_style': 'possession',
        'pressure_type': 'title_race',
        'days_since_european': 3,
        'squad_issues': [],

        # Underdog (Crystal Palace) data
        'underdog_rest_days': 7,
        'position_gap': 12,  # 12 places between them
        'underdog_home_unbeaten': 5,
        'underdog_is_home': True,
        'underdog_form': 'WWDWL',
        'counter_attack_goals_pct': 0.35,  # Good on counter
        'set_piece_goals_pct': 0.22,
        'goalkeeper_save_rate': 0.74,
        'is_derby': False,
        'is_relegation_threatened': False,
        'points_from_safety': 15,
        'games_since_manager_change': None,

        # General
        'weather': 'rain',
    }

    prediction = engine.analyze_match(
        home_team="Crystal Palace",
        away_team="Manchester City",
        favorite="Manchester City",
        underdog="Crystal Palace",
        match_date="2024-12-28",
        match_data=test_data
    )

    print("=" * 60)
    print("THE ANALYST - Match Prediction")
    print("=" * 60)
    print(f"\n{prediction.home_team} vs {prediction.away_team}")
    print(f"Favorite: {prediction.favorite}")
    print(f"Underdog: {prediction.underdog}")
    print()
    print(f"Side A Score (Favorite Weakness): {prediction.side_a_score:.1%}")
    for f in prediction.side_a_top_factors:
        print(f"  - {f['name']}: {f['explanation']}")
    print()
    print(f"Side B Score (Underdog Strength): {prediction.side_b_score:.1%}")
    for f in prediction.side_b_top_factors:
        print(f"  - {f['name']}: {f['explanation']}")
    print()
    print(f"Naive Upset Probability: {prediction.naive_upset_prob:.1%}")
    print(f"Interaction Boost: +{prediction.interaction_boost:.1%}")
    print(f"Gap Adjustment: +{prediction.third_knowledge_adj:.1%}")
    print(f"FINAL UPSET PROBABILITY: {prediction.final_upset_prob:.1%}")
    print()
    print(f"Confidence: {prediction.confidence_level.upper()} ({prediction.confidence_score:.0%})")
    print()
    print(f"KEY INSIGHT: {prediction.key_insight}")
    print()
    print(f"Explanation: {prediction.explanation}")
