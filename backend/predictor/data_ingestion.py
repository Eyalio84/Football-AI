"""
Data Ingestion Module for The Analyst
Fetches external data from APIs to enhance predictions

APIs Integrated:
- Football-Data.org (fixtures, standings, form)
- OpenWeatherMap (match day weather)
- The Odds API (betting odds, line movement)
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# ============================================
# API CONFIGURATION
# ============================================

# API Keys (set via environment variables)
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

# API Endpoints
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"
WEATHER_BASE = "https://api.openweathermap.org/data/2.5"
ODDS_BASE = "https://api.the-odds-api.com/v4"

# Premier League competition ID
PL_COMPETITION_ID = "PL"

# ============================================
# STADIUM DATA (for weather lookups)
# ============================================

STADIUM_LOCATIONS = {
    "arsenal": {"name": "Emirates Stadium", "city": "London", "lat": 51.5549, "lon": -0.1084},
    "aston_villa": {"name": "Villa Park", "city": "Birmingham", "lat": 52.5092, "lon": -1.8846},
    "bournemouth": {"name": "Vitality Stadium", "city": "Bournemouth", "lat": 50.7352, "lon": -1.8384},
    "brentford": {"name": "Gtech Community Stadium", "city": "London", "lat": 51.4907, "lon": -0.2886},
    "brighton": {"name": "Amex Stadium", "city": "Brighton", "lat": 50.8616, "lon": -0.0837},
    "chelsea": {"name": "Stamford Bridge", "city": "London", "lat": 51.4817, "lon": -0.1910},
    "crystal_palace": {"name": "Selhurst Park", "city": "London", "lat": 51.3983, "lon": -0.0855},
    "everton": {"name": "Goodison Park", "city": "Liverpool", "lat": 53.4388, "lon": -2.9663},
    "fulham": {"name": "Craven Cottage", "city": "London", "lat": 51.4749, "lon": -0.2217},
    "leicester": {"name": "King Power Stadium", "city": "Leicester", "lat": 52.6204, "lon": -1.1422},
    "liverpool": {"name": "Anfield", "city": "Liverpool", "lat": 53.4308, "lon": -2.9608},
    "manchester_city": {"name": "Etihad Stadium", "city": "Manchester", "lat": 53.4831, "lon": -2.2004},
    "manchester_united": {"name": "Old Trafford", "city": "Manchester", "lat": 53.4631, "lon": -2.2913},
    "newcastle": {"name": "St James' Park", "city": "Newcastle", "lat": 54.9756, "lon": -1.6217},
    "nottingham_forest": {"name": "City Ground", "city": "Nottingham", "lat": 52.9400, "lon": -1.1328},
    "tottenham": {"name": "Tottenham Hotspur Stadium", "city": "London", "lat": 51.6043, "lon": -0.0665},
    "west_ham": {"name": "London Stadium", "city": "London", "lat": 51.5387, "lon": -0.0166},
    "wolves": {"name": "Molineux Stadium", "city": "Wolverhampton", "lat": 52.5902, "lon": -2.1304},
}

# Football-Data.org team IDs
TEAM_IDS = {
    "arsenal": 57,
    "aston_villa": 58,
    "bournemouth": 1044,
    "brentford": 402,
    "brighton": 397,
    "chelsea": 61,
    "crystal_palace": 354,
    "everton": 62,
    "fulham": 63,
    "leicester": 338,
    "liverpool": 64,
    "manchester_city": 65,
    "manchester_united": 66,
    "newcastle": 67,
    "nottingham_forest": 351,
    "tottenham": 73,
    "west_ham": 563,
    "wolves": 76,
}


# ============================================
# HTTP HELPER
# ============================================

def api_request(url: str, headers: Dict = None) -> Dict:
    """Make an API request and return JSON response."""
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "message": e.read().decode('utf-8')}
    except urllib.error.URLError as e:
        return {"error": "network", "message": str(e)}
    except Exception as e:
        return {"error": "unknown", "message": str(e)}


# ============================================
# FOOTBALL DATA API
# ============================================

class FootballDataAPI:
    """Interface to Football-Data.org API for fixtures, standings, and form."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or FOOTBALL_DATA_KEY
        self.headers = {"X-Auth-Token": self.api_key} if self.api_key else {}

    def get_standings(self) -> Dict:
        """Get current Premier League standings."""
        url = f"{FOOTBALL_DATA_BASE}/competitions/{PL_COMPETITION_ID}/standings"
        data = api_request(url, self.headers)

        if "error" in data:
            return data

        standings = []
        try:
            for entry in data.get("standings", [{}])[0].get("table", []):
                standings.append({
                    "position": entry.get("position"),
                    "team": entry.get("team", {}).get("name"),
                    "team_id": entry.get("team", {}).get("id"),
                    "played": entry.get("playedGames"),
                    "won": entry.get("won"),
                    "drawn": entry.get("draw"),
                    "lost": entry.get("lost"),
                    "points": entry.get("points"),
                    "goals_for": entry.get("goalsFor"),
                    "goals_against": entry.get("goalsAgainst"),
                    "goal_diff": entry.get("goalDifference"),
                    "form": entry.get("form"),  # e.g., "W,W,D,L,W"
                })
        except (KeyError, IndexError):
            return {"error": "parse", "message": "Could not parse standings"}

        return {"standings": standings, "updated": datetime.now().isoformat()}

    def get_team_form(self, team_slug: str, matches: int = 5) -> Dict:
        """Get recent form for a team."""
        team_id = TEAM_IDS.get(team_slug)
        if not team_id:
            return {"error": "unknown_team", "message": f"Unknown team: {team_slug}"}

        url = f"{FOOTBALL_DATA_BASE}/teams/{team_id}/matches?status=FINISHED&limit={matches}"
        data = api_request(url, self.headers)

        if "error" in data:
            return data

        form = []
        try:
            for match in data.get("matches", []):
                home = match.get("homeTeam", {}).get("id")
                away = match.get("awayTeam", {}).get("id")
                score = match.get("score", {}).get("fullTime", {})

                if home == team_id:
                    is_home = True
                    goals_for = score.get("home", 0)
                    goals_against = score.get("away", 0)
                else:
                    is_home = False
                    goals_for = score.get("away", 0)
                    goals_against = score.get("home", 0)

                if goals_for > goals_against:
                    result = "W"
                elif goals_for < goals_against:
                    result = "L"
                else:
                    result = "D"

                form.append({
                    "date": match.get("utcDate"),
                    "opponent": match.get("awayTeam" if is_home else "homeTeam", {}).get("name"),
                    "home": is_home,
                    "result": result,
                    "score": f"{goals_for}-{goals_against}",
                })
        except (KeyError, TypeError):
            return {"error": "parse", "message": "Could not parse matches"}

        # Calculate form string (e.g., "WWDLW")
        form_string = "".join([m["result"] for m in form[:5]])

        return {
            "team": team_slug,
            "matches": form,
            "form_string": form_string,
            "wins": form_string.count("W"),
            "draws": form_string.count("D"),
            "losses": form_string.count("L"),
        }

    def get_upcoming_fixtures(self, days: int = 7) -> Dict:
        """Get upcoming Premier League fixtures."""
        date_from = datetime.now().strftime("%Y-%m-%d")
        date_to = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

        url = f"{FOOTBALL_DATA_BASE}/competitions/{PL_COMPETITION_ID}/matches?dateFrom={date_from}&dateTo={date_to}"
        data = api_request(url, self.headers)

        if "error" in data:
            return data

        fixtures = []
        try:
            for match in data.get("matches", []):
                fixtures.append({
                    "id": match.get("id"),
                    "date": match.get("utcDate"),
                    "home_team": match.get("homeTeam", {}).get("name"),
                    "away_team": match.get("awayTeam", {}).get("name"),
                    "home_id": match.get("homeTeam", {}).get("id"),
                    "away_id": match.get("awayTeam", {}).get("id"),
                    "matchday": match.get("matchday"),
                    "status": match.get("status"),
                })
        except (KeyError, TypeError):
            return {"error": "parse", "message": "Could not parse fixtures"}

        return {"fixtures": fixtures, "count": len(fixtures)}

    def get_head_to_head(self, team1_slug: str, team2_slug: str, limit: int = 10) -> Dict:
        """Get head-to-head history between two teams."""
        team1_id = TEAM_IDS.get(team1_slug)
        team2_id = TEAM_IDS.get(team2_slug)

        if not team1_id or not team2_id:
            return {"error": "unknown_team", "message": "One or both teams unknown"}

        # Get team1's matches
        url = f"{FOOTBALL_DATA_BASE}/teams/{team1_id}/matches?status=FINISHED&limit=50"
        data = api_request(url, self.headers)

        if "error" in data:
            return data

        h2h = []
        try:
            for match in data.get("matches", []):
                home_id = match.get("homeTeam", {}).get("id")
                away_id = match.get("awayTeam", {}).get("id")

                # Only include matches against team2
                if team2_id not in [home_id, away_id]:
                    continue

                score = match.get("score", {}).get("fullTime", {})
                h2h.append({
                    "date": match.get("utcDate"),
                    "home_team": match.get("homeTeam", {}).get("name"),
                    "away_team": match.get("awayTeam", {}).get("name"),
                    "score": f"{score.get('home', 0)}-{score.get('away', 0)}",
                })

                if len(h2h) >= limit:
                    break
        except (KeyError, TypeError):
            return {"error": "parse", "message": "Could not parse H2H"}

        return {
            "team1": team1_slug,
            "team2": team2_slug,
            "matches": h2h,
            "count": len(h2h),
        }


