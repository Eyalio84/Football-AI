#!/usr/bin/env python3
"""
Auto-generate trivia questions from the 230K match_history database.

Mines: match_history (9410 PL matches), kb_facts (681), elo_history.
Generates questions across 6 categories: records, head2head, history,
stats, legends, rivalries.

Usage:
    python scripts/generate_trivia.py              # preview only
    python scripts/generate_trivia.py --apply      # insert into DB
    python scripts/generate_trivia.py --apply --clear-old  # replace all
"""

import sqlite3
import json
import random
import os
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

BACKEND_DIR = Path(__file__).resolve().parent.parent
UNIFIED_DB = BACKEND_DIR / "unified_soccer_ai_kg.db"
MAIN_DB = BACKEND_DIR / "soccer_ai.db"

# Map match_history team names -> teams table names + IDs
TEAM_NAME_MAP = {
    "Arsenal": "Arsenal",
    "Aston Villa": "Aston Villa",
    "Bournemouth": "Bournemouth",
    "Brentford": "Brentford",
    "Brighton": "Brighton",
    "Burnley": "Burnley",
    "Chelsea": "Chelsea",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Fulham": "Fulham",
    "Leeds": "Leeds United",
    "Leicester": "Leicester City",
    "Liverpool": "Liverpool",
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Newcastle": "Newcastle United",
    "Nott'm Forest": "Nottingham Forest",
    "Southampton": "Southampton",
    "Sunderland": "Sunderland",
    "Tottenham": "Tottenham",
    "West Ham": "West Ham",
    "Wolves": "Wolverhampton",
    "Ipswich": "Ipswich Town",
}


def get_team_id_map(conn):
    """Build name -> id map from teams table."""
    rows = conn.execute("SELECT id, name FROM teams").fetchall()
    return {r[1]: r[0] for r in rows}


def load_match_data(conn):
    """Load PL match data from unified DB."""
    return conn.execute("""
        SELECT match_date, home_team, away_team, ft_home, ft_away, ft_result,
               ht_home, ht_away, ht_result, home_elo, away_elo
        FROM match_history
        WHERE division = 'E0'
        ORDER BY match_date
    """).fetchall()


# ─── Question Generators ──────────────────────────────────────────


def gen_biggest_wins(matches):
    """Questions about biggest PL wins."""
    questions = []
    big_wins = []
    for m in matches:
        date, home, away, fh, fa = m[0], m[1], m[2], m[3], m[4]
        if fh is None or fa is None:
            continue
        margin = abs(fh - fa)
        total = fh + fa
        if margin >= 5 or total >= 8:
            winner = home if fh > fa else away
            loser = away if fh > fa else home
            big_wins.append((date, home, away, fh, fa, winner, loser, margin, total))

    big_wins.sort(key=lambda x: x[7], reverse=True)

    for date, home, away, fh, fa, winner, loser, margin, total in big_wins[:20]:
        year = date[:4]
        score = f"{fh}-{fa}"
        q = {
            "category": "records",
            "difficulty": "hard",
            "question": f"In {year}, what was the score when {home} hosted {away} in a memorable Premier League thrashing?",
            "correct_answer": score,
            "wrong_answers": _score_distractors(fh, fa),
            "explanation": f"{home} beat {away} {score} on {date} - one of the biggest results in PL history.",
            "team": winner,
        }
        questions.append(q)

    return questions


