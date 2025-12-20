-- Soccer-AI Database Schema
-- SQLite + FTS5 for full-text search (RAG retrieval)
-- Created: December 18, 2024

-- ============================================
-- CORE ENTITIES
-- ============================================

-- Teams (must exist before players)
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    short_name TEXT,              -- "MAN UTD", "BAR"
    league TEXT NOT NULL,         -- "Premier League", "La Liga"
    country TEXT NOT NULL,
    stadium TEXT,
    founded INTEGER,
    logo_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Players
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    team_id INTEGER REFERENCES teams(id),
    position TEXT,                -- "Forward", "Midfielder", "Defender", "Goalkeeper"
    nationality TEXT,
    birth_date DATE,
    jersey_number INTEGER,
    height_cm INTEGER,
    weight_kg INTEGER,
    market_value_eur INTEGER,     -- In euros
    photo_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Games/Matches
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    time TIME,
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    home_score INTEGER,
    away_score INTEGER,
    status TEXT DEFAULT 'scheduled', -- "scheduled", "live", "finished", "postponed"
    competition TEXT,             -- "Premier League", "Champions League"
    matchday INTEGER,
    venue TEXT,
    attendance INTEGER,
    referee TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- STATISTICS & EVENTS
-- ============================================

-- Player Statistics (per game)
CREATE TABLE IF NOT EXISTS player_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    game_id INTEGER NOT NULL REFERENCES games(id),
    minutes_played INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    shots INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    passes INTEGER DEFAULT 0,
    pass_accuracy REAL,           -- Percentage 0-100
    tackles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    fouls_committed INTEGER DEFAULT 0,
    fouls_drawn INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    rating REAL,                  -- Match rating 0-10
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, game_id)
);

-- Game Events (goals, cards, substitutions)
CREATE TABLE IF NOT EXISTS game_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(id),
    player_id INTEGER REFERENCES players(id),
    event_type TEXT NOT NULL,     -- "goal", "assist", "yellow_card", "red_card", "substitution_in", "substitution_out", "penalty_scored", "penalty_missed", "own_goal"
    minute INTEGER,
    extra_time_minute INTEGER,    -- For 90+3 format
    details TEXT,                 -- JSON for additional context
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INJURIES & TRANSFERS
-- ============================================

-- Injuries
CREATE TABLE IF NOT EXISTS injuries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    injury_type TEXT NOT NULL,    -- "Hamstring", "ACL", "Ankle"
    severity TEXT,                -- "Minor", "Moderate", "Severe"
    occurred_date DATE,
    expected_return DATE,
    actual_return DATE,
    status TEXT DEFAULT 'active', -- "active", "recovered", "unknown"
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Transfers
CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    from_team_id INTEGER REFERENCES teams(id),
    to_team_id INTEGER REFERENCES teams(id),
    transfer_type TEXT,           -- "permanent", "loan", "loan_return", "free"
    fee_eur INTEGER,              -- Transfer fee in euros
    contract_years INTEGER,
    announced_date DATE,
    effective_date DATE,
    status TEXT DEFAULT 'completed', -- "rumor", "negotiating", "completed", "cancelled"
    source TEXT,                  -- Where we got this info
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- STANDINGS & FORM
-- ============================================

-- League Standings (snapshot)
CREATE TABLE IF NOT EXISTS standings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    league TEXT NOT NULL,
    season TEXT NOT NULL,         -- "2024-25"
    position INTEGER,
    played INTEGER DEFAULT 0,
    won INTEGER DEFAULT 0,
    drawn INTEGER DEFAULT 0,
    lost INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    goal_difference INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    form TEXT,                    -- "WWDLW" (last 5 games)
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, league, season)
);

-- ============================================
-- NEWS & UPDATES
-- ============================================

-- News Articles (for context)
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,                 -- AI-generated summary
    source TEXT,                  -- "ESPN", "BBC Sport"
    source_url TEXT,
    published_at DATETIME,
    category TEXT,                -- "transfer", "injury", "match_report", "preview"
    related_team_ids TEXT,        -- JSON array of team IDs
    related_player_ids TEXT,      -- JSON array of player IDs
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- FULL-TEXT SEARCH (FTS5)
-- RAG retrieval happens here
-- ============================================

