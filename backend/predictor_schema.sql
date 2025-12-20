-- Predictor Facts Database Schema
-- Separate knowledge base for The Analyst
-- Created: December 21, 2024

-- ============================================
-- CORE FACTS DATABASE
-- The Analyst's knowledge repository
-- ============================================

-- Historical match facts with outcome
CREATE TABLE IF NOT EXISTS predictor_match_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,                 -- Reference to games table
    season TEXT NOT NULL,             -- '2024-25'
    match_date DATE NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    favorite TEXT,                    -- Which team was favorite
    underdog TEXT,
    was_upset BOOLEAN DEFAULT FALSE,
    upset_magnitude REAL,             -- How big was the upset (odds difference)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SIDE A: FAVORITE WEAKNESS FACTORS
-- What made the favorite vulnerable?
-- ============================================

CREATE TABLE IF NOT EXISTS side_a_factors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_fact_id INTEGER REFERENCES predictor_match_facts(id),
    factor_code TEXT NOT NULL,        -- 'A01', 'A02', etc.
    factor_name TEXT NOT NULL,
    factor_value REAL,                -- Normalized 0.0 to 1.0
    raw_value TEXT,                   -- Original measurement
    contributed_to_upset BOOLEAN,     -- Did this factor matter?
    weight REAL DEFAULT 1.0,          -- Learned importance
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SIDE B: UNDERDOG STRENGTH FACTORS
-- What gave the underdog an edge?
-- ============================================

CREATE TABLE IF NOT EXISTS side_b_factors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_fact_id INTEGER REFERENCES predictor_match_facts(id),
    factor_code TEXT NOT NULL,        -- 'B01', 'B02', etc.
    factor_name TEXT NOT NULL,
    factor_value REAL,                -- Normalized 0.0 to 1.0
    raw_value TEXT,
    contributed_to_upset BOOLEAN,
    weight REAL DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- THIRD KNOWLEDGE: DISCOVERED PATTERNS
-- What's hidden between the data?
-- ============================================

CREATE TABLE IF NOT EXISTS third_knowledge_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name TEXT NOT NULL UNIQUE,
    description TEXT,
    factor_a_code TEXT,               -- First factor in interaction
    factor_b_code TEXT,               -- Second factor
    interaction_type TEXT,            -- 'multiplicative', 'threshold', 'inverse'
    multiplier REAL DEFAULT 1.0,      -- How much they amplify
    threshold_value REAL,             -- When pattern activates
    sample_size INTEGER DEFAULT 0,    -- Matches analyzed
    success_rate REAL,                -- How often pattern predicts correctly
    confidence REAL DEFAULT 0.5,      -- Statistical confidence
    is_validated BOOLEAN DEFAULT FALSE,
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_validated DATETIME
);

-- ============================================
-- PREDICTIONS & VALIDATION
-- Track accuracy, learn from mistakes
-- ============================================

CREATE TABLE IF NOT EXISTS predictor_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    match_date DATE,
    home_team TEXT,
    away_team TEXT,
    favorite TEXT,
    underdog TEXT,
    -- Side A analysis
    side_a_score REAL,                -- Aggregate weakness score
    side_a_top_factors TEXT,          -- JSON: top 3 factors
    -- Side B analysis
    side_b_score REAL,                -- Aggregate strength score
    side_b_top_factors TEXT,          -- JSON: top 3 factors
    -- Combined prediction
    naive_upset_prob REAL,            -- Simple A + B
    interaction_boost REAL,           -- From detected patterns
    third_knowledge_adj REAL,         -- Gap adjustment
    final_upset_prob REAL,            -- Final prediction
    -- Confidence
    confidence_level TEXT,            -- 'low', 'medium', 'high'
    confidence_score REAL,
    -- Explanation
    explanation TEXT,                 -- Natural language explanation
    key_insight TEXT,                 -- The "hidden" insight
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prediction_outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER REFERENCES predictor_predictions(id),
    actual_home_score INTEGER,
    actual_away_score INTEGER,
    actual_result TEXT,               -- 'home_win', 'draw', 'away_win'
    was_upset BOOLEAN,
    prediction_correct BOOLEAN,       -- Did we call it right?
    probability_error REAL,           -- How far off were we?
    lessons_learned TEXT,             -- JSON: what we learned
    validated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TEAM PROFILES (Predictor's View)
-- How the Analyst sees each team
-- ============================================

CREATE TABLE IF NOT EXISTS predictor_team_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name TEXT NOT NULL UNIQUE,
    team_id INTEGER,                  -- Reference to teams table
    -- Playing style metrics
    playing_style TEXT,               -- 'possession', 'counter', 'direct', 'pressing'
    avg_possession REAL,
    avg_ppda REAL,                    -- Passes per defensive action
    set_piece_threat REAL,            -- 0-1 scale
    counter_attack_efficiency REAL,
    -- Psychological profile
    pressure_handling TEXT,           -- 'strong', 'average', 'weak'
    home_fortress_rating REAL,        -- 0-1 scale
    away_performance_rating REAL,
    comeback_ability REAL,
    collapse_risk REAL,
    -- Form tracking
    current_form TEXT,                -- 'WWDLW'
    xg_trend TEXT,                    -- 'improving', 'stable', 'declining'
    momentum_score REAL,
    -- Historical patterns
    upset_likelihood_as_favorite REAL,
    upset_likelihood_as_underdog REAL,
    best_conditions TEXT,             -- JSON: when they overperform
    worst_conditions TEXT,            -- JSON: when they underperform
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- EXTERNAL FACTORS DATABASE
-- Weather, referees, schedules
-- ============================================

CREATE TABLE IF NOT EXISTS referee_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    avg_fouls_per_game REAL,
    avg_yellows_per_game REAL,
    avg_reds_per_game REAL,
    penalty_tendency REAL,            -- Above/below average
    home_bias_score REAL,             -- Does home team benefit?
    var_overturn_rate REAL,
    style TEXT,                       -- 'strict', 'lenient', 'card-happy'
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weather_impacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condition TEXT NOT NULL,          -- 'heavy_rain', 'strong_wind', 'extreme_heat'
    impact_on_possession_teams REAL,  -- -1 to +1
    impact_on_direct_teams REAL,
    impact_on_set_pieces REAL,
    upset_correlation REAL,           -- How much it increases upsets
    notes TEXT
);

