"""
Soccer-AI RAG Module
Retrieval Augmented Generation - extracts relevant context from database

Enhanced with 500-node Knowledge Graph (Dec 2024)
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import database

# Import 500-node KG integration
try:
    from kg_integration import get_kg
    KG_AVAILABLE = True
except ImportError:
    KG_AVAILABLE = False

# Import new enhanced components (Dec 2024)
try:
    from mood_engine import get_mood_engine
    from match_insights import get_match_insights
    from football_api import get_football_api
    ENHANCED_COMPONENTS = True
except ImportError:
    ENHANCED_COMPONENTS = False


# ============================================
# ENTITY EXTRACTION
# ============================================

# Common team name variations
TEAM_ALIASES = {
    "man utd": "Manchester United",
    "man united": "Manchester United",
    "united": "Manchester United",
    "man city": "Manchester City",
    "city": "Manchester City",
    "liverpool": "Liverpool",
    "arsenal": "Arsenal",
    "gunners": "Arsenal",
    "chelsea": "Chelsea",
    "blues": "Chelsea",
    "spurs": "Tottenham",
    "tottenham": "Tottenham",
    "barca": "Barcelona",
    "barcelona": "Barcelona",
    "real": "Real Madrid",
    "real madrid": "Real Madrid",
    "bayern": "Bayern Munich",
    "psg": "Paris Saint-Germain",
}

# Time expressions
TIME_PATTERNS = {
    "yesterday": -1,
    "today": 0,
    "tomorrow": 1,
    "last week": -7,
    "this week": 0,
    "last game": -1,  # Contextual
    "recent": -7,
    "latest": -3,
}


def deduplicate_sources(sources: List[Dict]) -> List[Dict]:
    """
    Remove duplicate sources from the list.
    Uses (type, id) as unique key. For sources without ID, uses (type, name/rival) or just (type, None).
    Bug fix: Insight #930 - Duplicate sources in hybrid RAG
    """
    seen = set()
    unique = []

    for source in sources:
        source_type = source.get("type", "unknown")
        source_id = source.get("id")
        source_name = source.get("name", "")
        source_rival = source.get("rival", "")

        if source_id is not None:
            # Use type + id as key
            key = (source_type, "id", source_id)
        elif source_name:
            # Use type + name as key (for named entities like legends)
            key = (source_type, "name", source_name)
        elif source_rival:
            # Use type + rival as key (for rivalries)
            key = (source_type, "rival", source_rival)
        else:
            # For sources with no identifying info, dedupe by type only (keep first)
            key = (source_type, "none", None)

        if key not in seen:
            seen.add(key)
            unique.append(source)

    return unique


def extract_entities(query: str) -> Dict[str, Any]:
    """
    Extract entities from natural language query.
    Returns dict with: teams, players, dates, intent
    """
    query_lower = query.lower()
    entities = {
        "teams": [],
        "players": [],
        "dates": [],
        "intent": detect_intent(query_lower),
        "raw_query": query
    }

    # Extract team mentions
    for alias, full_name in TEAM_ALIASES.items():
        if alias in query_lower:
            entities["teams"].append(full_name)

    # Extract time references
    for pattern, days_delta in TIME_PATTERNS.items():
        if pattern in query_lower:
            target_date = datetime.now() + timedelta(days=days_delta)
            entities["dates"].append(target_date.strftime("%Y-%m-%d"))

    # If no specific date, check for date patterns (e.g., "December 18")
    date_match = re.search(r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(\d{4}))?', query)
    if date_match:
        try:
            month_str = date_match.group(1)
            day = int(date_match.group(2))
            year = int(date_match.group(3)) if date_match.group(3) else datetime.now().year
            month = datetime.strptime(month_str, "%B").month
            entities["dates"].append(f"{year}-{month:02d}-{day:02d}")
        except ValueError:
            pass

    # Try to find player names via FTS search
    # Extract potential player names (capitalized words not matching teams)
    words = query.split()
    potential_names = []
    for i, word in enumerate(words):
        if word[0].isupper() and word.lower() not in TEAM_ALIASES:
            # Could be a player name - try to combine with next word
            if i + 1 < len(words) and words[i + 1][0].isupper():
                potential_names.append(f"{word} {words[i + 1]}")
            else:
                potential_names.append(word)

    # Verify player names against database
    for name in potential_names:
        players = database.search_players(name, limit=1)
        if players:
            entities["players"].append(players[0])

    return entities


def detect_intent(query: str) -> str:
    """
    Detect the intent of the query.
    Returns: score, injury, transfer, fixture, standing, player_info, team_info, general

    Enhancement: Added keywords for better standing detection
    - "top", "leading", "first place", "last place", "bottom", "relegation"
    Bug fix: Prioritize standing queries over player_info for "who is top" type queries
    """
    query = query.lower()

    # Score/result queries
    if any(word in query for word in ["score", "result", "won", "lost", "draw", "played", "beat"]):
        return "score"

    # Injury queries
    if any(word in query for word in ["injury", "injured", "hurt", "fitness", "sidelined", "out"]):
        return "injury"

    # Transfer queries
    if any(word in query for word in ["transfer", "sign", "buy", "sell", "loan", "rumor", "deal"]):
        return "transfer"

    # Fixture/schedule queries - ENHANCED
    # Check phrases first (multi-word), then single words
    fixture_phrases = [
        "games today", "games tomorrow", "matches today", "matches tomorrow",
        "playing next", "next game", "this weekend", "next week", "upcoming games",
        "what games", "which games", "any games", "today's games", "tomorrow's games"
    ]
    fixture_words = ["fixture", "fixtures", "schedule", "upcoming"]

    if any(phrase in query for phrase in fixture_phrases):
        return "fixture"
    if any(word in query for word in fixture_words):
        return "fixture"

    # Standing/table queries - ENHANCED with more keywords
    standing_keywords = [
        "standing", "table", "position", "rank", "points",
        "top of", "leading", "leader", "first place", "1st place",
        "last place", "bottom", "relegated", "relegation zone",
        "top 4", "top four", "champions league places",
        "league table", "how many points"
    ]
    if any(word in query for word in standing_keywords):
        return "standing"

    # Stats queries
    if any(word in query for word in ["stats", "goals", "assists", "top scorer", "most", "average"]):
        return "stats"

    # Player info
    if any(word in query for word in ["who is", "tell me about", "player"]):
        return "player_info"

    # Team info
    if any(word in query for word in ["team", "squad", "roster", "club"]):
        return "team_info"

    return "general"


# ============================================
# CONTEXT RETRIEVAL
# ============================================

def retrieve_context(query: str) -> Tuple[str, List[Dict]]:
    """
    Main RAG function. Retrieves relevant context for the query.
    Returns: (formatted_context, source_references)
    """
    entities = extract_entities(query)
    intent = entities["intent"]
    context_parts = []
    sources = []

    # Route to appropriate retrieval based on intent
    if intent == "score":
        ctx, src = retrieve_score_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "injury":
        ctx, src = retrieve_injury_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "transfer":
        ctx, src = retrieve_transfer_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "fixture":
        ctx, src = retrieve_fixture_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "standing":
        ctx, src = retrieve_standing_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "stats":
        ctx, src = retrieve_stats_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "player_info":
        ctx, src = retrieve_player_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    elif intent == "team_info":
        ctx, src = retrieve_team_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    else:
        # General query - search everything
        ctx, src = retrieve_general_context(entities)
        context_parts.append(ctx)
        sources.extend(src)

    # Also search news for additional context
    news_ctx, news_src = retrieve_news_context(entities)
    if news_ctx:
        context_parts.append(news_ctx)
        sources.extend(news_src)

    return "\n\n".join(filter(None, context_parts)), sources


def retrieve_score_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """
    Retrieve game score/result context.

    Enhancement: Show all recent scores when no specific team mentioned
    - "What were yesterday's scores?" → Show yesterday's results
    - "Latest results" → Show recent finished games
    """
    context_lines = []
    sources = []

    query_lower = entities.get("raw_query", "").lower()

    # If specific team(s) mentioned
    if entities.get("teams"):
        for team_name in entities["teams"]:
            team = database.get_team_by_name(team_name)
            if not team:
                continue

            # Get recent games
            if entities.get("dates"):
                # Specific date
                games = database.get_games(
                    team_id=team["id"],
                    date_from=entities["dates"][0],
                    date_to=entities["dates"][0],
                    limit=5
                )
            else:
                # Recent games
                games = database.get_recent_games(team["id"], limit=3)

            for game in games:
                home = game["home_team_name"]
                away = game["away_team_name"]
                score = f"{game.get('home_score', '?')}-{game.get('away_score', '?')}"
                date = game["date"]
                status = game["status"]

                if status == "finished":
                    context_lines.append(
                        f"Game on {date}: {home} {score} {away} at {game.get('venue', 'unknown venue')}"
                    )
                else:
                    context_lines.append(
                        f"Upcoming game on {date}: {home} vs {away} ({status})"
                    )

                sources.append({"type": "game", "id": game["id"]})

                # Get events if available
                if game.get("events"):
                    for event in game["events"]:
                        if event["event_type"] == "goal":
                            context_lines.append(
                                f"  - Goal: {event['player_name']} ({event['minute']}')"
                            )

    # No specific team - show recent scores
    else:
        # Determine target date
        target_date = None
        date_desc = None
        if "yesterday" in query_lower:
            target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            date_desc = "yesterday"
        elif "today" in query_lower:
            target_date = datetime.now().strftime("%Y-%m-%d")
            date_desc = "today"
        elif entities.get("dates") and ("latest" not in query_lower and "recent" not in query_lower):
            # Only use extracted date if not asking for "latest/recent" (which should show all recent games)
            target_date = entities["dates"][0]
            date_desc = target_date

        # Get games for target date
        if target_date:
            # Use get_games with date filter
            games = database.get_games(date_from=target_date, date_to=target_date, status="finished", limit=20)
            if games:
                context_lines.append(f"Results from {date_desc}:")
                for game in games:
                    score = f"{game.get('home_score', '?')}-{game.get('away_score', '?')}"
                    context_lines.append(
                        f"  - {game['home_team_name']} {score} {game['away_team_name']}"
                    )
                    sources.append({"type": "game", "id": game["id"]})
            else:
                # No games on that date - show most recent instead
                games = database.get_games(status="finished", limit=5)
                if games:
                    context_lines.append(f"No games on {date_desc}. Most recent results:")
                    for game in games:
                        score = f"{game.get('home_score', '?')}-{game.get('away_score', '?')}"
                        context_lines.append(
                            f"  - {game['date']}: {game['home_team_name']} {score} {game['away_team_name']}"
                        )
                        sources.append({"type": "game", "id": game["id"]})
        else:
            # Show recent finished games - order by date descending
            games = database.get_games(status="finished", limit=10)
            if games:
                context_lines.append("Recent Premier League results:")
                for game in games:
                    score = f"{game.get('home_score', '?')}-{game.get('away_score', '?')}"
                    context_lines.append(
                        f"  - {game['date']}: {game['home_team_name']} {score} {game['away_team_name']}"
                    )
                    sources.append({"type": "game", "id": game["id"]})

    return "\n".join(context_lines), sources


def retrieve_injury_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve injury context."""
    context_lines = []
    sources = []

    # Get injuries for mentioned teams
    for team_name in entities.get("teams", []):
        team = database.get_team_by_name(team_name)
        if team:
            injuries = database.get_injuries(team_id=team["id"], status="active")
            if injuries:
                context_lines.append(f"Current injuries for {team_name}:")
                for injury in injuries:
                    context_lines.append(
                        f"  - {injury['player_name']}: {injury['injury_type']} "
                        f"({injury['severity']}), expected return: {injury.get('expected_return', 'unknown')}"
                    )
                    sources.append({"type": "injury", "id": injury["id"]})

    # Get injuries for mentioned players
    for player in entities.get("players", []):
        injuries = database.get_injuries(status="active")
        player_injuries = [i for i in injuries if i["player_id"] == player["id"]]
        for injury in player_injuries:
            context_lines.append(
                f"{player['name']} injury: {injury['injury_type']} ({injury['severity']})"
            )
            sources.append({"type": "injury", "id": injury["id"]})

    # If no specific team/player, get all active injuries
    if not context_lines:
        injuries = database.get_injuries(status="active", limit=10)
        context_lines.append("Current active injuries:")
        for injury in injuries:
            context_lines.append(
                f"  - {injury['player_name']} ({injury['team_name']}): {injury['injury_type']}"
            )
            sources.append({"type": "injury", "id": injury["id"]})

    return "\n".join(context_lines), sources