# ============================================
# WEATHER API
# ============================================

class WeatherAPI:
    """Interface to OpenWeatherMap API for match day weather."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or WEATHER_API_KEY

    def get_current_weather(self, team_slug: str) -> Dict:
        """Get current weather at a team's stadium."""
        stadium = STADIUM_LOCATIONS.get(team_slug)
        if not stadium:
            return {"error": "unknown_team", "message": f"Unknown team: {team_slug}"}

        if not self.api_key:
            return {"error": "no_api_key", "message": "OPENWEATHER_API_KEY not set"}

        url = f"{WEATHER_BASE}/weather?lat={stadium['lat']}&lon={stadium['lon']}&appid={self.api_key}&units=metric"
        data = api_request(url)

        if "error" in data:
            return data

        try:
            weather = {
                "stadium": stadium["name"],
                "city": stadium["city"],
                "condition": data.get("weather", [{}])[0].get("main", "Unknown"),
                "description": data.get("weather", [{}])[0].get("description", ""),
                "temp_c": data.get("main", {}).get("temp"),
                "feels_like_c": data.get("main", {}).get("feels_like"),
                "humidity": data.get("main", {}).get("humidity"),
                "wind_speed_ms": data.get("wind", {}).get("speed"),
                "wind_speed_mph": round(data.get("wind", {}).get("speed", 0) * 2.237, 1),
                "rain_1h_mm": data.get("rain", {}).get("1h", 0),
                "clouds_percent": data.get("clouds", {}).get("all", 0),
            }
        except (KeyError, TypeError):
            return {"error": "parse", "message": "Could not parse weather"}

        # Calculate weather impact factors
        weather["impacts"] = self._calculate_weather_impacts(weather)

        return weather

    def _calculate_weather_impacts(self, weather: Dict) -> Dict:
        """Calculate how weather affects different playing styles."""
        impacts = {
            "possession_penalty": 0,
            "direct_bonus": 0,
            "injury_risk": 0,
            "factors_active": [],
        }

        # Rain impact
        rain = weather.get("rain_1h_mm", 0)
        if rain > 2:
            impacts["possession_penalty"] = -10
            impacts["direct_bonus"] = 5
            impacts["factors_active"].append("A11_rain_vs_possession")

        # Wind impact
        wind = weather.get("wind_speed_mph", 0)
        if wind > 25:
            impacts["direct_bonus"] += 15
            impacts["factors_active"].append("B11_wind_favors_direct")

        # Cold impact
        temp = weather.get("temp_c", 15)
        if temp < 5:
            impacts["injury_risk"] = 20
            impacts["factors_active"].append("cold_injury_risk")

        return impacts

    def get_forecast(self, team_slug: str, hours_ahead: int = 24) -> Dict:
        """Get weather forecast for upcoming match."""
        stadium = STADIUM_LOCATIONS.get(team_slug)
        if not stadium:
            return {"error": "unknown_team", "message": f"Unknown team: {team_slug}"}

        if not self.api_key:
            return {"error": "no_api_key", "message": "OPENWEATHER_API_KEY not set"}

        url = f"{WEATHER_BASE}/forecast?lat={stadium['lat']}&lon={stadium['lon']}&appid={self.api_key}&units=metric&cnt=8"
        data = api_request(url)

        if "error" in data:
            return data

        forecasts = []
        try:
            for item in data.get("list", []):
                forecasts.append({
                    "datetime": item.get("dt_txt"),
                    "condition": item.get("weather", [{}])[0].get("main"),
                    "temp_c": item.get("main", {}).get("temp"),
                    "wind_speed_mph": round(item.get("wind", {}).get("speed", 0) * 2.237, 1),
                    "rain_3h_mm": item.get("rain", {}).get("3h", 0),
                })
        except (KeyError, TypeError):
            return {"error": "parse", "message": "Could not parse forecast"}

        return {
            "stadium": stadium["name"],
            "forecasts": forecasts,
        }