def gen_head2head_dominance(matches):
    """Questions about head-to-head records between teams."""
    questions = []
    h2h = defaultdict(lambda: {"w": 0, "d": 0, "l": 0})

    for m in matches:
        home, away, result = m[1], m[2], m[5]
        key = tuple(sorted([home, away]))
        if result == "H":
            h2h[(home, away)]["w"] += 1
            h2h[(away, home)]["l"] += 1
        elif result == "A":
            h2h[(home, away)]["l"] += 1
            h2h[(away, home)]["w"] += 1
        else:
            h2h[(home, away)]["d"] += 1
            h2h[(away, home)]["d"] += 1

    # Find dominant matchups (>65% win rate, min 10 games)
    for (team_a, team_b), record in h2h.items():
        total = record["w"] + record["d"] + record["l"]
        if total < 10:
            continue
        win_rate = record["w"] / total
        if win_rate >= 0.60:
            correct = str(record["w"])
            wrongs = [str(record["w"] + i) for i in [-3, 2, 5]]
            diff = "medium" if total >= 20 else "hard"
            q = {
                "category": "head2head",
                "difficulty": diff,
                "question": f"In the Premier League era (since 2000), how many times have {team_a} beaten {team_b}?",
                "correct_answer": correct,
                "wrong_answers": wrongs,
                "explanation": f"{team_a} have won {record['w']} of their {total} PL meetings with {team_b} (drew {record['d']}, lost {record['l']}).",
                "team": team_a,
            }
            questions.append(q)

    return questions[:25]


def gen_comebacks(matches):
    """Questions about famous comebacks (losing at HT, winning at FT)."""
    questions = []
    comebacks = []

    for m in matches:
        date, home, away = m[0], m[1], m[2]
        ft_home, ft_away, ft_res = m[3], m[4], m[5]
        ht_home, ht_away, ht_res = m[6], m[7], m[8]

        if any(v is None for v in [ft_home, ft_away, ht_home, ht_away]):
            continue

        # Home comeback: losing at HT, winning at FT
        if ht_res == "A" and ft_res == "H":
            swing = (ft_home - ft_away) + (ht_away - ht_home)
            comebacks.append((date, home, away, ht_home, ht_away, ft_home, ft_away, home, swing))
        # Away comeback
        elif ht_res == "H" and ft_res == "A":
            swing = (ft_away - ft_home) + (ht_home - ht_away)
            comebacks.append((date, home, away, ht_home, ht_away, ft_home, ft_away, away, swing))

    comebacks.sort(key=lambda x: x[8], reverse=True)

    for date, home, away, hth, hta, fth, fta, winner, swing in comebacks[:15]:
        year = date[:4]
        q = {
            "category": "history",
            "difficulty": "hard",
            "question": f"In {year}, which team came from {hth}-{hta} down at half-time to win when {home} played {away}?",
            "correct_answer": winner,
            "wrong_answers": [home if winner == away else away, "It ended in a draw", "The match was abandoned"],
            "explanation": f"{winner} came back from {hth}-{hta} at half-time to win {fth}-{fta} on {date}.",
            "team": winner,
        }
        questions.append(q)

    return questions


def gen_season_records(matches):
    """Questions about seasonal records."""
    questions = []

    # Goals per season
    season_goals = defaultdict(int)
    season_matches = defaultdict(int)
    team_season_goals = defaultdict(int)
    team_season_wins = defaultdict(int)

    for m in matches:
        date, home, away, fh, fa, res = m[0], m[1], m[2], m[3], m[4], m[5]
        if fh is None or fa is None:
            continue
        # Derive season from date (Aug-Jul)
        year = int(date[:4])
        month = int(date[5:7])
        season = f"{year}-{str(year+1)[-2:]}" if month >= 7 else f"{year-1}-{str(year)[-2:]}"

        season_goals[season] += fh + fa
        season_matches[season] += 1
        team_season_goals[(home, season)] += fh
        team_season_goals[(away, season)] += fa

        if res == "H":
            team_season_wins[(home, season)] += 1
        elif res == "A":
            team_season_wins[(away, season)] += 1

    # Highest scoring season
    avg_goals = {s: season_goals[s] / season_matches[s] for s in season_goals if season_matches[s] > 100}
    if avg_goals:
        best_season = max(avg_goals, key=avg_goals.get)
        avg = round(avg_goals[best_season], 2)
        wrongs = [str(round(avg - 0.3, 2)), str(round(avg + 0.2, 2)), str(round(avg - 0.5, 2))]
        questions.append({
            "category": "stats",
            "difficulty": "hard",
            "question": f"What was the average goals per match in the {best_season} PL season (the highest-scoring in our records)?",
            "correct_answer": str(avg),
            "wrong_answers": wrongs,
            "explanation": f"The {best_season} season had {season_goals[best_season]} goals in {season_matches[best_season]} matches, averaging {avg} per game.",
            "team": None,
        })

    # Team with most wins in a season
    best_team_season = max(team_season_wins, key=team_season_wins.get)
    wins = team_season_wins[best_team_season]
    team, season = best_team_season
    wrongs = [str(wins - 2), str(wins + 1), str(wins - 4)]
    questions.append({
        "category": "records",
        "difficulty": "medium",
        "question": f"How many Premier League matches did {team} win in the {season} season?",
        "correct_answer": str(wins),
        "wrong_answers": wrongs,
        "explanation": f"{team} won {wins} PL matches in {season}, the most in a single season in our records.",
        "team": team,
    })

    # Team with most goals in a season
    best_goals = max(team_season_goals, key=team_season_goals.get)
    goals = team_season_goals[best_goals]
    team, season = best_goals
    wrongs = [str(goals - 8), str(goals + 5), str(goals - 15)]
    questions.append({
        "category": "records",
        "difficulty": "medium",
        "question": f"How many Premier League goals did {team} score in the {season} season?",
        "correct_answer": str(goals),
        "wrong_answers": wrongs,
        "explanation": f"{team} scored {goals} goals in the {season} Premier League season.",
        "team": team,
    })

    return questions