def retrieve_transfer_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve transfer context."""
    context_lines = []
    sources = []

    for team_name in entities.get("teams", []):
        team = database.get_team_by_name(team_name)
        if team:
            transfers = database.get_transfers(team_id=team["id"], limit=10)
            if transfers:
                context_lines.append(f"Recent transfers involving {team_name}:")
                for transfer in transfers:
                    direction = "to" if transfer["to_team_id"] == team["id"] else "from"
                    other_team = transfer["from_team_name"] if direction == "to" else transfer["to_team_name"]
                    fee = f"€{transfer['fee_eur']:,}" if transfer.get("fee_eur") else "undisclosed"
                    context_lines.append(
                        f"  - {transfer['player_name']}: {direction} {other_team} ({transfer['transfer_type']}, {fee})"
                    )
                    sources.append({"type": "transfer", "id": transfer["id"]})

    # Check for transfer rumors
    rumors = database.get_transfers(status="rumor", limit=5)
    if rumors:
        context_lines.append("\nRecent transfer rumors:")
        for rumor in rumors:
            context_lines.append(
                f"  - {rumor['player_name']}: {rumor['from_team_name']} → {rumor['to_team_name']} (rumored)"
            )
            sources.append({"type": "transfer", "id": rumor["id"]})

    return "\n".join(context_lines), sources


def retrieve_fixture_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """
    Retrieve upcoming fixture context.

    Enhancement: Show all upcoming games when no specific team mentioned
    - "What games are today?" → Show today's fixtures
    - "Fixtures this weekend" → Show upcoming games
    """
    context_lines = []
    sources = []

    query_lower = entities.get("raw_query", "").lower()

    # If specific team(s) mentioned
    if entities.get("teams"):
        for team_name in entities["teams"]:
            team = database.get_team_by_name(team_name)
            if team:
                fixtures = database.get_upcoming_games(team["id"], limit=5)
                if fixtures:
                    context_lines.append(f"Upcoming games for {team_name}:")
                    for game in fixtures:
                        opponent = game["away_team_name"] if game["home_team_id"] == team["id"] else game["home_team_name"]
                        venue = "home" if game["home_team_id"] == team["id"] else "away"
                        context_lines.append(
                            f"  - {game['date']}: vs {opponent} ({venue})"
                        )
                        sources.append({"type": "game", "id": game["id"]})

    # No specific team - show all upcoming games (filtered by date if specified)
    else:
        # Check for date/time context
        target_date = None
        if "today" in query_lower:
            target_date = datetime.now().strftime("%Y-%m-%d")
        elif "tomorrow" in query_lower:
            target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif entities.get("dates"):
            target_date = entities["dates"][0]

        # Get fixtures
        if target_date:
            # Use get_games with date filter
            games = database.get_games(date_from=target_date, date_to=target_date, status="scheduled", limit=20)
            if games:
                date_str = "today" if "today" in query_lower else target_date
                context_lines.append(f"Fixtures for {date_str}:")
                for game in games:
                    time_str = game.get('time', '')
                    status = game.get('status', 'scheduled')
                    context_lines.append(
                        f"  - {game['home_team_name']} vs {game['away_team_name']}"
                        f" ({time_str if time_str else status})"
                    )
                    sources.append({"type": "game", "id": game["id"]})
            else:
                # No games on exact date - show ALL scheduled games (don't filter by date)
                fixtures = database.get_games(status="scheduled", limit=10)
                if fixtures:
                    context_lines.append(f"No fixtures scheduled for {target_date}. Upcoming games:")
                    for game in fixtures[:8]:
                        context_lines.append(
                            f"  - {game['date']}: {game['home_team_name']} vs {game['away_team_name']}"
                        )
                        sources.append({"type": "game", "id": game["id"]})
                else:
                    # Truly no scheduled games - show recent past games
                    past_games = database.get_games(status="finished", limit=5)
                    if past_games:
                        context_lines.append(f"No upcoming fixtures. Most recent completed games:")
                        for game in past_games:
                            score = f"{game.get('home_score', '?')}-{game.get('away_score', '?')}"
                            context_lines.append(
                                f"  - {game['date']}: {game['home_team_name']} {score} {game['away_team_name']}"
                            )
                            sources.append({"type": "game", "id": game["id"]})
        else:
            # Show next few days of fixtures - use get_games with date filter
            today = datetime.now().strftime("%Y-%m-%d")
            fixtures = database.get_games(date_from=today, status="scheduled", limit=10)
            if fixtures:
                context_lines.append("Upcoming Premier League fixtures:")
                for game in fixtures:
                    context_lines.append(
                        f"  - {game['date']}: {game['home_team_name']} vs {game['away_team_name']}"
                    )
                    sources.append({"type": "game", "id": game["id"]})

    return "\n".join(context_lines), sources


def retrieve_standing_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """
    Retrieve league standings context.

    Enhancement: Show full league table when no specific team mentioned
    - Detects "Premier League", "the league" in query
    - Shows top 10 if no team specified
    - Shows full context for specific team queries
    """
    context_lines = []
    sources = []

    query_lower = entities.get("raw_query", "").lower()

    # Detect league mentions in query
    league_name = None
    if "premier league" in query_lower or "epl" in query_lower or "the league" in query_lower:
        league_name = "Premier League"
    elif "la liga" in query_lower or "spanish" in query_lower:
        league_name = "La Liga"
    elif "serie a" in query_lower or "italian" in query_lower:
        league_name = "Serie A"
    elif "bundesliga" in query_lower or "german" in query_lower:
        league_name = "Bundesliga"
    elif "ligue 1" in query_lower or "french" in query_lower:
        league_name = "Ligue 1"

    # If specific team(s) mentioned, show team-specific context
    if entities.get("teams"):
        for team_name in entities["teams"]:
            team = database.get_team_by_name(team_name)
            if team:
                standings = database.get_standings(team["league"])
                team_standing = next((s for s in standings if s["team_id"] == team["id"]), None)
                if team_standing:
                    context_lines.append(
                        f"{team_name} in {team['league']}: "
                        f"Position {team_standing['position']}, "
                        f"{team_standing['points']} points, "
                        f"Form: {team_standing.get('form', 'N/A')}"
                    )
                    sources.append({"type": "standing", "team_id": team["id"]})

                    # Show nearby teams
                    pos = team_standing["position"]
                    nearby = [s for s in standings if abs(s["position"] - pos) <= 2]
                    context_lines.append("Nearby teams:")
                    for s in nearby:
                        context_lines.append(
                            f"  {s['position']}. {s['team_name']} - {s['points']} pts"
                        )

    # If no specific teams but league detected, show full table
    elif league_name:
        standings = database.get_standings(league_name)
        if standings:
            context_lines.append(f"{league_name} Standings (2024-25):")
            context_lines.append("")
            # Show top 10
            for s in standings[:10]:
                form = s.get('form', '')
                form_str = f" (Form: {form})" if form else ""
                context_lines.append(
                    f"{s['position']:2d}. {s['team_name']:20s} {s['points']:2d} pts "
                    f"| {s.get('played', 0)}P {s.get('won', 0)}W {s.get('drawn', 0)}D {s.get('lost', 0)}L{form_str}"
                )
                sources.append({"type": "standing", "team_id": s["team_id"]})

            # If query asks about "top" or "leading", emphasize leader
            if "top" in query_lower or "leading" in query_lower or "first" in query_lower:
                leader = standings[0]
                context_lines.insert(1, f"Current leader: {leader['team_name']} with {leader['points']} points\n")

    # Fallback: If nothing specific, show Premier League (default)
    elif not context_lines:
        standings = database.get_standings("Premier League")
        if standings:
            context_lines.append("Premier League Standings (2024-25) - Top 5:")
            context_lines.append("")
            for s in standings[:5]:
                context_lines.append(
                    f"{s['position']}. {s['team_name']} - {s['points']} pts"
                )
                sources.append({"type": "standing", "team_id": s["team_id"]})

    return "\n".join(context_lines), sources


def retrieve_stats_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve player/team statistics context."""
    context_lines = []
    sources = []

    for player in entities.get("players", []):
        stats = database.get_player_stats(player["id"])
        if stats:
            context_lines.append(
                f"{player['name']} season stats: "
                f"{stats.get('total_goals', 0)} goals, "
                f"{stats.get('total_assists', 0)} assists in "
                f"{stats.get('games', 0)} games"
            )
            sources.append({"type": "player_stats", "player_id": player["id"]})

    return "\n".join(context_lines), sources


