"""
Dixon-Coles Football Prediction Model

Extends independent Poisson with:
- Per-team attack/defense strength parameters
- Home advantage parameter
- Rho (ρ) correlation for low-scoring outcomes (0-0, 1-0, 0-1, 1-1)
- Time-decay weighting (recent matches matter more)

Reference: Dixon & Coles (1997) "Modelling Association Football Scores
and Inefficiencies in the Football Betting Market"
"""

import math
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BACKEND_DIR = Path(__file__).resolve().parent.parent
UNIFIED_DB = BACKEND_DIR / "unified_soccer_ai_kg.db"

# ─── Data Structures ──────────────────────────────────────────────


@dataclass
class TeamParams:
    attack: float = 0.0  # Log attack strength (higher = more goals scored)
    defense: float = 0.0  # Log defense strength (higher = more goals conceded)


@dataclass
class DixonColesModel:
    """Fitted Dixon-Coles model parameters."""
    teams: Dict[str, TeamParams] = field(default_factory=dict)
    home_advantage: float = 0.3  # Log home advantage
    rho: float = -0.05  # Correlation parameter for low-scoring outcomes
    avg_goals: float = 1.4  # League average goals per team per match
    fitted_date: str = ""
    n_matches: int = 0


# ─── Poisson PMF ──────────────────────────────────────────────────