def gen_elo_questions(matches):
    """Questions about team strength and ELO ratings."""
    questions = []

    # Find highest ELO ever recorded
    best_elo = {}
    for m in matches:
        date, home, away, home_elo, away_elo = m[0], m[1], m[2], m[9], m[10]
        if home_elo and (home not in best_elo or home_elo > best_elo[home][0]):
            best_elo[home] = (home_elo, date)
        if away_elo and (away not in best_elo or away_elo > best_elo[away][0]):
            best_elo[away] = (away_elo, date)

    # Top 5 all-time ELO peaks
    sorted_elo = sorted(best_elo.items(), key=lambda x: x[1][0], reverse=True)[:5]

    peak_team, (peak_val, peak_date) = sorted_elo[0]
    other_teams = [t for t, _ in sorted_elo[1:4]]
    questions.append({
        "category": "stats",
        "difficulty": "medium",
        "question": "Which team achieved the highest ELO rating in Premier League history?",
        "correct_answer": peak_team,
        "wrong_answers": other_teams,
        "explanation": f"{peak_team} reached an ELO rating of {int(peak_val)} around {peak_date}.",
        "team": peak_team,
    })

    # For each big club, what's their peak?
    for team, (elo, date) in sorted_elo[:4]:
        elo_int = int(elo)
        wrongs = [str(elo_int - 40), str(elo_int + 25), str(elo_int - 80)]
        questions.append({
            "category": "stats",
            "difficulty": "hard",
            "question": f"What was {team}'s peak ELO rating in the Premier League?",
            "correct_answer": str(elo_int),
            "wrong_answers": wrongs,
            "explanation": f"{team} peaked at {elo_int} ELO around {date}.",
            "team": team,
        })

    return questions


