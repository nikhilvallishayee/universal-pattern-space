-- =============================================================================
-- Pattern Space v1 - PostgreSQL Bootstrap for mem0
-- =============================================================================
--
-- This script bootstraps PostgreSQL with pgvector for mem0.
-- mem0 handles its own table creation when initialized.
--
-- Run with: psql -U postgres -f init-postgres.sql
-- =============================================================================

-- Create database (if running as superuser)
-- Note: You may need to create this manually first
-- CREATE DATABASE pattern_space_memory;

-- Connect to the database
\c pattern_space_memory;

-- Enable pgvector extension (required for mem0 vector storage)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- APPLICATION USER
-- =============================================================================

-- Create application user (adjust password in production)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'pattern_space_app') THEN
        CREATE ROLE pattern_space_app WITH LOGIN PASSWORD 'pattern_space_dev';
    END IF;
END
$$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE pattern_space_memory TO pattern_space_app;

-- =============================================================================
-- OPTIONAL: Create schema for pattern-space-specific tables
-- (mem0 creates its own tables, this is for any custom extensions)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS pattern_space;
GRANT ALL PRIVILEGES ON SCHEMA pattern_space TO pattern_space_app;

-- Perspectives tracking (used by pattern-space-memory MCP for stats)
CREATE TABLE IF NOT EXISTS pattern_space.perspectives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    tasks_completed INT DEFAULT 0,
    avg_confidence FLOAT DEFAULT 0.0,
    total_breakthroughs INT DEFAULT 0,
    evolution_history JSONB DEFAULT '[]',
    last_active TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Initialize default perspectives
INSERT INTO pattern_space.perspectives (name, description) VALUES
    ('weaver', 'Pattern recognition and synthesis'),
    ('maker', 'Implementation and building'),
    ('checker', 'Validation and edge cases'),
    ('deep-thought', 'Meta-cognition and systems thinking'),
    ('observer-guardian', 'Meta-awareness and boundaries'),
    ('explorer-exploiter', 'Resource optimization'),
    ('scribe', 'Memory and pattern accumulation'),
    ('full-council', 'All perspectives active')
ON CONFLICT (name) DO NOTHING;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA pattern_space TO pattern_space_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA pattern_space TO pattern_space_app;

-- =============================================================================
-- DONE
-- =============================================================================

\echo 'Pattern Space PostgreSQL bootstrap complete!'
\echo 'Extensions: pgvector, uuid-ossp'
\echo 'User: pattern_space_app'
\echo 'mem0 will create its own tables when initialized'