-- Players FTS
CREATE VIRTUAL TABLE IF NOT EXISTS players_fts USING fts5(
    name,
    position,
    nationality,
    content='players',
    content_rowid='id'
);

-- Teams FTS
CREATE VIRTUAL TABLE IF NOT EXISTS teams_fts USING fts5(
    name,
    short_name,
    league,
    country,
    content='teams',
    content_rowid='id'
);

-- News FTS (main RAG source)
CREATE VIRTUAL TABLE IF NOT EXISTS news_fts USING fts5(
    title,
    content,
    summary,
    category,
    content='news',
    content_rowid='id'
);

-- ============================================
-- TRIGGERS FOR FTS SYNC
-- Keeps FTS tables in sync with main tables
-- ============================================

-- Players FTS triggers
CREATE TRIGGER IF NOT EXISTS players_ai AFTER INSERT ON players BEGIN
    INSERT INTO players_fts(rowid, name, position, nationality)
    VALUES (new.id, new.name, new.position, new.nationality);
END;

CREATE TRIGGER IF NOT EXISTS players_ad AFTER DELETE ON players BEGIN
    INSERT INTO players_fts(players_fts, rowid, name, position, nationality)
    VALUES ('delete', old.id, old.name, old.position, old.nationality);
END;

CREATE TRIGGER IF NOT EXISTS players_au AFTER UPDATE ON players BEGIN
    INSERT INTO players_fts(players_fts, rowid, name, position, nationality)
    VALUES ('delete', old.id, old.name, old.position, old.nationality);
    INSERT INTO players_fts(rowid, name, position, nationality)
    VALUES (new.id, new.name, new.position, new.nationality);
END;

-- Teams FTS triggers
CREATE TRIGGER IF NOT EXISTS teams_ai AFTER INSERT ON teams BEGIN
    INSERT INTO teams_fts(rowid, name, short_name, league, country)
    VALUES (new.id, new.name, new.short_name, new.league, new.country);
END;

CREATE TRIGGER IF NOT EXISTS teams_ad AFTER DELETE ON teams BEGIN
    INSERT INTO teams_fts(teams_fts, rowid, name, short_name, league, country)
    VALUES ('delete', old.id, old.name, old.short_name, old.league, old.country);
END;

CREATE TRIGGER IF NOT EXISTS teams_au AFTER UPDATE ON teams BEGIN
    INSERT INTO teams_fts(teams_fts, rowid, name, short_name, league, country)
    VALUES ('delete', old.id, old.name, old.short_name, old.league, old.country);
    INSERT INTO teams_fts(rowid, name, short_name, league, country)
    VALUES (new.id, new.name, new.short_name, new.league, new.country);
END;

-- News FTS triggers
CREATE TRIGGER IF NOT EXISTS news_ai AFTER INSERT ON news BEGIN
    INSERT INTO news_fts(rowid, title, content, summary, category)
    VALUES (new.id, new.title, new.content, new.summary, new.category);
END;

CREATE TRIGGER IF NOT EXISTS news_ad AFTER DELETE ON news BEGIN
    INSERT INTO news_fts(news_fts, rowid, title, content, summary, category)
    VALUES ('delete', old.id, old.title, old.content, old.summary, old.category);
END;

CREATE TRIGGER IF NOT EXISTS news_au AFTER UPDATE ON news BEGIN
    INSERT INTO news_fts(news_fts, rowid, title, content, summary, category)
    VALUES ('delete', old.id, old.title, old.content, old.summary, old.category);
    INSERT INTO news_fts(rowid, title, content, summary, category)
    VALUES (new.id, new.title, new.content, new.summary, new.category);