def gen_ground_records(matches):
    """Questions about home/away records."""
    questions = []

    home_record = defaultdict(lambda: {"w": 0, "d": 0, "l": 0})
    away_record = defaultdict(lambda: {"w": 0, "d": 0, "l": 0})

    for m in matches:
        home, away, res = m[1], m[2], m[5]
        if res == "H":
            home_record[home]["w"] += 1
            away_record[away]["l"] += 1
        elif res == "A":
            home_record[home]["l"] += 1
            away_record[away]["w"] += 1
        elif res == "D":
            home_record[home]["d"] += 1
            away_record[away]["d"] += 1

    # Best home win %
    home_pct = {t: r["w"] / (r["w"] + r["d"] + r["l"])
                for t, r in home_record.items()
                if r["w"] + r["d"] + r["l"] >= 100}
    if home_pct:
        best_home = max(home_pct, key=home_pct.get)
        pct = round(home_pct[best_home] * 100, 1)
        others = sorted(home_pct, key=home_pct.get, reverse=True)[1:4]
        questions.append({
            "category": "stats",
            "difficulty": "medium",
            "question": "Which team has the best home win percentage in the Premier League (since 2000)?",
            "correct_answer": best_home,
            "wrong_answers": list(others),
            "explanation": f"{best_home} have won {pct}% of their home PL matches since 2000.",
            "team": best_home,
        })

    # Worst away record
    away_pct = {t: r["w"] / (r["w"] + r["d"] + r["l"])
                for t, r in away_record.items()
                if r["w"] + r["d"] + r["l"] >= 100}
    if away_pct:
        best_away = max(away_pct, key=away_pct.get)
        pct = round(away_pct[best_away] * 100, 1)
        others = sorted(away_pct, key=away_pct.get, reverse=True)[1:4]
        questions.append({
            "category": "stats",
            "difficulty": "medium",
            "question": "Which team has the best away win percentage in the Premier League (since 2000)?",
            "correct_answer": best_away,
            "wrong_answers": list(others),
            "explanation": f"{best_away} have won {pct}% of their away PL matches since 2000.",
            "team": best_away,
        })

    return questions


def gen_draw_specialists(matches):
    """Questions about draws."""
    questions = []

    draw_counts = defaultdict(int)
    total_counts = defaultdict(int)

    for m in matches:
        home, away, res = m[1], m[2], m[5]
        total_counts[home] += 1
        total_counts[away] += 1
        if res == "D":
            draw_counts[home] += 1
            draw_counts[away] += 1

    draw_pct = {t: draw_counts[t] / total_counts[t]
                for t in total_counts if total_counts[t] >= 100}

    if draw_pct:
        most_draws = max(draw_pct, key=draw_pct.get)
        pct = round(draw_pct[most_draws] * 100, 1)
        count = draw_counts[most_draws]
        others = sorted(draw_pct, key=draw_pct.get, reverse=True)[1:4]
        questions.append({
            "category": "stats",
            "difficulty": "hard",
            "question": "Which Premier League team draws the most matches (highest draw percentage since 2000)?",
            "correct_answer": most_draws,
            "wrong_answers": list(others),
            "explanation": f"{most_draws} have drawn {pct}% of their PL matches ({count} draws total).",
            "team": most_draws,
        })

    return questions


def gen_scoreline_questions(matches):
    """Questions about specific scorelines."""
    questions = []

    scorelines = defaultdict(int)
    for m in matches:
        fh, fa = m[3], m[4]
        if fh is not None and fa is not None:
            scorelines[(fh, fa)] += 1

    sorted_scores = sorted(scorelines.items(), key=lambda x: x[1], reverse=True)

    # Most common scoreline
    (h, a), count = sorted_scores[0]
    total = sum(scorelines.values())
    pct = round(count / total * 100, 1)
    wrongs = [f"{sorted_scores[1][0][0]}-{sorted_scores[1][0][1]}",
              f"{sorted_scores[2][0][0]}-{sorted_scores[2][0][1]}",
              f"{sorted_scores[3][0][0]}-{sorted_scores[3][0][1]}"]
    questions.append({
        "category": "stats",
        "difficulty": "medium",
        "question": "What is the most common scoreline in Premier League history?",
        "correct_answer": f"{h}-{a}",
        "wrong_answers": wrongs,
        "explanation": f"{h}-{a} has occurred {count} times ({pct}% of all PL matches since 2000).",
        "team": None,
    })

    # 0-0 draws
    nil_nil = scorelines.get((0, 0), 0)
    pct_nn = round(nil_nil / total * 100, 1)
    wrongs = [f"{pct_nn + 2}%", f"{pct_nn - 2}%", f"{pct_nn + 5}%"]
    questions.append({
        "category": "stats",
        "difficulty": "hard",
        "question": "What percentage of Premier League matches (since 2000) have ended 0-0?",
        "correct_answer": f"{pct_nn}%",
        "wrong_answers": wrongs,
        "explanation": f"{nil_nil} out of {total} PL matches have ended goalless ({pct_nn}%).",
        "team": None,
    })

    return questions


