#!/usr/bin/env python3
"""
Enrich the Knowledge Graph with iconic Premier League matches.
Focuses on underrepresented clubs and universally memorable moments.

Usage:
    python scripts/enrich_iconic_matches.py              # preview
    python scripts/enrich_iconic_matches.py --apply       # insert
"""

import sqlite3
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
UNIFIED_DB = BACKEND_DIR / "unified_soccer_ai_kg.db"

# ─── Iconic Matches Data ──────────────────────────────────────────
# Format: (name, node_type, description, properties_dict, edges)
# edges: list of (target_node_name, relationship)

ICONIC_MATCHES = [
    # === TITLE DECIDERS ===
    {
        "name": "Arsenal 4-2 Wigan Athletic 2002",
        "desc": "Arsenal clinched the Double at Highbury, with Freddie Ljungberg scoring twice.",
        "date": "2002-05-11", "score": "4-2", "competition": "Premier League",
        "teams": ["Arsenal", "Wigan Athletic"],
        "significance": "title_decider",
    },
    {
        "name": "Chelsea 8-0 Wigan 2010",
        "desc": "Chelsea clinched the 2009-10 Premier League title with an 8-0 demolition, also winning the Golden Boot for Drogba. Record title-winning scoreline.",
        "date": "2010-05-09", "score": "8-0", "competition": "Premier League",
        "teams": ["Chelsea"],
        "significance": "title_decider",
    },
    {
        "name": "Arsenal 2-1 Leicester 2004",
        "desc": "Arsenal completed the entire 2003-04 season unbeaten — The Invincibles. The only team to achieve this in modern PL history.",
        "date": "2004-05-15", "score": "2-1", "competition": "Premier League",
        "teams": ["Arsenal", "Leicester"],
        "significance": "title_decider",
    },

    # === EVERTON ===
    {
        "name": "Everton 3-2 Watford FA Cup Semi-Final 1984",
        "desc": "Everton came from behind to beat Watford and reach the FA Cup final, a defining moment in their mid-80s golden era.",
        "date": "1984-04-14", "score": "3-2", "competition": "FA Cup",
        "teams": ["Everton"],
        "significance": "cup_classic",
    },
    {
        "name": "Everton 1-0 Manchester United 1995 FA Cup Final",
        "desc": "Paul Rideout's goal sealed a shock FA Cup win over favourites United. One of Everton's most celebrated modern trophies.",
        "date": "1995-05-20", "score": "1-0", "competition": "FA Cup Final",
        "teams": ["Everton", "Manchester United"],
        "significance": "cup_final",
    },
    {
        "name": "Everton 3-2 Liverpool Merseyside Derby 2001",
        "desc": "A dramatic Merseyside Derby comeback. Everton trailed 2-0 before three goals in 10 minutes turned it around.",
        "date": "2001-09-15", "score": "3-2", "competition": "Premier League",
        "teams": ["Everton", "Liverpool"],
        "significance": "derby_classic",
    },

    # === WEST HAM ===
    {
        "name": "West Ham 3-3 Manchester United FA Cup Final 2016",
        "desc": "A thrilling FA Cup Final where West Ham twice came from behind before United won in extra time. Winston Reid's injury-time equaliser was dramatic.",
        "date": "2016-05-21", "score": "3-3", "competition": "FA Cup Final",
        "teams": ["West Ham", "Manchester United"],
        "significance": "cup_final",
    },
    {
        "name": "West Ham 3-2 Manchester United 2001",
        "desc": "Paolo Di Canio's stunning scissor-kick volley, one of the greatest ever PL goals, sealed a famous win.",
        "date": "2001-03-26", "score": "3-2", "competition": "Premier League",
        "teams": ["West Ham", "Manchester United"],
        "significance": "iconic_goal",
    },
    {
        "name": "West Ham 2-1 Fiorentina Europa Conference League Final 2023",
        "desc": "West Ham won their first European trophy in 58 years. Jarrod Bowen scored the winner in Prague.",
        "date": "2023-06-07", "score": "2-1", "competition": "Europa Conference League Final",
        "teams": ["West Ham"],
        "significance": "european_final",
    },

    # === ASTON VILLA ===
    {
        "name": "Aston Villa 1-0 Bayern Munich European Cup Final 1982",
        "desc": "Villa's greatest night. Peter Withe scored the only goal as unfancied Villa became European Champions.",
        "date": "1982-05-26", "score": "1-0", "competition": "European Cup Final",
        "teams": ["Aston Villa"],
        "significance": "european_final",
    },
    {
        "name": "Aston Villa 7-2 Liverpool 2020",
        "desc": "A stunning demolition of the reigning champions. Ollie Watkins scored a hat-trick as Villa ran riot.",
        "date": "2020-10-04", "score": "7-2", "competition": "Premier League",
        "teams": ["Aston Villa", "Liverpool"],
        "significance": "giant_killing",
    },

    # === LEEDS ===
    {
        "name": "Leeds United 3-2 Stuttgart UEFA Cup 1992",
        "desc": "Leeds won the last First Division title before the Premier League era. Howard Wilkinson's side ended a 18-year wait.",
        "date": "1992-04-26", "score": "N/A", "competition": "First Division",
        "teams": ["Leeds"],
        "significance": "title_decider",
    },
    {
        "name": "Leeds United 4-3 Liverpool 2021",
        "desc": "A breathtaking see-saw match at Elland Road. Diego Llorente equalised in the last minute for a classic PL draw... or was it? Sadio Mane made it 4-3.",
        "date": "2021-09-12", "score": "0-3 to 3-3", "competition": "Premier League",
        "teams": ["Leeds", "Liverpool"],
        "significance": "classic",
    },

    # === SUNDERLAND ===
    {
        "name": "Sunderland 4-1 Chelsea 2014",
        "desc": "A stunning upset as relegation-threatened Sunderland hammered title-chasing Chelsea. Fabio Borini was the hero.",
        "date": "2014-04-19", "score": "4-1", "competition": "Premier League",
        "teams": ["Sunderland", "Chelsea"],
        "significance": "giant_killing",
    },
    {
        "name": "Sunderland 3-0 Everton 'Great Escape' 2014",
        "desc": "Sunderland sealed the greatest PL survival by beating their rivals on the final day. Connor Wickham's brace sent the Stadium of Light into delirium.",
        "date": "2014-05-11", "score": "3-0", "competition": "Premier League",
        "teams": ["Sunderland", "Everton"],
        "significance": "great_escape",
    },

    # === CRYSTAL PALACE ===
    {
        "name": "Crystal Palace 3-3 Liverpool 2014",
        "desc": "Palace came from 3-0 down with 12 minutes left to draw 3-3, effectively ending Liverpool's title hopes. Dwight Gayle scored twice.",
        "date": "2014-05-05", "score": "3-3", "competition": "Premier League",
        "teams": ["Crystal Palace", "Liverpool"],
        "significance": "title_decider",
    },
    {
        "name": "Crystal Palace 1-2 Manchester United FA Cup Final 2016",
        "desc": "A dramatic final where Jason Puncheon scored a screamer before Jesse Lingard's volley won it for United in extra time.",
        "date": "2016-05-21", "score": "1-2", "competition": "FA Cup Final",
        "teams": ["Crystal Palace", "Manchester United"],
        "significance": "cup_final",
    },

    # === BRIGHTON ===
    {
        "name": "Brighton 1-0 Manchester United 2023",
        "desc": "A famous win at Old Trafford, demonstrating Brighton's rise under Roberto De Zerbi. Pascal Gross scored the winner.",
        "date": "2023-09-16", "score": "1-0", "competition": "Premier League",
        "teams": ["Brighton", "Manchester United"],
        "significance": "giant_killing",
    },
    {
        "name": "Brighton 2-1 Manchester City 2023 FA Cup Semi",
        "desc": "Brighton reached their first-ever FA Cup Final by beating the Treble-chasers. One of the biggest upsets in modern cup football.",
        "date": "2023-04-22", "score": "2-1", "competition": "FA Cup Semi-Final",
        "teams": ["Brighton", "Manchester City"],
        "significance": "cup_classic",
    },

    # === WOLVES ===
    {
        "name": "Wolves 3-2 Manchester City 2019",
        "desc": "Wolves came from 2-0 down against the champions, Adama Traore scored a late winner. Nuno's team were fearless against the big clubs.",
        "date": "2019-12-27", "score": "3-2", "competition": "Premier League",
        "teams": ["Wolves", "Manchester City"],
        "significance": "comeback",
    },

    # === FULHAM ===
    {
        "name": "Fulham 4-1 Juventus Europa League 2010",
        "desc": "Fulham's miracle Europa League run. Down 3-1 on aggregate, they scored 4 goals (Dempsey, Zamora, Gera) for an incredible comeback to reach the semi-finals.",
        "date": "2010-03-18", "score": "4-1", "competition": "Europa League",
        "teams": ["Fulham"],
        "significance": "european_comeback",
    },

    # === BOURNEMOUTH ===
    {
        "name": "Bournemouth 4-3 Liverpool 2016",
        "desc": "A remarkable PL match where Bournemouth came from 3-1 down to beat Liverpool 4-3. Nathan Ake scored the 93rd-minute winner.",
        "date": "2016-12-04", "score": "4-3", "competition": "Premier League",
        "teams": ["Bournemouth", "Liverpool"],
        "significance": "comeback",
    },

    # === BURNLEY ===
    {
        "name": "Burnley 1-0 Manchester United 2020",
        "desc": "Chris Wood's goal at Old Trafford sealed a famous win for Sean Dyche's side, in a match where United fans chanted 'We want Glazers out'.",
        "date": "2020-01-22", "score": "1-0", "competition": "Premier League",
        "teams": ["Burnley", "Manchester United"],
        "significance": "giant_killing",
    },

    # === BRENTFORD ===
    {
        "name": "Brentford 4-0 Manchester United 2022",
        "desc": "Brentford's dream start: 4 goals in 35 minutes against United at the Gtech. Ivan Toney, Ben Mee, and Bryan Mbuemo ran riot. Erik ten Hag's worst night.",
        "date": "2022-08-13", "score": "4-0", "competition": "Premier League",
        "teams": ["Brentford", "Manchester United"],
        "significance": "giant_killing",
    },

    # === SOUTHAMPTON ===
    {
        "name": "Southampton 6-3 Manchester United 1996",
        "desc": "Egil Ostenstad scored a hat-trick as Southampton hammered United. One of the most iconic results of the 90s PL.",
        "date": "1996-10-26", "score": "6-3", "competition": "Premier League",
        "teams": ["Southampton", "Manchester United"],
        "significance": "classic",
    },

    # === IPSWICH ===
    {
        "name": "Ipswich Town 1-0 Inter Milan UEFA Cup 2002",
        "desc": "Ipswich's European adventure under George Burley saw them beat Inter Milan at Portman Road. Marcus Stewart's winner was a fairytale.",
        "date": "2001-11-08", "score": "1-0", "competition": "UEFA Cup",
        "teams": ["Ipswich"],
        "significance": "european_classic",
    },

    # === EXTRA CLASSICS (big clubs, not yet covered) ===
    {
        "name": "Leicester City 3-1 Everton Title Win 2016",
        "desc": "Leicester sealed the most improbable title win in sporting history. 5000-1 outsiders became champions under Claudio Ranieri.",
        "date": "2016-05-07", "score": "3-1", "competition": "Premier League",
        "teams": ["Leicester"],
        "significance": "title_decider",
    },
    {
        "name": "Tottenham 3-2 Ajax Champions League Semi-Final 2019",
        "desc": "Lucas Moura's 96th-minute hat-trick goal completed an incredible comeback from 3-0 down on aggregate. One of the great European nights.",
        "date": "2019-05-08", "score": "3-2", "competition": "Champions League Semi-Final",
        "teams": ["Tottenham"],
        "significance": "european_classic",
    },
]


