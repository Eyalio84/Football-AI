-- NLKE-Compliant Knowledge Graph Schema
-- Migration 001: Initial schema creation
--
-- This schema follows unified-kg.db format for cross-domain compatibility.
-- Critical: source_kg field enables Soccer-AI and Predictor unified queries.

-- ============================================
-- CORE TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    original_id TEXT,
    name TEXT NOT NULL,
    type TEXT,
    description TEXT,
    metadata TEXT,
    source_kg TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_node TEXT NOT NULL,
    to_node TEXT NOT NULL,
    type TEXT,
    weight REAL DEFAULT 1.0,
    metadata TEXT,
    source_kg TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_node) REFERENCES nodes(id),
    FOREIGN KEY (to_node) REFERENCES nodes(id),
    UNIQUE(from_node, to_node, type)
);

CREATE TABLE IF NOT EXISTS embeddings (
    node_id TEXT PRIMARY KEY,
    dimensions TEXT NOT NULL,
    num_dimensions INTEGER,
    method TEXT DEFAULT 'bge-small',
    generated_date TEXT,
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);

-- ============================================
-- LEARNING TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS interaction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    query TEXT NOT NULL,
    command_type TEXT,
    matched_nodes TEXT,
    result_count INTEGER,
    search_mode TEXT,
    response_time_ms INTEGER,
    source_kg TEXT,
    cross_dimensional INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lsh_buckets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bucket_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    hash_table_id INTEGER,
    source_kg TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES nodes(id),
    UNIQUE(bucket_id, node_id, hash_table_id)
);

CREATE TABLE IF NOT EXISTS node_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_node TEXT NOT NULL,
    to_node TEXT NOT NULL,
    transition_count INTEGER DEFAULT 1,
    transition_probability REAL,
    from_dimension TEXT,
    to_dimension TEXT,
    via_edge_type TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_node) REFERENCES nodes(id),
    FOREIGN KEY (to_node) REFERENCES nodes(id),
    UNIQUE(from_node, to_node, via_edge_type)
);

CREATE TABLE IF NOT EXISTS association_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT UNIQUE NOT NULL,
    antecedent TEXT NOT NULL,
    consequent TEXT NOT NULL,
    support REAL,
    confidence REAL,
    lift REAL,
    cross_dimensional INTEGER DEFAULT 0,
    pattern_type TEXT,
    first_observed TIMESTAMP,
    last_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS query_synonyms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_term TEXT NOT NULL,
    synonym TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    source_kg TEXT,
    relationship_type TEXT,
    success_rate REAL,
    UNIQUE(query_term, synonym)
);

CREATE TABLE IF NOT EXISTS tfidf_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL,
    node_id TEXT NOT NULL,
    tf REAL,
    idf REAL,
    tfidf REAL,
    FOREIGN KEY (node_id) REFERENCES nodes(id),
    UNIQUE(term, node_id)
);

CREATE TABLE IF NOT EXISTS umap_coordinates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT UNIQUE NOT NULL,
    x REAL NOT NULL,
    y REAL NOT NULL,
    cluster_id INTEGER,
    cluster_label TEXT,
    source_kg TEXT,
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);

-- ============================================
-- FTS5 FOR HYBRID SEARCH
-- ============================================

CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    name, description, metadata,
    content='nodes',
    content_rowid='rowid'
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_source_kg ON nodes(source_kg);
CREATE INDEX IF NOT EXISTS idx_nodes_type_source ON nodes(type, source_kg);
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);

CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_node);
CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_node);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(type);
CREATE INDEX IF NOT EXISTS idx_edges_source_kg ON edges(source_kg);

CREATE INDEX IF NOT EXISTS idx_tfidf_term ON tfidf_index(term);
CREATE INDEX IF NOT EXISTS idx_tfidf_node ON tfidf_index(node_id);

CREATE INDEX IF NOT EXISTS idx_interaction_session ON interaction_log(session_id);

-- ============================================
-- TRIGGERS FOR FTS SYNC
-- ============================================

CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
    INSERT INTO nodes_fts(rowid, name, description, metadata)
    VALUES (new.rowid, new.name, new.description, new.metadata);
END;

CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, description, metadata)
    VALUES('delete', old.rowid, old.name, old.description, old.metadata);
END;

CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, description, metadata)
    VALUES('delete', old.rowid, old.name, old.description, old.metadata);
    INSERT INTO nodes_fts(rowid, name, description, metadata)
    VALUES (new.rowid, new.name, new.description, new.metadata);
END;