# ============================================
# ODDS API
# ============================================

class OddsAPI:
    """Interface to The Odds API for betting odds and line movement."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or ODDS_API_KEY

    def get_epl_odds(self) -> Dict:
        """Get current odds for all Premier League matches."""
        if not self.api_key:
            return {"error": "no_api_key", "message": "ODDS_API_KEY not set"}

        url = f"{ODDS_BASE}/sports/soccer_epl/odds?apiKey={self.api_key}&regions=uk&markets=h2h"
        data = api_request(url)

        if "error" in data:
            return data

        matches = []
        try:
            for event in data:
                bookmakers = event.get("bookmakers", [])
                if not bookmakers:
                    continue

                # Get average odds across bookmakers
                home_odds = []
                draw_odds = []
                away_odds = []

                for bookie in bookmakers:
                    for market in bookie.get("markets", []):
                        if market.get("key") == "h2h":
                            for outcome in market.get("outcomes", []):
                                name = outcome.get("name")
                                price = outcome.get("price")
                                if name == event.get("home_team"):
                                    home_odds.append(price)
                                elif name == event.get("away_team"):
                                    away_odds.append(price)
                                elif name == "Draw":
                                    draw_odds.append(price)

                avg_home = sum(home_odds) / len(home_odds) if home_odds else 0
                avg_draw = sum(draw_odds) / len(draw_odds) if draw_odds else 0
                avg_away = sum(away_odds) / len(away_odds) if away_odds else 0

                matches.append({
                    "id": event.get("id"),
                    "home_team": event.get("home_team"),
                    "away_team": event.get("away_team"),
                    "commence_time": event.get("commence_time"),
                    "odds": {
                        "home": round(avg_home, 2),
                        "draw": round(avg_draw, 2),
                        "away": round(avg_away, 2),
                    },
                    "implied_probability": {
                        "home": round(100 / avg_home, 1) if avg_home else 0,
                        "draw": round(100 / avg_draw, 1) if avg_draw else 0,
                        "away": round(100 / avg_away, 1) if avg_away else 0,
                    },
                    "bookmaker_count": len(bookmakers),
                })
        except (KeyError, TypeError, ZeroDivisionError):
            return {"error": "parse", "message": "Could not parse odds"}

        return {"matches": matches, "count": len(matches)}

    def detect_value_bet(self, match_odds: Dict, our_probability: Dict) -> Dict:
        """Detect if market is undervaluing a team (A14/B14 factors)."""
        result = {
            "value_found": False,
            "factors_active": [],
        }

        implied = match_odds.get("implied_probability", {})

        # Check each outcome for value
        for outcome in ["home", "draw", "away"]:
            market_prob = implied.get(outcome, 0)
            our_prob = our_probability.get(outcome, 0)

            # Value exists if our probability is significantly higher than market
            if our_prob > market_prob + 10:  # 10% edge threshold
                result["value_found"] = True
                result["factors_active"].append(f"B14_value_{outcome}")
                result[f"{outcome}_edge"] = round(our_prob - market_prob, 1)

        return result


# ============================================
# UNIFIED DATA INGESTION
# ============================================

class DataIngestion:
    """
    Unified interface for all external data sources.
    Provides data for predictor factors A11-A15 and B11-B15.
    """

    def __init__(self):
        self.football = FootballDataAPI()
        self.weather = WeatherAPI()
        self.odds = OddsAPI()

    def get_match_context(self, home_team: str, away_team: str) -> Dict:
        """
        Get all relevant external data for a match prediction.
        Returns factors for Side A and Side B analysis.
        """
        context = {
            "home_team": home_team,
            "away_team": away_team,
            "generated_at": datetime.now().isoformat(),
            "weather": None,
            "home_form": None,
            "away_form": None,
            "standings": None,
            "odds": None,
            "active_factors": {
                "side_a": [],
                "side_b": [],
            },
        }

        # Get weather at home stadium
        weather = self.weather.get_current_weather(home_team)
        if "error" not in weather:
            context["weather"] = weather
            # Add weather-based factors
            if weather.get("impacts", {}).get("possession_penalty"):
                context["active_factors"]["side_a"].append("A11")
            if weather.get("impacts", {}).get("direct_bonus"):
                context["active_factors"]["side_b"].append("B11")

        # Get form for both teams
        home_form = self.football.get_team_form(home_team)
        if "error" not in home_form:
            context["home_form"] = home_form

        away_form = self.football.get_team_form(away_team)
        if "error" not in away_form:
            context["away_form"] = away_form

        # Get current standings
        standings = self.football.get_standings()
        if "error" not in standings:
            context["standings"] = standings

        # B12: Home team has no travel advantage
        context["active_factors"]["side_b"].append("B12")

        return context

    def calculate_travel_fatigue(self, team_slug: str, opponent_slug: str) -> Dict:
        """Calculate travel distance for A12 factor."""
        team_stadium = STADIUM_LOCATIONS.get(team_slug)
        opponent_stadium = STADIUM_LOCATIONS.get(opponent_slug)

        if not team_stadium or not opponent_stadium:
            return {"error": "unknown_team"}

        # Haversine formula for distance
        from math import radians, sin, cos, sqrt, atan2

        lat1, lon1 = radians(team_stadium["lat"]), radians(team_stadium["lon"])
        lat2, lon2 = radians(opponent_stadium["lat"]), radians(opponent_stadium["lon"])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))

        # Earth's radius in km
        distance_km = 6371 * c

        fatigue_factor = False
        if distance_km > 300:
            fatigue_factor = True  # A12 activates

        return {
            "from": team_stadium["name"],
            "to": opponent_stadium["name"],
            "distance_km": round(distance_km, 1),
            "a12_fatigue_active": fatigue_factor,
        }


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("Data Ingestion Module - Test Suite")
    print("=" * 60)

    ingestion = DataIngestion()

    # Test 1: Stadium data
    print("\n[TEST 1] Stadium Locations")
    print("-" * 40)
    for team, stadium in list(STADIUM_LOCATIONS.items())[:3]:
        print(f"  {team}: {stadium['name']} ({stadium['city']})")
    print(f"  ... and {len(STADIUM_LOCATIONS) - 3} more")

    # Test 2: Travel distance
    print("\n[TEST 2] Travel Distance Calculator")
    print("-" * 40)
    travel = ingestion.calculate_travel_fatigue("newcastle", "bournemouth")
    if "error" not in travel:
        print(f"  Newcastle -> Bournemouth: {travel['distance_km']} km")
        print(f"  A12 Fatigue Factor: {'ACTIVE' if travel['a12_fatigue_active'] else 'inactive'}")

    travel2 = ingestion.calculate_travel_fatigue("arsenal", "tottenham")
    if "error" not in travel2:
        print(f"  Arsenal -> Tottenham: {travel2['distance_km']} km")
        print(f"  A12 Fatigue Factor: {'ACTIVE' if travel2['a12_fatigue_active'] else 'inactive'}")

    # Test 3: API availability
    print("\n[TEST 3] API Key Status")
    print("-" * 40)
    print(f"  Football-Data.org: {'CONFIGURED' if FOOTBALL_DATA_KEY else 'NOT SET'}")
    print(f"  OpenWeatherMap: {'CONFIGURED' if WEATHER_API_KEY else 'NOT SET'}")
    print(f"  The Odds API: {'CONFIGURED' if ODDS_API_KEY else 'NOT SET'}")

    # Test 4: Weather (if key available)
    if WEATHER_API_KEY:
        print("\n[TEST 4] Weather API")
        print("-" * 40)
        weather = ingestion.weather.get_current_weather("manchester_united")
        if "error" not in weather:
            print(f"  Old Trafford: {weather['condition']}, {weather['temp_c']}°C")
            print(f"  Wind: {weather['wind_speed_mph']} mph, Rain: {weather['rain_1h_mm']} mm")
            print(f"  Impacts: {weather['impacts']}")
        else:
            print(f"  Error: {weather}")

    # Test 5: Football Data (if key available)
    if FOOTBALL_DATA_KEY:
        print("\n[TEST 5] Football Data API")
        print("-" * 40)
        form = ingestion.football.get_team_form("liverpool", matches=3)
        if "error" not in form:
            print(f"  Liverpool form: {form['form_string']}")
            for match in form["matches"][:3]:
                print(f"    {match['result']} vs {match['opponent']} ({match['score']})")
        else:
            print(f"  Error: {form}")

    print("\n" + "=" * 60)
    print("Tests complete.")
    print("=" * 60)
