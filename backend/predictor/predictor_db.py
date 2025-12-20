"""
Predictor Database Module
Connection and queries for The Analyst's facts database.
Separate from main soccer_ai.db - this is the predictor's unique knowledge.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime

# Predictor's own database (separate from main)
PREDICTOR_DB_PATH = Path(__file__).parent.parent / "predictor_facts.db"


@contextmanager
def get_predictor_connection():
    """Context manager for predictor database connections."""
    conn = sqlite3.connect(PREDICTOR_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def dict_from_row(row: sqlite3.Row) -> Optional[Dict[str, Any]]:
    """Convert sqlite3.Row to dict."""
    return dict(row) if row else None


class PredictorDB:
    """
    The Analyst's knowledge repository.
    Stores facts, patterns, predictions, and learnings.
    """

    # ============================================
    # FACTOR DEFINITIONS
    # ============================================

    @staticmethod
    def get_side_a_factors() -> List[Dict]:
        """Get all Side A (favorite weakness) factor definitions."""
        with get_predictor_connection() as conn:
            cursor = conn.execute("""
                SELECT code, name, description, data_source, weight, is_active
                FROM factor_definitions_a
                WHERE is_active = TRUE
                ORDER BY code
            """)
            return [dict_from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def get_side_b_factors() -> List[Dict]:
        """Get all Side B (underdog strength) factor definitions."""
        with get_predictor_connection() as conn:
            cursor = conn.execute("""
                SELECT code, name, description, data_source, weight, is_active
                FROM factor_definitions_b
                WHERE is_active = TRUE
                ORDER BY code
            """)
            return [dict_from_row(row) for row in cursor.fetchall()]

    # ============================================
    # MATCH FACTS
    # ============================================

    @staticmethod
    def record_match_fact(
        match_id: int,
        season: str,
        match_date: str,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        favorite: str,
        underdog: str,
        was_upset: bool,
        upset_magnitude: float = 0.0
    ) -> int:
        """Record a match fact for learning."""
        with get_predictor_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO predictor_match_facts
                (match_id, season, match_date, home_team, away_team,
                 home_score, away_score, favorite, underdog, was_upset, upset_magnitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (match_id, season, match_date, home_team, away_team,
                  home_score, away_score, favorite, underdog, was_upset, upset_magnitude))
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_upset_rate(team: str, as_favorite: bool = True) -> float:
        """Get historical upset rate for a team."""
        with get_predictor_connection() as conn:
            if as_favorite:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN was_upset THEN 1 ELSE 0 END) as upsets
                    FROM predictor_match_facts
                    WHERE favorite = ?
                """, (team,))
            else:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN was_upset THEN 1 ELSE 0 END) as upsets
                    FROM predictor_match_facts
                    WHERE underdog = ?
                """, (team,))
            row = cursor.fetchone()
            if row and row['total'] > 0:
                return row['upsets'] / row['total']
            return 0.0

    # ============================================
    # PREDICTIONS
    # ============================================

    @staticmethod
    def save_prediction(prediction: Dict) -> int:
        """Save a prediction to the database."""
        with get_predictor_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO predictor_predictions
                (match_id, match_date, home_team, away_team, favorite, underdog,
                 side_a_score, side_a_top_factors, side_b_score, side_b_top_factors,
                 naive_upset_prob, interaction_boost, third_knowledge_adj, final_upset_prob,
                 confidence_level, confidence_score, explanation, key_insight)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction.get('match_id'),
                prediction.get('match_date'),
                prediction.get('home_team'),
                prediction.get('away_team'),
                prediction.get('favorite'),
                prediction.get('underdog'),
                prediction.get('side_a_score'),
                json.dumps(prediction.get('side_a_top_factors', [])),
                prediction.get('side_b_score'),
                json.dumps(prediction.get('side_b_top_factors', [])),
                prediction.get('naive_upset_prob'),
                prediction.get('interaction_boost', 0),
                prediction.get('third_knowledge_adj', 0),
                prediction.get('final_upset_prob'),
                prediction.get('confidence_level'),
                prediction.get('confidence_score'),
                prediction.get('explanation'),
                prediction.get('key_insight')
            ))
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_recent_predictions(limit: int = 10) -> List[Dict]:
        """Get recent predictions."""
        with get_predictor_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM predictor_predictions
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            results = []
            for row in cursor.fetchall():
                result = dict_from_row(row)
                # Parse JSON fields
                result['side_a_top_factors'] = json.loads(result.get('side_a_top_factors', '[]'))
                result['side_b_top_factors'] = json.loads(result.get('side_b_top_factors', '[]'))
                results.append(result)
            return results

    # ============================================
    # THIRD KNOWLEDGE PATTERNS
    # ============================================

    @staticmethod
    def get_validated_patterns() -> List[Dict]:
        """Get all validated third knowledge patterns."""
        with get_predictor_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM third_knowledge_patterns
                WHERE is_validated = TRUE
                ORDER BY confidence DESC
            """)
            return [dict_from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def save_pattern(pattern: Dict) -> int:
        """Save a discovered pattern."""
        with get_predictor_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO third_knowledge_patterns
                (pattern_name, description, factor_a_code, factor_b_code,
                 interaction_type, multiplier, threshold_value, sample_size,
                 success_rate, confidence, is_validated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern.get('pattern_name'),
                pattern.get('description'),
                pattern.get('factor_a_code'),
                pattern.get('factor_b_code'),
                pattern.get('interaction_type'),
                pattern.get('multiplier', 1.0),
                pattern.get('threshold_value'),
                pattern.get('sample_size', 0),
                pattern.get('success_rate'),
                pattern.get('confidence', 0.5),
                pattern.get('is_validated', False)
            ))
            conn.commit()
            return cursor.lastrowid

    # ============================================
    # TEAM PROFILES
    # ============================================

    @staticmethod
    def get_team_profile(team_name: str) -> Optional[Dict]:
        """Get predictor's profile of a team."""
        with get_predictor_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM predictor_team_profiles
                WHERE team_name = ?
            """, (team_name,))
            return dict_from_row(cursor.fetchone())

    @staticmethod
    def update_team_profile(team_name: str, profile: Dict) -> None:
        """Update or create team profile."""
        with get_predictor_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO predictor_team_profiles
                (team_name, team_id, playing_style, avg_possession, avg_ppda,
                 set_piece_threat, counter_attack_efficiency, pressure_handling,
                 home_fortress_rating, away_performance_rating, comeback_ability,
                 collapse_risk, current_form, xg_trend, momentum_score,
                 upset_likelihood_as_favorite, upset_likelihood_as_underdog,
                 best_conditions, worst_conditions, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                team_name,
                profile.get('team_id'),
                profile.get('playing_style'),
                profile.get('avg_possession'),
                profile.get('avg_ppda'),
                profile.get('set_piece_threat'),
                profile.get('counter_attack_efficiency'),
                profile.get('pressure_handling'),
                profile.get('home_fortress_rating'),
                profile.get('away_performance_rating'),
                profile.get('comeback_ability'),
                profile.get('collapse_risk'),
                profile.get('current_form'),
                profile.get('xg_trend'),
                profile.get('momentum_score'),
                profile.get('upset_likelihood_as_favorite'),
                profile.get('upset_likelihood_as_underdog'),
                json.dumps(profile.get('best_conditions', [])),
                json.dumps(profile.get('worst_conditions', [])),
                datetime.now().isoformat()
            ))
            conn.commit()

    # ============================================
    # API ENDPOINTS TRACKING
    # ============================================

    @staticmethod
    def record_api_endpoint(
        source_name: str,
        endpoint_url: str,
        data_type: str,
        use_for: str,  # 'fan', 'predictor', 'both'
        is_free: bool = True,
        rate_limit: str = None,
        notes: str = None
    ) -> int:
        """Record a discovered API endpoint."""
        with get_predictor_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO api_endpoints
                (source_name, endpoint_url, data_type, use_for, is_free, rate_limit, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (source_name, endpoint_url, data_type, use_for, is_free, rate_limit, notes))
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_endpoints_for(use_for: str) -> List[Dict]:
        """Get endpoints for fan or predictor."""
        with get_predictor_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM api_endpoints
                WHERE use_for = ? OR use_for = 'both'
                ORDER BY source_name
            """, (use_for,))
            return [dict_from_row(row) for row in cursor.fetchall()]

    # ============================================
    # ANALYST INSIGHTS
    # ============================================

    @staticmethod
    def record_insight(
        insight_type: str,
        title: str,
        description: str,
        supporting_data: Dict = None,
        confidence: float = 0.5
    ) -> int:
        """Record an insight The Analyst discovered."""
        with get_predictor_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO analyst_insights
                (insight_type, title, description, supporting_data, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (
                insight_type,
                title,
                description,
                json.dumps(supporting_data) if supporting_data else None,
                confidence
            ))
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_top_insights(limit: int = 10) -> List[Dict]:
        """Get top insights by success rate."""
        with get_predictor_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM analyst_insights
                WHERE actionable = TRUE
                ORDER BY success_rate DESC NULLS LAST, confidence DESC
                LIMIT ?
            """, (limit,))
            return [dict_from_row(row) for row in cursor.fetchall()]

    # ============================================
    # STATISTICS
    # ============================================

    @staticmethod
    def get_predictor_stats() -> Dict:
        """Get predictor database statistics."""
        with get_predictor_connection() as conn:
            stats = {}
            tables = [
                'predictor_match_facts', 'predictor_predictions',
                'third_knowledge_patterns', 'predictor_team_profiles',
                'analyst_insights', 'api_endpoints'
            ]
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            return stats