def retrieve_player_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve player information context."""
    context_lines = []
    sources = []

    for player in entities.get("players", []):
        context_lines.append(
            f"{player['name']}: {player.get('position', 'Unknown')} for {player.get('team_name', 'Unknown')}, "
            f"Nationality: {player.get('nationality', 'Unknown')}"
        )
        sources.append({"type": "player", "id": player["id"]})

        # Add stats
        stats = database.get_player_stats(player["id"])
        if stats and stats.get("games", 0) > 0:
            context_lines.append(
                f"  Season: {stats.get('total_goals', 0)} goals, {stats.get('total_assists', 0)} assists"
            )

    return "\n".join(context_lines), sources


def retrieve_team_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve team information context."""
    context_lines = []
    sources = []

    for team_name in entities.get("teams", []):
        team = database.get_team_by_name(team_name)
        if team:
            context_lines.append(
                f"{team['name']}: {team['league']} ({team['country']}), "
                f"Stadium: {team.get('stadium', 'Unknown')}"
            )
            sources.append({"type": "team", "id": team["id"]})

            # Get standing
            standings = database.get_standings(team["league"])
            team_standing = next((s for s in standings if s["team_id"] == team["id"]), None)
            if team_standing:
                context_lines.append(
                    f"  Current position: {team_standing['position']} with {team_standing['points']} points"
                )

    return "\n".join(context_lines), sources