def gen_derby_records(matches):
    """Questions about derby/rivalry match records."""
    questions = []

    DERBIES = {
        ("Arsenal", "Tottenham"): "North London Derby",
        ("Liverpool", "Everton"): "Merseyside Derby",
        ("Man United", "Man City"): "Manchester Derby",
        ("Man United", "Liverpool"): "North-West Derby",
        ("Arsenal", "Chelsea"): "London Derby",
        ("Crystal Palace", "Brighton"): "M23 Derby",
        ("Newcastle", "Sunderland"): "Tyne-Wear Derby",
        ("Tottenham", "Chelsea"): "London Derby",
        ("West Ham", "Tottenham"): "London Derby",
        ("Aston Villa", "Wolves"): "West Midlands Derby",
    }

    h2h = defaultdict(lambda: {"home_wins": 0, "away_wins": 0, "draws": 0, "goals": 0, "matches": 0})

    for m in matches:
        home, away, fh, fa, res = m[1], m[2], m[3], m[4], m[5]
        key = tuple(sorted([home, away]))
        if key not in [(tuple(sorted(k))) for k in DERBIES.keys()]:
            continue

        h2h[key]["matches"] += 1
        if fh is not None:
            h2h[key]["goals"] += fh + (fa or 0)
        if res == "H":
            h2h[key]["home_wins"] += 1
        elif res == "A":
            h2h[key]["away_wins"] += 1
        else:
            h2h[key]["draws"] += 1

    for (t1, t2), name in DERBIES.items():
        key = tuple(sorted([t1, t2]))
        rec = h2h.get(key)
        if not rec or rec["matches"] < 5:
            continue

        total = rec["matches"]
        avg_goals = round(rec["goals"] / total, 1) if total > 0 else 0

        questions.append({
            "category": "rivalries",
            "difficulty": "medium",
            "question": f"How many Premier League {name} matches have there been between {t1} and {t2} since 2000?",
            "correct_answer": str(total),
            "wrong_answers": [str(total - 5), str(total + 4), str(total - 9)],
            "explanation": f"The {name} has been played {total} times since 2000 ({rec['home_wins']}H, {rec['draws']}D, {rec['away_wins']}A, avg {avg_goals} goals/game).",
            "team": t1,
        })

    return questions


def gen_fact_trivia(conn):
    """Generate trivia from kb_facts table."""
    questions = []

    facts = conn.execute("SELECT content FROM kb_facts WHERE content LIKE '%scored%goal%' OR content LIKE '%won%' OR content LIKE '%trophy%' OR content LIKE '%record%' LIMIT 30").fetchall()

    # True/false style questions from verified facts
    for (fact,) in facts[:15]:
        if len(fact) < 30 or len(fact) > 150:
            continue
        # Skip messy facts with formatting artifacts
        if "(" in fact[:5] or "List of" in fact or "\n" in fact:
            continue
        questions.append({
            "category": "legends",
            "difficulty": "easy",
            "question": f"True or false: {fact}",
            "correct_answer": "True",
            "wrong_answers": ["False", "Partially true", "Unverified"],
            "explanation": fact,
            "team": None,
        })

    return questions


# ─── Helpers ──────────────────────────────────────────────────────


def _score_distractors(home, away):
    """Generate plausible wrong scorelines."""
    distractors = set()
    for dh in range(-2, 3):
        for da in range(-2, 3):
            s = f"{max(0, home + dh)}-{max(0, away + da)}"
            if s != f"{home}-{away}":
                distractors.add(s)
    return random.sample(sorted(distractors), min(3, len(distractors)))


def resolve_team_id(team_name, team_id_map):
    """Resolve match_history team name to teams table ID."""
    db_name = TEAM_NAME_MAP.get(team_name, team_name)
    return team_id_map.get(db_name)


