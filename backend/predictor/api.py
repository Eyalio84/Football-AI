"""
Predictor API Module
Exposes The Analyst's predictions via API endpoints.
Separate from main chat API - different persona, different database.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from predictor.prediction_engine import PredictionEngine, Prediction
from predictor.analyst_persona import TheAnalyst, AnalystResponse
from predictor.predictor_db import PredictorDB


@dataclass
class PredictionRequest:
    """Request structure for prediction."""
    home_team: str
    away_team: str
    favorite: str
    underdog: str
    match_date: str
    match_data: Dict


@dataclass
class PredictionAPIResponse:
    """API response structure."""
    success: bool
    prediction: Optional[Dict] = None
    analyst_response: Optional[Dict] = None
    error: Optional[str] = None


class PredictorAPI:
    """
    API handler for The Analyst predictions.
    Keeps predictor logic separate from main chat.
    """

    def __init__(self):
        self.engine = PredictionEngine()
        self.analyst = TheAnalyst()
        self.db = PredictorDB()

    def predict(
        self,
        request: PredictionRequest,
        verbose: bool = True,
        save_to_db: bool = True
    ) -> PredictionAPIResponse:
        """
        Generate prediction for a match.

        Args:
            request: Match details and data
            verbose: Include detailed factor breakdown
            save_to_db: Save prediction to database

        Returns:
            PredictionAPIResponse with prediction and analyst commentary
        """
        try:
            # Generate prediction
            prediction = self.engine.analyze_match(
                home_team=request.home_team,
                away_team=request.away_team,
                favorite=request.favorite,
                underdog=request.underdog,
                match_date=request.match_date,
                match_data=request.match_data
            )

            # Convert to dict
            pred_dict = self.engine.to_dict(prediction)

            # Generate analyst response
            analyst_response = self.analyst.generate_response(pred_dict, verbose=verbose)

            # Save to database if requested
            if save_to_db:
                self.db.save_prediction(pred_dict)

            return PredictionAPIResponse(
                success=True,
                prediction=pred_dict,
                analyst_response={
                    'summary': analyst_response.summary,
                    'analysis': analyst_response.analysis,
                    'insight': analyst_response.insight,
                    'confidence_statement': analyst_response.confidence_statement,
                    'warning': analyst_response.warning,
                    'full_text': self.analyst.format_full_response(analyst_response)
                }
            )

        except Exception as e:
            return PredictionAPIResponse(
                success=False,
                error=str(e)
            )

    def get_team_profile(self, team_name: str) -> Optional[Dict]:
        """Get predictor's profile for a team."""
        return self.db.get_team_profile(team_name)

    def get_recent_predictions(self, limit: int = 10) -> List[Dict]:
        """Get recent predictions."""
        return self.db.get_recent_predictions(limit)

    def get_validated_patterns(self) -> List[Dict]:
        """Get validated third knowledge patterns."""
        return self.db.get_validated_patterns()

    def get_upset_rate(self, team: str, as_favorite: bool = True) -> float:
        """Get historical upset rate for a team."""
        return self.db.get_upset_rate(team, as_favorite)


# ============================================
# QUICK ACCESS FUNCTIONS
# ============================================

_api_instance = None

def get_predictor_api() -> PredictorAPI:
    """Get singleton predictor API instance."""
    global _api_instance
    if _api_instance is None:
        _api_instance = PredictorAPI()
    return _api_instance


def quick_predict(
    home_team: str,
    away_team: str,
    favorite: str,
    underdog: str,
    match_date: str = "2024-12-28",
    **match_data
) -> str:
    """
    Quick prediction with analyst response.
    Returns formatted string for display.
    """
    api = get_predictor_api()

    request = PredictionRequest(
        home_team=home_team,
        away_team=away_team,
        favorite=favorite,
        underdog=underdog,
        match_date=match_date,
        match_data=match_data
    )

    response = api.predict(request, verbose=True, save_to_db=False)

    if response.success:
        return response.analyst_response['full_text']
    else:
        return f"Error: {response.error}"


# ============================================
# DEMO
# ============================================

if __name__ == "__main__":
    result = quick_predict(
        home_team="Crystal Palace",
        away_team="Manchester City",
        favorite="Manchester City",
        underdog="Crystal Palace",
        # Match data
        favorite_rest_days=3,
        favorite_injuries=["Rodri"],
        favorite_recent_games=3,
        favorite_is_home=False,
        favorite_form="WDWLW",
        favorite_xg=2.3,
        favorite_actual_goals=2.8,
        favorite_style="possession",
        pressure_type="title_race",
        days_since_european=3,
        squad_issues=[],
        underdog_rest_days=7,
        position_gap=12,
        underdog_home_unbeaten=5,
        underdog_is_home=True,
        underdog_form="WWDWL",
        counter_attack_goals_pct=0.35,
        set_piece_goals_pct=0.22,
        goalkeeper_save_rate=0.74,
        is_derby=False,
        is_relegation_threatened=False,
        points_from_safety=15,
        games_since_manager_change=None,
        weather="rain"
    )

    print(result)