def get_next_id(conn):
    """Get next available match node ID."""
    max_id = conn.execute(
        "SELECT MAX(CAST(SUBSTR(id, 6) AS INTEGER)) FROM nodes WHERE id LIKE 'match_%'"
    ).fetchone()[0]
    return (max_id or 0) + 1


def main():
    apply = "--apply" in sys.argv

    conn = sqlite3.connect(str(UNIFIED_DB))

    # Get existing match names to avoid duplicates
    existing = {r[0].lower() for r in conn.execute(
        "SELECT name FROM nodes WHERE node_type IN ('match', 'moment')"
    ).fetchall()}

    print("=" * 60)
    print("  Iconic Matches Enrichment")
    print("=" * 60)
    print(f"  Existing match/moment nodes: {len(existing)}")
    print(f"  Candidate matches: {len(ICONIC_MATCHES)}")

    new_matches = []
    for match in ICONIC_MATCHES:
        if match["name"].lower() not in existing:
            new_matches.append(match)

    print(f"  New (not duplicated): {len(new_matches)}")

    if not new_matches:
        print("  Nothing to add!")
        conn.close()
        return

    # Show what we'll add
    teams_covered = set()
    for m in new_matches:
        teams_covered.update(m.get("teams", []))
        print(f"  + {m['name']} [{m['significance']}]")

    print(f"\n  Teams covered by new additions: {sorted(teams_covered)}")

    if not apply:
        print("\n  [DRY RUN] Pass --apply to insert.")
        conn.close()
        return

    # Insert nodes and edges
    next_id = get_next_id(conn)
    inserted_nodes = 0
    inserted_edges = 0

    for match in new_matches:
        node_id = f"match_{next_id}"
        next_id += 1

        props = json.dumps({
            "date": match.get("date"),
            "score": match.get("score"),
            "competition": match.get("competition"),
            "significance": match.get("significance"),
            "teams": match.get("teams", []),
        })

        conn.execute(
            """INSERT INTO nodes (id, name, node_type, description, properties, source_db)
               VALUES (?, ?, 'match', ?, ?, 'enrichment')""",
            (node_id, match["name"], match["desc"], props),
        )
        inserted_nodes += 1

        # Create edges to team nodes
        for team_name in match.get("teams", []):
            # Find team node
            team_node = conn.execute(
                "SELECT id FROM nodes WHERE node_type IN ('club', 'team') AND name LIKE ?",
                (f"%{team_name}%",),
            ).fetchone()

            if team_node:
                conn.execute(
                    """INSERT INTO edges (source_id, target_id, relationship, weight, properties, source_db)
                       VALUES (?, ?, 'iconic_match_for', 1.0, '{}', 'enrichment')""",
                    (node_id, team_node[0]),
                )
                inserted_edges += 1

    conn.commit()

    # Final count
    total = conn.execute("SELECT COUNT(*) FROM nodes WHERE node_type='match'").fetchone()[0]
    conn.close()

    print(f"\n  Inserted: {inserted_nodes} match nodes, {inserted_edges} team edges")
    print(f"  Total match nodes now: {total}")
    print("  Done!")


if __name__ == "__main__":
    main()