def retrieve_news_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve relevant news context."""
    context_lines = []
    sources = []

    # Build search query from entities
    search_terms = []
    search_terms.extend(entities.get("teams", []))
    search_terms.extend([p["name"] for p in entities.get("players", [])])

    if search_terms:
        search_query = " OR ".join(search_terms)
        news = database.search_news(search_query, limit=3)
        if news:
            context_lines.append("Related news:")
            for article in news:
                context_lines.append(f"  - {article['title']} ({article.get('source', 'Unknown')})")
                if article.get("summary"):
                    context_lines.append(f"    {article['summary']}")
                sources.append({"type": "news", "id": article["id"]})

    return "\n".join(context_lines), sources


def retrieve_general_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve context for general queries using FTS search."""
    context_lines = []
    sources = []

    # Use the raw query for FTS search
    query = entities.get("raw_query", "")
    if query:
        results = database.search_all(query, limit=3)

        if results["teams"]:
            context_lines.append("Teams found:")
            for team in results["teams"]:
                context_lines.append(f"  - {team['name']} ({team['league']})")
                sources.append({"type": "team", "id": team["id"]})

        if results["players"]:
            context_lines.append("Players found:")
            for player in results["players"]:
                context_lines.append(f"  - {player['name']} ({player.get('team_name', 'Unknown')})")
                sources.append({"type": "player", "id": player["id"]})

        if results["news"]:
            context_lines.append("Related news:")
            for article in results["news"]:
                context_lines.append(f"  - {article['title']}")
                sources.append({"type": "news", "id": article["id"]})

    return "\n".join(context_lines), sources