# ─── Main ─────────────────────────────────────────────────────────


def main():
    apply = "--apply" in sys.argv
    clear_old = "--clear-old" in sys.argv

    print("=" * 60)
    print("  Soccer-AI Trivia Generator")
    print("=" * 60)

    # Load data
    unified_conn = sqlite3.connect(str(UNIFIED_DB))
    unified_conn.row_factory = sqlite3.Row
    main_conn = sqlite3.connect(str(MAIN_DB))
    main_conn.row_factory = sqlite3.Row

    team_id_map = get_team_id_map(main_conn)
    print(f"  Teams in DB: {len(team_id_map)}")

    matches = load_match_data(unified_conn)
    print(f"  PL matches loaded: {len(matches)}")

    # Generate all categories
    all_questions = []

    generators = [
        ("Biggest Wins", gen_biggest_wins),
        ("Head-to-Head Dominance", gen_head2head_dominance),
        ("Comebacks", gen_comebacks),
        ("Season Records", gen_season_records),
        ("ELO Ratings", gen_elo_questions),
        ("Ground Records", gen_ground_records),
        ("Draw Specialists", gen_draw_specialists),
        ("Scoreline Stats", gen_scoreline_questions),
        ("Derby Records", gen_derby_records),
    ]

    for name, gen_fn in generators:
        qs = gen_fn(matches)
        print(f"  {name}: {len(qs)} questions")
        all_questions.extend(qs)

    # Fact-based trivia
    fact_qs = gen_fact_trivia(unified_conn)
    print(f"  KB Facts: {len(fact_qs)} questions")
    all_questions.extend(fact_qs)

    unified_conn.close()

    # Deduplicate by question text
    seen = set()
    unique = []
    for q in all_questions:
        key = q["question"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(q)

    print(f"\n  Total unique questions: {len(unique)}")

    # Category breakdown
    cats = defaultdict(int)
    diffs = defaultdict(int)
    for q in unique:
        cats[q["category"]] += 1
        diffs[q["difficulty"]] += 1
    print("  By category:", dict(cats))
    print("  By difficulty:", dict(diffs))

    if not apply:
        print("\n  [DRY RUN] Pass --apply to insert into database.")
        # Show 5 samples
        print("\n  Sample questions:")
        for q in random.sample(unique, min(5, len(unique))):
            print(f"    [{q['category']}/{q['difficulty']}] {q['question']}")
            print(f"      Answer: {q['correct_answer']}")
        main_conn.close()
        return

    # ─── Insert into DB ───────────────────────────────────────────
    existing_count = main_conn.execute("SELECT COUNT(*) FROM trivia_questions").fetchone()[0]

    if clear_old:
        main_conn.execute("DELETE FROM trivia_questions")
        print(f"\n  Cleared {existing_count} existing questions.")
        existing_count = 0

    # Get existing questions to avoid duplicates
    existing_qs = {r[0].lower() for r in main_conn.execute("SELECT question FROM trivia_questions").fetchall()}

    inserted = 0
    for q in unique:
        if q["question"].lower() in existing_qs:
            continue

        team_id = None
        if q.get("team"):
            team_id = resolve_team_id(q["team"], team_id_map)

        wrong_json = json.dumps(q["wrong_answers"])

        main_conn.execute(
            """INSERT INTO trivia_questions
               (team_id, category, difficulty, question, correct_answer,
                wrong_answers, explanation, times_asked, times_correct, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?)""",
            (team_id, q["category"], q["difficulty"], q["question"],
             q["correct_answer"], wrong_json, q["explanation"],
             datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        )
        inserted += 1

    main_conn.commit()

    final_count = main_conn.execute("SELECT COUNT(*) FROM trivia_questions").fetchone()[0]
    main_conn.close()

    print(f"\n  Inserted: {inserted} new questions")
    print(f"  Total now: {final_count} (was {existing_count})")
    print("  Done!")


if __name__ == "__main__":
    main()