-- ============================================
-- API ENDPOINTS DISCOVERED
-- Track useful data sources
-- ============================================

CREATE TABLE IF NOT EXISTS api_endpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,        -- 'football-data.org', 'api-football'
    endpoint_url TEXT,
    data_type TEXT,                   -- 'fixtures', 'weather', 'injuries', 'xg'
    use_for TEXT,                     -- 'fan', 'predictor', 'both'
    is_free BOOLEAN,
    rate_limit TEXT,
    reliability_score REAL,
    notes TEXT,
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- ANALYST INSIGHTS LOG
-- What The Analyst has learned
-- ============================================

CREATE TABLE IF NOT EXISTS analyst_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_type TEXT,                -- 'pattern', 'correlation', 'anomaly'
    title TEXT NOT NULL,
    description TEXT,
    supporting_data TEXT,             -- JSON: evidence
    confidence REAL,
    actionable BOOLEAN DEFAULT TRUE,
    times_validated INTEGER DEFAULT 0,
    times_failed INTEGER DEFAULT 0,
    success_rate REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used DATETIME
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX IF NOT EXISTS idx_match_facts_date ON predictor_match_facts(match_date);
CREATE INDEX IF NOT EXISTS idx_match_facts_upset ON predictor_match_facts(was_upset);
CREATE INDEX IF NOT EXISTS idx_side_a_factor ON side_a_factors(factor_code);
CREATE INDEX IF NOT EXISTS idx_side_b_factor ON side_b_factors(factor_code);
CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictor_predictions(match_date);
CREATE INDEX IF NOT EXISTS idx_team_profiles_name ON predictor_team_profiles(team_name);
CREATE INDEX IF NOT EXISTS idx_patterns_validated ON third_knowledge_patterns(is_validated);

-- ============================================
-- INITIAL FACTOR DEFINITIONS (Simplified Start)
-- 10 Side A + 10 Side B factors
-- ============================================

-- Side A: Favorite Weakness Factors (Simplified)
CREATE TABLE IF NOT EXISTS factor_definitions_a (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    data_source TEXT,
    weight REAL DEFAULT 1.0,
    is_active BOOLEAN DEFAULT TRUE
);

INSERT OR IGNORE INTO factor_definitions_a (code, name, description, data_source) VALUES
('A01', 'Rest disadvantage', 'Fewer rest days than opponent', 'fixtures'),
('A02', 'Key player missing', 'Top scorer or captain injured/suspended', 'injuries'),
('A03', 'Fixture congestion', '3+ games in 8 days', 'fixtures'),
('A04', 'Away from home', 'Playing away (reduced home advantage)', 'fixtures'),
('A05', 'Bad recent form', 'Lost 2+ of last 5 games', 'results'),
('A06', 'Overperforming xG', 'Scoring above expected (regression due)', 'xg_data'),
('A07', 'Weather disadvantage', 'Conditions favor opponent style', 'weather'),
('A08', 'Pressure situation', 'Must-win or title race pressure', 'standings'),
('A09', 'Post-European hangover', 'Played European game in last 4 days', 'fixtures'),
('A10', 'Squad disruption', 'Transfer rumors, contract disputes', 'news');

-- Side B: Underdog Strength Factors (Simplified)
CREATE TABLE IF NOT EXISTS factor_definitions_b (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    data_source TEXT,
    weight REAL DEFAULT 1.0,
    is_active BOOLEAN DEFAULT TRUE
);

INSERT OR IGNORE INTO factor_definitions_b (code, name, description, data_source) VALUES
('B01', 'Nothing to lose', 'Position gap > 8 places (freedom)', 'standings'),
('B02', 'Home fortress', 'Unbeaten at home 5+ games', 'results'),
('B03', 'Rest advantage', 'More rest days than opponent', 'fixtures'),
('B04', 'Hot streak', 'Won 3+ of last 5 games', 'results'),
('B05', 'Counter-attack threat', 'Goals from counters > 30%', 'xg_data'),
('B06', 'Set-piece danger', 'Set-piece goals > league average', 'stats'),
('B07', 'Goalkeeper form', 'Save rate > 75% last 5 games', 'stats'),
('B08', 'Derby motivation', 'Local rivalry match', 'fixtures'),
('B09', 'Survival fight', 'Relegation threatened (desperation)', 'standings'),
('B10', 'New manager bounce', 'Manager appointed < 5 games ago', 'news');