# ============================================
# KNOWLEDGE GRAPH ENHANCED RETRIEVAL (KG-RAG)
# Hybrid retrieval: FTS5 (β=0.60) + Graph (γ=0.40)
# ============================================

# Intent patterns that benefit from graph traversal
KG_INTENT_PATTERNS = {
    "multi_hop": ["best", "greatest", "iconic", "legendary", "famous", "memorable"],
    "relationship": ["compare", "vs", "versus", "rivalry", "between"],
    "discovery": ["connection", "related", "link", "any", "history with"],
    "emotional": ["feeling", "mood", "how are we", "atmosphere"],
}

# Legend and moment keywords for KG routing
LEGEND_KEYWORDS = ["legend", "legendary", "greatest", "icon", "hero", "hall of fame"]
MOMENT_KEYWORDS = ["moment", "memory", "derby", "classic", "famous", "iconic", "invincibles"]
RIVALRY_KEYWORDS = ["rival", "rivalry", "derby", "enemy", "hate", "spurs", "enemy"]


def detect_kg_intent(query: str) -> Optional[str]:
    """Detect if query would benefit from KG traversal."""
    query_lower = query.lower()

    # Priority order: specific intents first, then general

    # Check for rivalry-specific FIRST (most specific)
    if any(word in query_lower for word in RIVALRY_KEYWORDS):
        return "rivalry"

    # Check for moment-specific
    if any(word in query_lower for word in MOMENT_KEYWORDS):
        return "moment"

    # Check for legend-specific
    if any(word in query_lower for word in LEGEND_KEYWORDS):
        return "legend"

    # Check for emotional/mood queries
    if any(word in query_lower for word in KG_INTENT_PATTERNS["emotional"]):
        return "emotional"

    # Check for discovery queries
    if any(word in query_lower for word in KG_INTENT_PATTERNS["discovery"]):
        return "discovery"

    # Check for relationship queries
    if any(word in query_lower for word in KG_INTENT_PATTERNS["relationship"]):
        return "relationship"

    # Check for multi-hop queries (most general)
    if any(word in query_lower for word in KG_INTENT_PATTERNS["multi_hop"]):
        return "multi_hop"

    return None


def extract_kg_entities(query: str) -> Dict[str, Any]:
    """Extract entities and resolve them to KG nodes."""
    # Start with standard extraction
    entities = extract_entities(query)

    # Add KG-specific fields
    entities["kg_nodes"] = []
    entities["kg_intent"] = detect_kg_intent(query)

    # Resolve teams to KG nodes
    for team_name in entities.get("teams", []):
        node = database.find_kg_node_by_name(team_name)
        if node:
            entities["kg_nodes"].append(node)

    # Search for legends mentioned
    query_lower = query.lower()
    legends = database.get_legends(limit=100)
    for legend in legends:
        # Check if legend name is in query
        if legend["name"].lower() in query_lower:
            node = database.find_kg_node_by_name(legend["name"])
            if node:
                entities["kg_nodes"].append(node)

    return entities


