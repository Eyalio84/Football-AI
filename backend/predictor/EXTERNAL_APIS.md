# External APIs for The Analyst

## Priority 1: High Impact, Free Tiers Available

### 1. Weather API
**OpenWeatherMap** (openweathermap.org)
- Free: 1000 calls/day
- Data: Temperature, rain, wind speed, humidity
- Pattern Impact:
  - Rain > 2mm/hr: Possession teams -10% efficiency
  - Wind > 25mph: Long ball accuracy +15%
  - Cold < 5°C: Player muscle injury risk +20%

```python
# Example endpoint
GET https://api.openweathermap.org/data/2.5/weather?q=London&appid={API_KEY}

# Fields we need:
# - weather[0].main (Rain, Clear, Snow)
# - wind.speed (m/s)
# - main.temp (Kelvin)
```

### 2. Football Data API
**Football-Data.org** (football-data.org)
- Free: 10 calls/minute
- Data: Fixtures, results, standings, teams
- Pattern Impact:
  - Days since last match
  - Head-to-head history
  - Current league position
  - Recent form (WWLDL)

```python
# Example endpoints
GET https://api.football-data.org/v4/matches?status=SCHEDULED
GET https://api.football-data.org/v4/teams/{id}/matches?status=FINISHED&limit=5
GET https://api.football-data.org/v4/competitions/PL/standings
```

### 3. Odds API
**The Odds API** (the-odds-api.com)
- Free: 500 requests/month
- Data: Betting odds from multiple bookmakers
- Pattern Impact:
  - Line movement detection (smart money)
  - Market inefficiencies
  - Implied probability vs our probability

```python
# Example
GET https://api.the-odds-api.com/v4/sports/soccer_epl/odds?regions=uk

# Pattern: When line moves AGAINST public, smart money knows something
```

## Priority 2: Medium Impact

### 4. News/Sentiment API
**NewsAPI** (newsapi.org)
- Free: 100 requests/day (dev)
- Data: Headlines, articles
- Pattern Impact:
  - Manager sack speculation
  - Transfer drama
  - Player controversies
  - Fan protests

```python
# Search for team-related news
GET https://newsapi.org/v2/everything?q=Arsenal+manager&sortBy=publishedAt
```

### 5. Social Sentiment (X/Twitter)
**Twitter API v2** (developer.twitter.com)
- Free: Limited read access
- Data: Fan sentiment, player mentions
- Pattern Impact:
  - Pre-match atmosphere
  - Injury rumors before official
  - Dressing room leaks

### 6. Transfermarkt (Unofficial)
**Transfermarkt API** (via scraping or unofficial API)
- Data: Player values, injuries, suspensions
- Pattern Impact:
  - Who's actually fit
  - Who's suspended
  - Squad depth analysis

## Priority 3: Nice to Have

### 7. Travel/Distance Calculator
**Google Maps Distance Matrix** or **OpenRouteService**
- Data: Travel distance, time between stadiums
- Pattern Impact:
  - Newcastle away = fatigue factor
  - London derbies = no travel advantage

### 8. Historical Stats
**FBref** (fbref.com) - Scraping
- Data: Advanced stats, xG, progressive passes
- Pattern Impact:
  - xG overperformance regression
  - Pressing intensity metrics

### 9. Referee Data
**Custom Database** (build from historical)
- Data: Cards per game, home bias, penalty tendency
- Pattern Impact:
  - Certain refs favor home teams
  - Card-happy refs = physical teams disadvantaged

## Implementation Plan

### Phase 1: Weather + Fixtures
```python
class DataIngestion:
    def get_match_weather(self, venue: str, match_date: str) -> dict:
        # Call OpenWeatherMap
        # Return: {rain_mm, wind_mph, temp_c}

    def get_team_fixtures(self, team_id: int, days: int = 14) -> list:
        # Call Football-Data.org
        # Return: [recent_games, upcoming_games]
```

### Phase 2: Odds Integration
```python
class OddsAnalyzer:
    def get_current_odds(self, home: str, away: str) -> dict:
        # Return: {home_odds, draw_odds, away_odds, implied_prob}

    def detect_line_movement(self, match_id: str) -> dict:
        # Return: {direction, magnitude, smart_money_indicator}
```

### Phase 3: News Sentiment
```python
class SentimentAnalyzer:
    def get_team_sentiment(self, team: str, hours: int = 48) -> dict:
        # Return: {positive, negative, neutral, key_topics}

    def detect_crisis(self, team: str) -> bool:
        # Return: True if manager sack, player drama, etc.
```

## New Factors to Add (from APIs)

### Side A (Favorite Weakness)
- A11: Bad weather for style (rain vs possession)
- A12: Travel fatigue (distance > 300km)
- A13: Negative press sentiment
- A14: Odds shortening suspiciously (smart money against)
- A15: Referee history unfavorable

### Side B (Underdog Strength)
- B11: Home weather advantage
- B12: No travel (home game)
- B13: Positive momentum from news
- B14: Value odds (market underestimating)
- B15: Referee history favorable

## Cost Estimates

| API | Monthly Cost | Value |
|-----|-------------|-------|
| OpenWeatherMap | Free | High |
| Football-Data.org | Free | Critical |
| The Odds API | Free (limited) | High |
| NewsAPI | Free (dev) | Medium |
| Total | $0 | Excellent ROI |

## Next Steps
1. Register for free API keys
2. Build data ingestion layer
3. Add A11-A15 and B11-B15 factors
4. Create new Third Knowledge patterns
5. Backtest against historical data
