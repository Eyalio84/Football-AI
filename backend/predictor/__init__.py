"""
Soccer-AI Predictor Module
The Analyst's brain - two-sided prediction with third knowledge discovery.

Architecture:
- predictor_db.py: Facts database connection
- side_a_calculator.py: Favorite weakness analysis (10 factors)
- side_b_calculator.py: Underdog strength analysis (10 factors)
- prediction_engine.py: Main orchestrator with Third Knowledge
- analyst_persona.py: The Analyst's unique voice
- api.py: API endpoint handlers

Philosophy:
"The question isn't who SHOULD win.
 The question is: what would make the SHOULD not happen?"

Separation of Concerns:
- This module is SEPARATE from the fan chat system
- Uses its own database (predictor_facts.db)
- Has its own persona (The Analyst - cold, analytical)
- Can be used independently or integrated with fan personas
"""

from .prediction_engine import PredictionEngine, Prediction
from .predictor_db import PredictorDB
from .side_a_calculator import SideACalculator, FactorResult
from .side_b_calculator import SideBCalculator
from .analyst_persona import TheAnalyst, AnalystResponse
from .api import PredictorAPI, quick_predict

__all__ = [
    'PredictionEngine',
    'Prediction',
    'PredictorDB',
    'SideACalculator',
    'SideBCalculator',
    'FactorResult',
    'TheAnalyst',
    'AnalystResponse',
    'PredictorAPI',
    'quick_predict'
]