def retrieve_kg_context(entities: Dict) -> Tuple[str, List[Dict]]:
    """Retrieve context from Knowledge Graph."""
    context_parts = []
    sources = []
    kg_intent = entities.get("kg_intent")

    for node in entities.get("kg_nodes", []):
        node_type = node["node_type"]
        entity_id = node["entity_id"]
        node_id = node["node_id"]

        # Get full entity context via graph traversal
        kg_ctx = database.get_entity_context(node_type, entity_id)

        if node_type == "team":
            # Team context
            context_parts.append(f"## {node['name']} Knowledge Graph")

            # Legends
            if kg_ctx.get("legends"):
                legend_names = [e["source_name"] for e in kg_ctx["legends"][:5]]
                context_parts.append(f"**Legends**: {', '.join(legend_names)}")
                sources.extend([{"type": "kg_legend", "name": n} for n in legend_names])

            # Rivalries
            if kg_ctx.get("rivalries"):
                for rival in kg_ctx["rivalries"]:
                    weight = rival.get("weight", 0)
                    intensity = "fierce" if weight >= 0.9 else "strong" if weight >= 0.7 else "notable"
                    context_parts.append(f"**Rivalry**: {intensity} with {rival['target_name']}")
                    sources.append({"type": "kg_rivalry", "rival": rival["target_name"]})

            # Iconic moments
            if kg_ctx.get("moments"):
                context_parts.append("**Iconic Moments**:")
                for moment in kg_ctx["moments"][:4]:
                    moment_node = database.get_kg_node(moment["source_id"])
                    if moment_node and moment_node.get("properties"):
                        props = moment_node["properties"]
                        emotion = props.get("emotion", "")
                        context_parts.append(f"  - {moment['source_name']} ({emotion})")
                        sources.append({"type": "kg_moment", "name": moment["source_name"]})

            # Current mood
            if kg_ctx.get("mood"):
                mood = kg_ctx["mood"]
                context_parts.append(f"**Current Mood**: {mood.get('current_mood', 'unknown')}")
                context_parts.append(f"  Reason: {mood.get('mood_reason', '')}")

        elif node_type == "legend":
            # Legend context
            context_parts.append(f"## Legend: {node['name']}")

            if node.get("properties"):
                props = node["properties"]
                if props.get("era"):
                    context_parts.append(f"**Era**: {props['era']}")
                if props.get("position"):
                    context_parts.append(f"**Position**: {props['position']}")

            # What team
            if kg_ctx.get("team"):
                team = kg_ctx["team"]
                context_parts.append(f"**Club**: {team['name']}")
                sources.append({"type": "kg_team", "name": team["name"]})

            # Multi-hop: get team's rivals (legend's rivalries by extension)
            if kg_intent == "relationship" or kg_intent == "rivalry":
                team_edges = database.get_kg_edges_from(node_id, "legendary_at")
                if team_edges:
                    team_node_id = team_edges[0]["target_id"]
                    rivals = database.get_kg_edges_from(team_node_id, "rival_of")
                    if rivals:
                        rival_names = [r["target_name"] for r in rivals]
                        context_parts.append(f"**Rivalries (via team)**: vs {', '.join(rival_names)}")

    # Special handling for rivalry queries
    if kg_intent == "rivalry" and len(entities.get("kg_nodes", [])) >= 1:
        team_node = next((n for n in entities["kg_nodes"] if n["node_type"] == "team"), None)
        if team_node:
            rivalries = database.get_club_rivalries(team_node["entity_id"])
            if rivalries:
                context_parts.append("\n## Rivalry Details")
                for rivalry in rivalries[:3]:
                    context_parts.append(f"**{rivalry['rival_name']}** ({rivalry['rivalry_type']})")
                    context_parts.append(f"  Intensity: {rivalry['intensity']}/10")
                    if rivalry.get("banter_phrases"):
                        phrases = rivalry["banter_phrases"][:2] if isinstance(rivalry["banter_phrases"], list) else []
                        if phrases:
                            context_parts.append(f"  Banter: {'; '.join(phrases)}")

    # Special handling for moment queries
    if kg_intent == "moment" and entities.get("kg_nodes"):
        team_node = next((n for n in entities["kg_nodes"] if n["node_type"] == "team"), None)
        if team_node:
            moments = database.get_club_moments(team_node["entity_id"], limit=5)
            if moments:
                context_parts.append("\n## Memorable Moments")
                for moment in moments:
                    context_parts.append(f"**{moment['title']}** ({moment.get('date', 'unknown')})")
                    if moment.get("description"):
                        context_parts.append(f"  {moment['description'][:200]}")
                    sources.append({"type": "kg_moment", "id": moment["id"]})

    return "\n".join(context_parts), sources


# ============================================
# CLUB PERSONA HELPERS
# ============================================

def get_team_id_by_name(club_name: str) -> Optional[int]:
    """Get team ID from club name (handles aliases)."""
    if not club_name:
        return None

    # Normalize the name
    normalized = club_name.lower().replace("_", " ").strip()

    # Check aliases first
    canonical = TEAM_ALIASES.get(normalized, normalized.title())

    # Query database for team
    teams = database.search_teams(canonical, limit=1)
    if teams:
        return teams[0]["id"]

    return None


def get_club_persona_context(club_name: str) -> Tuple[str, List[Dict]]:
    """
    Get rich context for a club persona.
    Returns identity, legends, rivalries, mood - everything needed for persona.
    """
    context_parts = []
    sources = []

    team_id = get_team_id_by_name(club_name)
    if not team_id:
        return "", []

    # Club identity
    identity = database.get_club_identity(team_id)
    if identity:
        context_parts.append(f"## Your Club: {identity.get('name', club_name)}")
        if identity.get("founded"):
            context_parts.append(f"**Founded**: {identity['founded']}")
        if identity.get("stadium"):
            context_parts.append(f"**Home**: {identity['stadium']}")
        if identity.get("nickname"):
            context_parts.append(f"**Known as**: {identity['nickname']}")
        if identity.get("philosophy"):
            context_parts.append(f"**Philosophy**: {identity['philosophy']}")
        sources.append({"type": "club_identity", "id": team_id})

    # Legends
    legends = database.get_legends(team_id, limit=5)
    if legends:
        context_parts.append("\n## Your Legends")
        for legend in legends:
            context_parts.append(f"- **{legend['name']}** ({legend.get('years', 'legend')})")
            if legend.get("nickname"):
                context_parts.append(f"  Known as: {legend['nickname']}")
        sources.append({"type": "legends", "id": team_id})

    # Rivalries
    rivalries = database.get_club_rivalries(team_id)
    if rivalries:
        context_parts.append("\n## Your Rivalries")
        for rivalry in rivalries[:3]:
            context_parts.append(f"- **{rivalry['rival_name']}** ({rivalry.get('rivalry_type', 'rivalry')})")
            context_parts.append(f"  Intensity: {rivalry.get('intensity', 5)}/10")
        sources.append({"type": "rivalries", "id": team_id})

    # Iconic moments
    moments = database.get_club_moments(team_id, limit=3)
    if moments:
        context_parts.append("\n## Iconic Moments")
        for moment in moments:
            context_parts.append(f"- **{moment['title']}**")
        sources.append({"type": "moments", "id": team_id})

    return "\n".join(context_parts), sources