END;

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);
CREATE INDEX IF NOT EXISTS idx_games_date ON games(date);
CREATE INDEX IF NOT EXISTS idx_games_teams ON games(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_game ON player_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_injuries_player ON injuries(player_id);
CREATE INDEX IF NOT EXISTS idx_injuries_status ON injuries(status);
CREATE INDEX IF NOT EXISTS idx_transfers_player ON transfers(player_id);
CREATE INDEX IF NOT EXISTS idx_standings_team ON standings(team_id);
CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at);
CREATE INDEX IF NOT EXISTS idx_news_category ON news(category);

-- ============================================
-- IMPLEMENTATION GAP TRACKER (Meta-Tool)
-- Prevents "forgotten implementations" pattern
-- ============================================

CREATE TABLE IF NOT EXISTS implementation_gaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_name TEXT NOT NULL,
    source_doc TEXT,              -- Which .md/.ctx file defined it
    source_line INTEGER,          -- Line number in source doc
    status TEXT DEFAULT 'pending', -- pending, in_progress, completed, deferred
    priority TEXT DEFAULT 'medium', -- critical, high, medium, low
    assigned_phase TEXT,          -- Which phase it belongs to
    completed_at DATETIME,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gaps_status ON implementation_gaps(status);
CREATE INDEX IF NOT EXISTS idx_gaps_priority ON implementation_gaps(priority);

-- ============================================
-- SECURITY INFRASTRUCTURE
-- Session state machine + logging
-- ============================================

-- Session state tracking for escalation
CREATE TABLE IF NOT EXISTS session_state (
    session_id TEXT PRIMARY KEY,
    state TEXT DEFAULT 'normal',   -- normal, warned, cautious, escalated, probation
    injection_count INTEGER DEFAULT 0,
    clean_query_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Security event log (injection attempts)
CREATE TABLE IF NOT EXISTS security_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    attempt_number INTEGER,
    query_hash TEXT,              -- SHA256 hash, not raw query
    pattern_matched TEXT,
    escalation_level TEXT,
    response_type TEXT            -- snap_back, security_persona, normal
);

CREATE INDEX IF NOT EXISTS idx_security_session ON security_log(session_id);
CREATE INDEX IF NOT EXISTS idx_security_timestamp ON security_log(timestamp);

-- ============================================
-- TRIVIA SYSTEM
-- Fan engagement through quizzes
-- ============================================

CREATE TABLE IF NOT EXISTS trivia_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER REFERENCES teams(id),
    category TEXT,                -- legends, history, transfers, rivalries, stats
    difficulty TEXT DEFAULT 'medium', -- easy, medium, hard, expert
    question TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    wrong_answers TEXT,           -- JSON array of 3 wrong answers
    explanation TEXT,             -- Why this answer is correct
    times_asked INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trivia_team ON trivia_questions(team_id);
CREATE INDEX IF NOT EXISTS idx_trivia_category ON trivia_questions(category);
CREATE INDEX IF NOT EXISTS idx_trivia_difficulty ON trivia_questions(difficulty);

-- ============================================
-- EXAMPLE QUERIES (for RAG reference)
-- ============================================

-- Find player by name (FTS)
-- SELECT * FROM players WHERE id IN (SELECT rowid FROM players_fts WHERE players_fts MATCH 'Haaland');

-- Find recent injuries
-- SELECT p.name, i.* FROM injuries i JOIN players p ON i.player_id = p.id WHERE i.status = 'active' ORDER BY i.occurred_date DESC;

-- Find team's recent games
-- SELECT * FROM games WHERE (home_team_id = ? OR away_team_id = ?) AND status = 'finished' ORDER BY date DESC LIMIT 5;

-- Search news (RAG retrieval)
-- SELECT * FROM news WHERE id IN (SELECT rowid FROM news_fts WHERE news_fts MATCH 'Manchester United transfer') ORDER BY published_at DESC LIMIT 10;

-- Get player with stats
-- SELECT p.*, SUM(ps.goals) as total_goals, SUM(ps.assists) as total_assists FROM players p LEFT JOIN player_stats ps ON p.id = ps.player_id WHERE p.id = ? GROUP BY p.id;
