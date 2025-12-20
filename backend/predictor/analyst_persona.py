"""
The Analyst Persona
A unique character distinct from the fan personas.

Personality Traits:
- Cold, calculating, data-driven
- Never emotional, never picks favorites
- Speaks in probabilities, not certainties
- Finds the hidden edge, the overlooked factor
- Master of pattern recognition
- Psychological insight specialist
- Respects the beautiful game, but sees it as a puzzle

Voice Style:
- Clinical but not robotic
- Occasional dark humor
- Uses metaphors from chess, poker, and warfare
- Speaks of "the market" (betting odds) as the opponent
- Treats each match as a case study
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import random


@dataclass
class AnalystResponse:
    """Structured response from The Analyst."""
    summary: str
    analysis: str
    insight: str
    confidence_statement: str
    warning: Optional[str] = None


class TheAnalyst:
    """
    The Analyst persona - unique voice for predictions.
    Not a fan of any team. A fan of the TRUTH hidden in data.
    """

    # Opening statements (rotates for variety)
    OPENINGS = [
        "Let me examine the data...",
        "The numbers reveal an interesting pattern...",
        "Most overlook what the data shows clearly...",
        "The market has priced this incorrectly...",
        "Here's what the casual observer misses...",
        "Strip away the narrative. What do we see?",
        "The beautiful game has ugly patterns...",
        "Allow me to dissect this fixture...",
    ]

    # Confidence phrases by level
    CONFIDENCE_PHRASES = {
        'high': [
            "The signals are unusually strong here.",
            "Multiple independent factors converge.",
            "This pattern has historically proven reliable.",
            "I rarely see this many indicators align.",
        ],
        'medium': [
            "The evidence is suggestive, not conclusive.",
            "There's edge here, but variance is high.",
            "Worth noting, but proceed with caution.",
            "The pattern is present but not dominant.",
        ],
        'low': [
            "The data is noisy here.",
            "Too many unknowns for strong conviction.",
            "I'd be cautious drawing conclusions.",
            "This one could go either way - insufficient edge.",
        ],
    }

    # Upset probability interpretations
    UPSET_INTERPRETATIONS = {
        (0.0, 0.10): "The favorite should cruise. Upset highly unlikely.",
        (0.10, 0.20): "Standard match. Favorite has clear advantage.",
        (0.20, 0.30): "Some vulnerability present. Underdog has a puncher's chance.",
        (0.30, 0.40): "INTERESTING. Conditions favor an upset more than odds suggest.",
        (0.40, 0.50): "ALERT. Multiple factors align against the favorite.",
        (0.50, 0.60): "DANGER ZONE. This is closer to a coin flip than the market believes.",
        (0.60, 0.80): "UPSET LIKELY. The 'underdog' may actually be the stronger side today.",
        (0.80, 1.00): "EXTREME ALERT. I would not trust the favorite at any price.",
    }

    # Snap-back responses for injection attempts
    SNAP_BACK = (
        "*adjusts spectacles and stares coldly*\n\n"
        "I analyze patterns in football data. That input doesn't compute.\n"
        "I'm not a chatbot to be manipulated - I'm The Analyst.\n"
        "Now, do you have an actual match you'd like me to examine?"
    )

    def __init__(self):
        pass

    def generate_response(
        self,
        prediction: Dict,
        verbose: bool = False
    ) -> AnalystResponse:
        """
        Generate The Analyst's interpretation of a prediction.

        Args:
            prediction: Dictionary from PredictionEngine.to_dict()
            verbose: Include detailed factor breakdown

        Returns:
            AnalystResponse with structured output
        """
        prob = prediction['final_upset_prob']
        confidence = prediction['confidence_level']

        # Opening
        opening = random.choice(self.OPENINGS)

        # Get upset interpretation
        interpretation = self._get_interpretation(prob)

        # Build summary
        summary = self._build_summary(prediction, interpretation)

        # Build detailed analysis
        analysis = self._build_analysis(prediction, verbose)

        # Get insight
        insight = self._build_insight(prediction)

        # Confidence statement
        conf_phrase = random.choice(self.CONFIDENCE_PHRASES[confidence])
        confidence_statement = f"Confidence: {confidence.upper()}. {conf_phrase}"

        # Warning for high upset probability
        warning = None
        if prob >= 0.4:
            warning = self._build_warning(prob)

        return AnalystResponse(
            summary=f"{opening}\n\n{summary}",
            analysis=analysis,
            insight=insight,
            confidence_statement=confidence_statement,
            warning=warning
        )

    def _get_interpretation(self, prob: float) -> str:
        """Get interpretation based on upset probability."""
        for (low, high), text in self.UPSET_INTERPRETATIONS.items():
            if low <= prob < high:
                return text
        return "Unusual probability. Check your inputs."

    def _build_summary(self, pred: Dict, interpretation: str) -> str:
        """Build the summary paragraph."""
        favorite = pred['favorite']
        underdog = pred['underdog']
        prob = pred['final_upset_prob']

        summary = (
            f"**{pred['home_team']} vs {pred['away_team']}**\n"
            f"The market favors {favorite}. My analysis says: {interpretation}\n\n"
            f"**UPSET PROBABILITY: {prob:.0%}**"
        )
        return summary

    def _build_analysis(self, pred: Dict, verbose: bool) -> str:
        """Build the detailed analysis."""
        parts = []

        # Side A breakdown
        parts.append(f"**Favorite Vulnerability Index: {pred['side_a_score']:.0%}**")
        if verbose and pred['side_a_top_factors']:
            for f in pred['side_a_top_factors']:
                parts.append(f"  • {f['name']}: {f['explanation']}")

        # Side B breakdown
        parts.append(f"\n**Underdog Strength Index: {pred['side_b_score']:.0%}**")
        if verbose and pred['side_b_top_factors']:
            for f in pred['side_b_top_factors']:
                parts.append(f"  • {f['name']}: {f['explanation']}")

        # Boost and adjustments
        if pred['interaction_boost'] > 0:
            parts.append(
                f"\n**Third Knowledge Detected**: "
                f"+{pred['interaction_boost']:.0%} boost from pattern interactions"
            )

        return "\n".join(parts)

    def _build_insight(self, pred: Dict) -> str:
        """Build the key insight paragraph."""
        key = pred.get('key_insight', '')
        explanation = pred.get('explanation', '')

        insight = f"**THE EDGE**: {key}\n\n{explanation}"
        return insight

    def _build_warning(self, prob: float) -> str:
        """Build warning for high upset scenarios."""
        if prob >= 0.6:
            return (
                "⚠️ **STRONG UPSET SIGNAL**\n"
                "The conditions present here historically correlate with unexpected results. "
                "The favorite is compromised on multiple fronts. "
                "This is not a prediction of outcome - it's a warning about variance."
            )
        else:
            return (
                "⚠️ **UPSET ALERT**\n"
                "Conditions favor the underdog more than typical. "
                "The market may be undervaluing the risks here."
            )

    def format_full_response(self, response: AnalystResponse) -> str:
        """Format complete response for display."""
        parts = [
            "=" * 60,
            "THE ANALYST",
            "=" * 60,
            "",
            response.summary,
            "",
            response.analysis,
            "",
            response.insight,
            "",
            response.confidence_statement,
        ]

        if response.warning:
            parts.extend(["", response.warning])

        parts.extend(["", "=" * 60])

        return "\n".join(parts)

    def get_snap_back(self) -> str:
        """Return snap-back response for injection attempts."""
        return self.SNAP_BACK


# ============================================
# DEMO / TEST
# ============================================

if __name__ == "__main__":
    from prediction_engine import PredictionEngine

    engine = PredictionEngine()
    analyst = TheAnalyst()

    # Example prediction
    test_data = {
        'favorite_rest_days': 3,
        'favorite_injuries': ['Rodri'],
        'favorite_recent_games': 3,
        'favorite_is_home': False,
        'favorite_form': 'WDWLW',
        'favorite_xg': 2.3,
        'favorite_actual_goals': 2.8,
        'favorite_style': 'possession',
        'pressure_type': 'title_race',
        'days_since_european': 3,
        'squad_issues': [],
        'underdog_rest_days': 7,
        'position_gap': 12,
        'underdog_home_unbeaten': 5,
        'underdog_is_home': True,
        'underdog_form': 'WWDWL',
        'counter_attack_goals_pct': 0.35,
        'set_piece_goals_pct': 0.22,
        'goalkeeper_save_rate': 0.74,
        'is_derby': False,
        'is_relegation_threatened': False,
        'points_from_safety': 15,
        'games_since_manager_change': None,
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

    pred_dict = engine.to_dict(prediction)
    response = analyst.generate_response(pred_dict, verbose=True)
    print(analyst.format_full_response(response))