def retrieve_hybrid(query: str, club: str = None) -> Tuple[str, List[Dict], Dict]:
    """
    Hybrid retrieval combining FTS5 + Knowledge Graph.
    Formula: β=0.60 (FTS5) + γ=0.40 (Graph)

    Enhanced with 500-node KG (Dec 2024) for deeper football knowledge.

    Args:
        query: User's question
        club: Optional club name for persona-aware retrieval (e.g., "arsenal", "chelsea")
    """
    # Extract entities with KG resolution
    entities = extract_kg_entities(query)

    # Get FTS5 context (standard RAG)
    fts_context, fts_sources = retrieve_context(query)

    # Get KG context from original KG
    kg_context, kg_sources = retrieve_kg_context(entities)

    # === ENHANCED: 500-node KG Integration ===
    enhanced_kg_context = ""
    if KG_AVAILABLE:
        try:
            kg = get_kg()
            enhanced_result = kg.get_enhanced_context(query, club=club)
            if enhanced_result.get("combined_context"):
                enhanced_kg_context = enhanced_result["combined_context"]
                # Add stats to track
                entities["enhanced_kg"] = enhanced_result.get("kg_stats", {})
        except Exception as e:
            pass  # Graceful degradation if enhanced KG fails

    # If club specified but not detected in query, add club context
    team_node = None
    if entities.get("kg_nodes"):
        team_node = next((n for n in entities["kg_nodes"] if n["node_type"] == "team"), None)

    # Club persona enrichment: add club context even for generic queries
    if club and club != "default" and not team_node:
        club_context, club_sources = get_club_persona_context(club)
        if club_context:
            kg_context = club_context + "\n" + kg_context if kg_context else club_context
            kg_sources.extend(club_sources)
        # Also get the team node for mood
        team_id = get_team_id_by_name(club)
        if team_id:
            team_node = {"entity_id": team_id, "node_type": "team"}

    # Get mood for emotional calibration
    team_mood = None
    if team_node:
        team_mood = database.get_club_mood(team_node["entity_id"])

    # Fuse contexts (original)
    fused_context = fuse_contexts(fts_context, kg_context, team_mood)

    # === ENHANCED: Append 500-node KG context ===
    if enhanced_kg_context:
        fused_context = fused_context + "\n\n=== Enhanced Knowledge (500-node KG) ===\n" + enhanced_kg_context

    # === NEW: Live Data Integration (Dec 2024) ===
    live_context_parts = []
    enhanced_mood = None

    if not club or club == "default":
        # === ANALYST MODE: Inject league-wide context ===
        try:
            import sqlite3
            conn = sqlite3.connect(database.DB_PATH)
            conn.row_factory = sqlite3.Row

            # Current standings (top 20)
            standings = conn.execute("""
                SELECT s.position, t.name, s.points, s.won, s.drawn, s.lost,
                       s.goals_for, s.goals_against, s.goal_difference
                FROM standings s JOIN teams t ON s.team_id = t.id
                WHERE s.season = '2025-26'
                ORDER BY s.position
            """).fetchall()

            if standings:
                table_lines = ["=== Current Premier League Standings (2025-26) ==="]
                for r in standings:
                    table_lines.append(
                        f"  {r['position']:>2}. {r['name']:<22} {r['points']:>3} pts "
                        f"({r['won']}W {r['drawn']}D {r['lost']}L) GD:{r['goal_difference']:+d}"
                    )
                live_context_parts.append("\n".join(table_lines))

            # Upcoming fixtures (next 10)
            fixtures = conn.execute("""
                SELECT g.date, h.name AS home, a.name AS away
                FROM games g
                JOIN teams h ON g.home_team_id = h.id
                JOIN teams a ON g.away_team_id = a.id
                WHERE g.status = 'scheduled' AND g.date >= date('now')
                ORDER BY g.date
                LIMIT 10
            """).fetchall()

            if fixtures:
                fix_lines = ["\n=== Upcoming Fixtures ==="]
                for f in fixtures:
                    fix_lines.append(f"  {f['date']}: {f['home']} vs {f['away']}")
                live_context_parts.append("\n".join(fix_lines))

            conn.close()
        except Exception:
            pass

    elif ENHANCED_COMPONENTS:
        try:
            # Get mood from live results
            mood_engine = get_mood_engine()
            club_name = club.replace("_", " ").title()
            mood_result = mood_engine.generate_mood_aware_opening(club_name)
            enhanced_mood = {
                "mood": mood_result.get("mood"),
                "mood_value": mood_result.get("mood_value"),
                "tone": mood_result.get("tone"),
                "banter_level": mood_result.get("banter_level"),
                "reason": mood_result.get("context", {}).get("mood_reason")
            }
            live_context_parts.append(f"Current Mood: {mood_result.get('mood')} - {mood_result.get('context', {}).get('mood_reason', '')}")

            # Get match insights for detected teams
            insights = get_match_insights()
            detected_teams = entities.get("teams", [])

            # If another team is mentioned, get H2H
            if detected_teams and detected_teams[0].lower() != club_name.lower():
                opponent = detected_teams[0]
                h2h = insights.head_to_head(club_name, opponent)
                if h2h.get("total_matches", 0) > 0:
                    live_context_parts.append(
                        f"H2H vs {opponent}: {h2h['team1_wins']}W-{h2h['draws']}D-{h2h['team2_wins']}L "
                        f"({h2h['total_matches']} matches)"
                    )

            # Get ELO context
            elo = insights.get_elo_trajectory(club_name)
            if elo.get("current"):
                live_context_parts.append(f"Current ELO: {elo['current']['elo']:.0f} (Peak: {elo['peak']['elo']:.0f} in {elo['peak']['date'][:4]})")

        except Exception as e:
            pass  # Graceful degradation

    if live_context_parts:
        fused_context = fused_context + "\n\n=== Live Data ===\n" + "\n".join(live_context_parts)

    # Combine and deduplicate sources
    all_sources = deduplicate_sources(fts_sources + kg_sources)

    # Metadata
    enhanced_stats = entities.get("enhanced_kg", {})
    metadata = {
        "entities": {
            "teams": entities.get("teams", []),
            "players": [p.get("name") for p in entities.get("players", [])],
            "kg_nodes": len(entities.get("kg_nodes", [])),
        },
        "kg_intent": entities.get("kg_intent"),
        "mood": team_mood.get("current_mood") if team_mood else None,
        "retrieval_type": "hybrid_kg_rag_enhanced",
        "enhanced_kg": {
            "available": KG_AVAILABLE,
            "entities_matched": enhanced_stats.get("entities_matched", 0),
            "facts_found": enhanced_stats.get("facts_found", 0),
        },
        "live_mood": enhanced_mood,  # New: mood from live results
        "enhanced_components": ENHANCED_COMPONENTS,
    }

    return fused_context, all_sources, metadata