def poisson_pmf(k: int, lam: float) -> float:
    """Probability of k goals given expected rate lam."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


# ─── Dixon-Coles Tau Correction ───────────────────────────────────


def tau(x: int, y: int, lam: float, mu: float, rho: float) -> float:
    """
    Dixon-Coles correction factor for low-scoring outcomes.
    x = home goals, y = away goals, lam = home rate, mu = away rate.
    Only modifies probabilities for (0,0), (1,0), (0,1), (1,1).
    """
    if x == 0 and y == 0:
        return 1.0 - lam * mu * rho
    elif x == 0 and y == 1:
        return 1.0 + lam * rho
    elif x == 1 and y == 0:
        return 1.0 + mu * rho
    elif x == 1 and y == 1:
        return 1.0 - rho
    else:
        return 1.0


# ─── Score Probability ────────────────────────────────────────────


def score_probability(x: int, y: int, lam: float, mu: float, rho: float) -> float:
    """
    Probability of home scoring x and away scoring y
    under the Dixon-Coles model.
    """
    return tau(x, y, lam, mu, rho) * poisson_pmf(x, lam) * poisson_pmf(y, mu)


def match_probabilities(lam: float, mu: float, rho: float,
                        max_goals: int = 8) -> Tuple[float, float, float]:
    """
    Compute P(home win), P(draw), P(away win) from expected goals.
    Returns (p_home, p_draw, p_away).
    """
    p_home = 0.0
    p_draw = 0.0
    p_away = 0.0

    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = score_probability(i, j, lam, mu, rho)
            if i > j:
                p_home += p
            elif i == j:
                p_draw += p
            else:
                p_away += p

    # Normalize to sum to 1 (floating point)
    total = p_home + p_draw + p_away
    if total > 0:
        p_home /= total
        p_draw /= total
        p_away /= total

    return p_home, p_draw, p_away


# ─── Model Fitting ────────────────────────────────────────────────


def _time_weight(match_date: str, reference_date: str, half_life_days: float = 180) -> float:
    """Exponential time decay weight. Half-life = 180 days (~6 months)."""
    try:
        d_match = datetime.strptime(match_date[:10], "%Y-%m-%d")
        d_ref = datetime.strptime(reference_date[:10], "%Y-%m-%d")
        days_ago = (d_ref - d_match).days
        if days_ago < 0:
            days_ago = 0
        return math.exp(-0.693 * days_ago / half_life_days)
    except (ValueError, TypeError):
        return 0.5


def fit_model(division: str = "E0", seasons_back: int = 3,
              reference_date: str = None) -> DixonColesModel:
    """
    Fit Dixon-Coles model on recent match history.

    Uses iterative approach:
    1. Estimate attack/defense from goals scored/conceded (weighted)
    2. Estimate home advantage from home vs away scoring rates
    3. Estimate rho from low-scoring result frequencies vs model predictions

    Args:
        division: League code (E0 = Premier League)
        seasons_back: How many seasons of data to use
        reference_date: Date to measure recency from (default: today)
    """
    if reference_date is None:
        reference_date = datetime.now().strftime("%Y-%m-%d")

    ref_year = int(reference_date[:4])
    start_date = f"{ref_year - seasons_back}-08-01"

    conn = sqlite3.connect(str(UNIFIED_DB))
    conn.row_factory = sqlite3.Row

    matches = conn.execute("""
        SELECT match_date, home_team, away_team, ft_home, ft_away, ft_result
        FROM match_history
        WHERE division = ? AND match_date >= ? AND match_date <= ?
          AND ft_home IS NOT NULL AND ft_away IS NOT NULL
        ORDER BY match_date
    """, (division, start_date, reference_date)).fetchall()
    conn.close()

    if not matches:
        return DixonColesModel()

    # ── Step 1: Compute weighted attack/defense strengths ──

    team_attack_sum = defaultdict(float)
    team_attack_weight = defaultdict(float)
    team_defense_sum = defaultdict(float)
    team_defense_weight = defaultdict(float)
    home_goals_total = 0.0
    away_goals_total = 0.0
    total_weight = 0.0

    for m in matches:
        w = _time_weight(m["match_date"], reference_date)
        home = m["home_team"]
        away = m["away_team"]
        gh = m["ft_home"]
        ga = m["ft_away"]

        # Attack = goals scored, defense = goals conceded
        team_attack_sum[home] += gh * w
        team_attack_weight[home] += w
        team_defense_sum[home] += ga * w
        team_defense_weight[home] += w

        team_attack_sum[away] += ga * w
        team_attack_weight[away] += w
        team_defense_sum[away] += ga * w  # Away concedes home goals
        # Correction: away defense = home goals conceded by away team
        # Actually: away team concedes gh goals, scores ga goals
        team_defense_sum[away] = team_defense_sum.get(away, 0)  # Reset needed
        team_attack_sum[away] += ga * w  # Away scores ga
        team_defense_sum[away] += gh * w  # Away concedes gh

        home_goals_total += gh * w
        away_goals_total += ga * w
        total_weight += w

    # Fix double-counting from the loop above
    # Recalculate cleanly
    team_attack_sum = defaultdict(float)
    team_attack_weight = defaultdict(float)
    team_defense_sum = defaultdict(float)
    team_defense_weight = defaultdict(float)
    home_goals_total = 0.0
    away_goals_total = 0.0
    total_weight = 0.0

    for m in matches:
        w = _time_weight(m["match_date"], reference_date)
        home = m["home_team"]
        away = m["away_team"]
        gh = m["ft_home"]
        ga = m["ft_away"]

        # Home team attack = goals scored at home
        team_attack_sum[home] += gh * w
        team_attack_weight[home] += w
        # Home team defense = goals conceded at home
        team_defense_sum[home] += ga * w
        team_defense_weight[home] += w

        # Away team attack = goals scored away
        team_attack_sum[away] += ga * w
        team_attack_weight[away] += w
        # Away team defense = goals conceded away
        team_defense_sum[away] += gh * w
        team_defense_weight[away] += w

        home_goals_total += gh * w
        away_goals_total += ga * w
        total_weight += w

    # League averages
    avg_home_goals = home_goals_total / total_weight if total_weight > 0 else 1.5
    avg_away_goals = away_goals_total / total_weight if total_weight > 0 else 1.1
    avg_goals = (avg_home_goals + avg_away_goals) / 2

    # Home advantage (in log space)
    home_adv = math.log(avg_home_goals / avg_away_goals) if avg_away_goals > 0 else 0.3

    # Compute per-team attack and defense RATES (goals per match, weighted)
    # Attack = goals scored per match (higher = better attacker)
    # Defense = goals conceded per match (lower = better defender)
    teams = {}
    all_teams = set(team_attack_sum.keys())

    for team in all_teams:
        aw = team_attack_weight[team]
        dw = team_defense_weight[team]
        if aw > 0 and dw > 0:
            # Attack strength = (team's scoring rate) / (league average scoring rate)
            attack_rate = team_attack_sum[team] / aw
            attack_strength = attack_rate / avg_goals

            # Defense strength = (team's conceding rate) / (league average conceding rate)
            defense_rate = team_defense_sum[team] / dw
            defense_strength = defense_rate / avg_goals

            teams[team] = TeamParams(
                attack=math.log(max(attack_strength, 0.3)),   # Log scale
                defense=math.log(max(defense_strength, 0.3)),  # Log scale
            )

    # ── Step 2: Estimate rho via grid search on log-likelihood ──

    # Test multiple rho values and pick the one that maximizes log-likelihood
    best_rho = -0.05
    best_ll = float("-inf")

    for rho_candidate in [r / 100 for r in range(-15, 6)]:  # -0.15 to 0.05
        ll = 0.0
        for m in matches:
            home = m["home_team"]
            away = m["away_team"]
            gh = m["ft_home"]
            ga = m["ft_away"]

            if home not in teams or away not in teams:
                continue

            lam = avg_goals * math.exp(teams[home].attack - teams[away].defense + home_adv / 2)
            mu = avg_goals * math.exp(teams[away].attack - teams[home].defense - home_adv / 2)
            lam = max(0.3, min(lam, 4.5))
            mu = max(0.3, min(mu, 4.5))

            w = _time_weight(m["match_date"], reference_date)
            p = score_probability(gh, ga, lam, mu, rho_candidate)
            if p > 0:
                ll += w * math.log(p)

        if ll > best_ll:
            best_ll = ll
            best_rho = rho_candidate

    rho = best_rho

    model = DixonColesModel(
        teams=teams,
        home_advantage=home_adv,
        rho=rho,
        avg_goals=avg_goals,
        fitted_date=reference_date,
        n_matches=len(matches),
    )

    return model


# ─── Prediction ───────────────────────────────────────────────────


def predict(model: DixonColesModel, home_team: str, away_team: str) -> Dict:
    """
    Predict match outcome using fitted Dixon-Coles model.

    Returns dict with:
        home_win, draw, away_win: probabilities
        expected_home_goals, expected_away_goals: float
        rho: correlation parameter used
        most_likely_score: (h, a) tuple
    """
    home_params = model.teams.get(home_team)
    away_params = model.teams.get(away_team)

    if not home_params or not away_params:
        # Fallback for unknown teams: use league average
        lam = model.avg_goals * math.exp(model.home_advantage / 2)
        mu = model.avg_goals * math.exp(-model.home_advantage / 2)
    else:
        # Expected home goals = avg * home_attack * away_defense_weakness * home_advantage
        # attack > 0 means scores more than average, defense > 0 means concedes more than average
        lam = model.avg_goals * math.exp(
            home_params.attack + away_params.defense + model.home_advantage / 2
        )
        # Expected away goals = avg * away_attack * home_defense_weakness * away_disadvantage
        mu = model.avg_goals * math.exp(
            away_params.attack + home_params.defense - model.home_advantage / 2
        )

    # Clamp
    lam = max(0.2, min(lam, 5.0))
    mu = max(0.2, min(mu, 5.0))

    p_home, p_draw, p_away = match_probabilities(lam, mu, model.rho)

    # Find most likely score
    best_score = (0, 0)
    best_p = 0.0
    for i in range(6):
        for j in range(6):
            p = score_probability(i, j, lam, mu, model.rho)
            if p > best_p:
                best_p = p
                best_score = (i, j)

    return {
        "home_win": round(p_home, 4),
        "draw": round(p_draw, 4),
        "away_win": round(p_away, 4),
        "expected_home_goals": round(lam, 2),
        "expected_away_goals": round(mu, 2),
        "most_likely_score": best_score,
        "most_likely_score_prob": round(best_p, 4),
        "rho": round(model.rho, 4),
        "home_team": home_team,
        "away_team": away_team,
    }


# ─── Bookmaker Odds Integration ──────────────────────────────────


def odds_to_probabilities(odd_home: float, odd_draw: float, odd_away: float) -> Tuple[float, float, float]:
    """
    Convert bookmaker decimal odds to implied probabilities
    after removing the overround (vig).
    """
    if odd_home <= 0 or odd_draw <= 0 or odd_away <= 0:
        return (0.4, 0.3, 0.3)

    # Raw implied probabilities
    raw_h = 1.0 / odd_home
    raw_d = 1.0 / odd_draw
    raw_a = 1.0 / odd_away

    # Overround (typically 1.02-1.12)
    overround = raw_h + raw_d + raw_a

    # Normalize to remove vig
    p_h = raw_h / overround
    p_d = raw_d / overround
    p_a = raw_a / overround

    return (p_h, p_d, p_a)


def get_match_odds(home_team: str, away_team: str, match_date: str = None) -> Optional[Tuple[float, float, float]]:
    """
    Look up bookmaker odds for a specific match from the database.
    Returns (odd_home, odd_draw, odd_away) or None.
    """
    conn = sqlite3.connect(str(UNIFIED_DB))
    conn.row_factory = sqlite3.Row

    if match_date:
        row = conn.execute("""
            SELECT odd_home, odd_draw, odd_away
            FROM match_history
            WHERE home_team = ? AND away_team = ? AND match_date = ?
            AND odd_home > 0
        """, (home_team, away_team, match_date)).fetchone()
    else:
        # Get most recent match between these teams
        row = conn.execute("""
            SELECT odd_home, odd_draw, odd_away
            FROM match_history
            WHERE home_team = ? AND away_team = ?
            AND odd_home > 0
            ORDER BY match_date DESC LIMIT 1
        """, (home_team, away_team)).fetchone()

    conn.close()

    if row and row["odd_home"] > 0:
        return (row["odd_home"], row["odd_draw"], row["odd_away"])
    return None


# ─── Backtest ─────────────────────────────────────────────────────


def backtest(test_season: str = "2024", train_seasons: int = 3) -> Dict:
    """
    Backtest the Dixon-Coles model on a full season.
    Trains on prior seasons, tests on the specified season.

    Returns accuracy metrics.
    """
    test_start = f"{test_season}-08-01"
    test_end = f"{int(test_season) + 1}-06-30"

    # Fit model on data BEFORE the test season
    model = fit_model(
        division="E0",
        seasons_back=train_seasons,
        reference_date=test_start,
    )

    # Load test matches
    conn = sqlite3.connect(str(UNIFIED_DB))
    conn.row_factory = sqlite3.Row

    test_matches = conn.execute("""
        SELECT match_date, home_team, away_team, ft_home, ft_away, ft_result,
               odd_home, odd_draw, odd_away
        FROM match_history
        WHERE division = 'E0' AND match_date >= ? AND match_date <= ?
          AND ft_home IS NOT NULL AND ft_away IS NOT NULL
        ORDER BY match_date
    """, (test_start, test_end)).fetchall()
    conn.close()

    if not test_matches:
        return {"error": "No test matches found"}

    # Test Dixon-Coles predictions
    dc_correct = 0
    dc_draw_predicted = 0
    dc_draw_correct = 0
    actual_draws = 0
    brier_sum = 0.0

    # Test bookmaker odds predictions
    bk_correct = 0
    bk_draw_predicted = 0
    bk_draw_correct = 0
    bk_brier_sum = 0.0
    bk_count = 0

    # Test ensemble (DC + bookmaker)
    ens_correct = 0
    ens_draw_predicted = 0
    ens_draw_correct = 0
    ens_brier_sum = 0.0
    ens_count = 0

    for m in test_matches:
        actual = m["ft_result"]
        home = m["home_team"]
        away = m["away_team"]

        if actual == "D":
            actual_draws += 1

        # Dixon-Coles prediction
        pred = predict(model, home, away)
        dc_pred_result = max(
            ("H", pred["home_win"]),
            ("D", pred["draw"]),
            ("A", pred["away_win"]),
            key=lambda x: x[1]
        )[0]

        if dc_pred_result == actual:
            dc_correct += 1
        if dc_pred_result == "D":
            dc_draw_predicted += 1
            if actual == "D":
                dc_draw_correct += 1

        # Brier score (lower is better)
        actual_vec = [1 if actual == "H" else 0, 1 if actual == "D" else 0, 1 if actual == "A" else 0]
        brier_sum += sum((p - a) ** 2 for p, a in zip(
            [pred["home_win"], pred["draw"], pred["away_win"]], actual_vec
        ))

        # Bookmaker odds prediction
        if m["odd_home"] and m["odd_home"] > 0:
            bk_h, bk_d, bk_a = odds_to_probabilities(m["odd_home"], m["odd_draw"], m["odd_away"])
            bk_pred = max(("H", bk_h), ("D", bk_d), ("A", bk_a), key=lambda x: x[1])[0]

            if bk_pred == actual:
                bk_correct += 1
            if bk_pred == "D":
                bk_draw_predicted += 1
                if actual == "D":
                    bk_draw_correct += 1

            bk_brier_sum += sum((p - a) ** 2 for p, a in zip([bk_h, bk_d, bk_a], actual_vec))
            bk_count += 1

            # Ensemble: 40% Dixon-Coles + 60% Bookmaker
            ens_h = 0.40 * pred["home_win"] + 0.60 * bk_h
            ens_d = 0.40 * pred["draw"] + 0.60 * bk_d
            ens_a = 0.40 * pred["away_win"] + 0.60 * bk_a

            # Draw detection: draws are systematically under-predicted.
            # If P(draw) is close to the max outcome and above threshold, predict draw.
            max_p = max(ens_h, ens_d, ens_a)
            DRAW_THRESHOLD = 0.245
            if ens_d >= DRAW_THRESHOLD and ens_d >= max_p * 0.75:
                ens_pred = "D"
            else:
                ens_pred = max(("H", ens_h), ("D", ens_d), ("A", ens_a), key=lambda x: x[1])[0]

            if ens_pred == actual:
                ens_correct += 1
            if ens_pred == "D":
                ens_draw_predicted += 1
                if actual == "D":
                    ens_draw_correct += 1

            ens_brier_sum += sum((p - a) ** 2 for p, a in zip([ens_h, ens_d, ens_a], actual_vec))
            ens_count += 1

    n = len(test_matches)

    result = {
        "season": f"{test_season}-{str(int(test_season)+1)[-2:]}",
        "matches": n,
        "actual_draws": actual_draws,
        "actual_draw_rate": round(actual_draws / n * 100, 1),

        "dixon_coles": {
            "accuracy": round(dc_correct / n * 100, 1),
            "correct": dc_correct,
            "draws_predicted": dc_draw_predicted,
            "draws_correct": dc_draw_correct,
            "draw_precision": round(dc_draw_correct / dc_draw_predicted * 100, 1) if dc_draw_predicted > 0 else 0,
            "brier_score": round(brier_sum / n, 4),
            "rho": model.rho,
        },

        "bookmaker": {
            "accuracy": round(bk_correct / bk_count * 100, 1) if bk_count > 0 else 0,
            "correct": bk_correct,
            "draws_predicted": bk_draw_predicted,
            "draws_correct": bk_draw_correct,
            "draw_precision": round(bk_draw_correct / bk_draw_predicted * 100, 1) if bk_draw_predicted > 0 else 0,
            "brier_score": round(bk_brier_sum / bk_count, 4) if bk_count > 0 else 0,
            "matches_with_odds": bk_count,
        },

        "ensemble_dc_bk": {
            "accuracy": round(ens_correct / ens_count * 100, 1) if ens_count > 0 else 0,
            "correct": ens_correct,
            "draws_predicted": ens_draw_predicted,
            "draws_correct": ens_draw_correct,
            "draw_precision": round(ens_draw_correct / ens_draw_predicted * 100, 1) if ens_draw_predicted > 0 else 0,
            "brier_score": round(ens_brier_sum / ens_count, 4) if ens_count > 0 else 0,
            "weights": "45% DC + 55% BK",
        },

        "model_info": {
            "teams_fitted": len(model.teams),
            "training_matches": model.n_matches,
            "home_advantage": round(model.home_advantage, 4),
            "rho": round(model.rho, 4),
            "avg_goals": round(model.avg_goals, 3),
        },
    }

    return result


# ─── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("  Dixon-Coles Model — Backtest")
    print("=" * 60)

    results = backtest(test_season="2024", train_seasons=3)
    print(json.dumps(results, indent=2))