# ============================================
# HIGH IMPACT: RIVAL DETECTION & BANTER
# ============================================

def detect_rival_mention(query: str, persona_data: Dict) -> Optional[Dict]:
    """
    Detect if query mentions a rival team.
    Returns rivalry data if found, None otherwise.
    """
    if not persona_data or not persona_data.get("rivalries"):
        return None

    query_lower = query.lower()

    for rivalry in persona_data["rivalries"]:
        rival_name = rivalry.get("rival_name", "").lower()
        # Check various forms: "tottenham", "spurs", "tott"
        if rival_name in query_lower or any(
            word in query_lower
            for word in rival_name.split()
        ):
            return rivalry

    return None


def enrich_with_rivalry(context: str, rivalry: Dict) -> str:
    """
    Inject rivalry data and banter into context.
    HIGH IMPACT: This makes rival mentions feel AUTHENTIC.
    """
    if not rivalry:
        return context

    rivalry_section = f"""

## 🔥 RIVALRY DETECTED
Rival: {rivalry.get('rival_name')}
Intensity: {rivalry.get('intensity', 5)}/10
Type: {rivalry.get('rivalry_type', 'unknown')}

Origin Story:
{rivalry.get('origin_story', 'Historic rivalry')}

Banter Arsenal (you can use):
{', '.join(rivalry.get('banter_phrases', []))}

IMPORTANT: Show EMOTION when discussing this rival. The intensity is {rivalry.get('intensity')}/10 - let that guide how strongly you feel about them.
"""

    return context + rivalry_section


def detect_squad_query(query: str) -> bool:
    """Detect if query is about squad fitness/injuries."""
    squad_keywords = [
        "squad", "injuries", "injured", "fitness", "who's out", "who is out",
        "team news", "how's the squad", "squad looking", "who can't play"
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in squad_keywords)


def enrich_with_injuries(context: str, team_id: int) -> str:
    """
    Inject current injury list for squad fitness queries.
    HIGH IMPACT: Adds current context to squad discussions.
    """
    injuries = database.get_injuries(team_id=team_id, status="out")
    if not injuries:
        return context

    injury_section = "\n\n## 🏥 CURRENT INJURIES\n"
    for injury in injuries[:5]:  # Top 5 injuries
        injury_section += f"- {injury.get('player_name')}: {injury.get('injury_type')} (out until {injury.get('expected_return', 'TBD')})\n"

    return context + injury_section


# ============================================
# POLISH: LEGEND COMPARISONS
# ============================================

def detect_legend_comparison(query: str) -> bool:
    """Detect if query compares current player to legends."""
    comparison_phrases = [
        "next", "like", "reminds me of", "better than", "as good as",
        "compared to", "vs", "versus"
    ]
    query_lower = query.lower()
    return any(phrase in query_lower for phrase in comparison_phrases)


def enrich_with_legends(context: str, persona_data: Dict) -> str:
    """
    Add legend reference data for comparison queries.
    POLISH: Enables natural comparisons to club legends.
    """
    if not persona_data or not persona_data.get("legends"):
        return context

    legends = persona_data["legends"][:3]  # Top 3 legends
    if not legends:
        return context

    legend_section = "\n\n## ⭐ CLUB LEGENDS (for comparison context)\n"
    for legend in legends:
        legend_section += f"- **{legend.get('name')}** ({legend.get('era')}): {legend.get('fan_nickname', 'Legend')}\n"
        legend_section += f"  {legend.get('story', 'Club icon')}\n"

    return context + legend_section


def fuse_contexts(fts_context: str, kg_context: str, mood: Dict = None) -> str:
    """
    Merge FTS5 + Graph + Mood into rich context.
    Prioritizes graph context for relationship-aware responses.
    """
    parts = []

    # Graph context first (relationship awareness)
    if kg_context:
        parts.append(kg_context)

    # FTS5 results
    if fts_context:
        parts.append("\n## Retrieved Information")
        parts.append(fts_context)

    # Mood calibration
    if mood:
        parts.append(f"\n## Emotional Context")
        parts.append(f"Current mood: {mood.get('current_mood', 'neutral')}")
        parts.append(f"Intensity: {mood.get('mood_intensity', 5)}/10")
        if mood.get("mood_reason"):
            parts.append(f"Reason: {mood['mood_reason']}")

    return "\n".join(parts)


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    # Test entity extraction
    test_queries = [
        "How did Manchester United play yesterday?",
        "Is Haaland injured?",
        "What's the score of the Arsenal game?",
        "Show me Liverpool's upcoming fixtures",
        "Premier League standings",
        "Transfer news for Chelsea",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        entities = extract_entities(query)
        print(f"Entities: {entities}")
        print(f"Intent: {entities['intent']}")
