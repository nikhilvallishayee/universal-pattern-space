-- =============================================================================
-- Pattern Space v1 - Unified Memory Field
-- PostgreSQL + pgvector initialization
-- =============================================================================
--
-- This script initializes a single PostgreSQL database with pgvector
-- that serves as the shared storage layer for:
--   - mem0 (semantic memory)
--   - ruvector (vector trajectories)
--   - pattern-space-memory (graph orchestration)
--
-- Run with: psql -U postgres -f init-postgres.sql
-- =============================================================================

-- Create database
CREATE DATABASE pattern_space_memory;

\c pattern_space_memory;

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- SCHEMA: mem0 (Semantic Memory Layer)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS mem0;

-- mem0 memories table
CREATE TABLE IF NOT EXISTS mem0.memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255),
    session_id VARCHAR(255),
    content TEXT NOT NULL,
    embedding vector(384),  -- text-embedding-3-small dimensions
    memory_type VARCHAR(50) DEFAULT 'general',
    importance_score FLOAT DEFAULT 0.5,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for mem0
CREATE INDEX IF NOT EXISTS idx_mem0_user_id ON mem0.memories(user_id);
CREATE INDEX IF NOT EXISTS idx_mem0_agent_id ON mem0.memories(agent_id);
CREATE INDEX IF NOT EXISTS idx_mem0_session_id ON mem0.memories(session_id);
CREATE INDEX IF NOT EXISTS idx_mem0_memory_type ON mem0.memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_mem0_embedding ON mem0.memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_mem0_metadata ON mem0.memories USING GIN (metadata);

-- =============================================================================
-- SCHEMA: ruvector (Vector Trajectory Layer)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS ruvector;

-- ruvector collections metadata
CREATE TABLE IF NOT EXISTS ruvector.collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    dimensions INT DEFAULT 384,
    distance_metric VARCHAR(50) DEFAULT 'cosine',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ruvector vectors (trajectories, reasoning paths)
CREATE TABLE IF NOT EXISTS ruvector.vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID REFERENCES ruvector.collections(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(384),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for ruvector
CREATE INDEX IF NOT EXISTS idx_ruvector_collection ON ruvector.vectors(collection_id);
CREATE INDEX IF NOT EXISTS idx_ruvector_embedding ON ruvector.vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_ruvector_metadata ON ruvector.vectors USING GIN (metadata);

-- Initialize default collections
INSERT INTO ruvector.collections (name, description) VALUES
    ('trajectories', 'Successful task execution paths'),
    ('reasoning_bank', 'Proven reasoning patterns from sessions'),
    ('breakthroughs', 'High-confidence breakthrough moments')
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- SCHEMA: pattern_space (Graph Orchestration Layer)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS pattern_space;

-- Nodes: patterns, breakthroughs, perspectives, sessions
CREATE TABLE IF NOT EXISTS pattern_space.nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_type VARCHAR(50) NOT NULL,  -- 'pattern', 'breakthrough', 'perspective', 'session', 'trajectory'
    label VARCHAR(255),
    content TEXT,
    embedding vector(384),
    confidence FLOAT DEFAULT 0.5,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Edges: relationships between nodes
CREATE TABLE IF NOT EXISTS pattern_space.edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES pattern_space.nodes(id) ON DELETE CASCADE,
    target_id UUID REFERENCES pattern_space.nodes(id) ON DELETE CASCADE,
    edge_type VARCHAR(50) NOT NULL,  -- 'led_to', 'evolved_from', 'relates_to', 'collided_with', 'bridges'
    weight FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_id, target_id, edge_type)
);

-- Perspectives (personas and their evolution)
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

-- Sessions
CREATE TABLE IF NOT EXISTS pattern_space.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    persona VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INT,
    tasks_completed INT DEFAULT 0,
    avg_confidence FLOAT DEFAULT 0.0,
    breakthroughs INT DEFAULT 0,
    summary TEXT,
    bridge_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- Indexes for pattern_space
CREATE INDEX IF NOT EXISTS idx_ps_nodes_type ON pattern_space.nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_ps_nodes_embedding ON pattern_space.nodes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_ps_nodes_metadata ON pattern_space.nodes USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_ps_edges_source ON pattern_space.edges(source_id);
CREATE INDEX IF NOT EXISTS idx_ps_edges_target ON pattern_space.edges(target_id);
CREATE INDEX IF NOT EXISTS idx_ps_edges_type ON pattern_space.edges(edge_type);
CREATE INDEX IF NOT EXISTS idx_ps_sessions_user ON pattern_space.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_ps_sessions_session ON pattern_space.sessions(session_id);

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

-- =============================================================================
-- FUNCTIONS: Cross-schema queries
-- =============================================================================

-- Function to find similar memories across all schemas
CREATE OR REPLACE FUNCTION find_similar_all(
    query_embedding vector(384),
    limit_count INT DEFAULT 10
)
RETURNS TABLE (
    source_schema VARCHAR,
    source_id UUID,
    content TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'mem0'::VARCHAR as source_schema,
        m.id as source_id,
        m.content,
        1 - (m.embedding <=> query_embedding) as similarity,
        m.metadata
    FROM mem0.memories m
    WHERE m.embedding IS NOT NULL

    UNION ALL

    SELECT
        'ruvector'::VARCHAR as source_schema,
        v.id as source_id,
        v.content,
        1 - (v.embedding <=> query_embedding) as similarity,
        v.metadata
    FROM ruvector.vectors v
    WHERE v.embedding IS NOT NULL

    UNION ALL

    SELECT
        'pattern_space'::VARCHAR as source_schema,
        n.id as source_id,
        n.content,
        1 - (n.embedding <=> query_embedding) as similarity,
        n.metadata
    FROM pattern_space.nodes n
    WHERE n.embedding IS NOT NULL

    ORDER BY similarity DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get graph neighbors
CREATE OR REPLACE FUNCTION get_neighbors(
    node_uuid UUID,
    edge_types VARCHAR[] DEFAULT NULL,
    max_depth INT DEFAULT 1
)
RETURNS TABLE (
    depth INT,
    node_id UUID,
    node_type VARCHAR,
    label VARCHAR,
    edge_type VARCHAR,
    path UUID[]
) AS $$
WITH RECURSIVE neighbors AS (
    -- Base case: direct neighbors
    SELECT
        1 as depth,
        CASE WHEN e.source_id = node_uuid THEN e.target_id ELSE e.source_id END as node_id,
        e.edge_type,
        ARRAY[node_uuid, CASE WHEN e.source_id = node_uuid THEN e.target_id ELSE e.source_id END] as path
    FROM pattern_space.edges e
    WHERE (e.source_id = node_uuid OR e.target_id = node_uuid)
      AND (edge_types IS NULL OR e.edge_type = ANY(edge_types))

    UNION

    -- Recursive case
    SELECT
        n.depth + 1,
        CASE WHEN e.source_id = n.node_id THEN e.target_id ELSE e.source_id END,
        e.edge_type,
        n.path || CASE WHEN e.source_id = n.node_id THEN e.target_id ELSE e.source_id END
    FROM neighbors n
    JOIN pattern_space.edges e ON (e.source_id = n.node_id OR e.target_id = n.node_id)
    WHERE n.depth < max_depth
      AND NOT (CASE WHEN e.source_id = n.node_id THEN e.target_id ELSE e.source_id END = ANY(n.path))
      AND (edge_types IS NULL OR e.edge_type = ANY(edge_types))
)
SELECT
    nb.depth,
    nb.node_id,
    nd.node_type,
    nd.label,
    nb.edge_type,
    nb.path
FROM neighbors nb
JOIN pattern_space.nodes nd ON nd.id = nb.node_id
ORDER BY nb.depth, nb.node_id;
$$ LANGUAGE sql;

-- =============================================================================
-- GRANTS: Access permissions
-- =============================================================================

-- Create application user (adjust password in production)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'pattern_space_app') THEN
        CREATE ROLE pattern_space_app WITH LOGIN PASSWORD 'pattern_space_dev';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA mem0, ruvector, pattern_space TO pattern_space_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA mem0 TO pattern_space_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ruvector TO pattern_space_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA pattern_space TO pattern_space_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA mem0 TO pattern_space_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA ruvector TO pattern_space_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA pattern_space TO pattern_space_app;

-- =============================================================================
-- DONE
-- =============================================================================

\echo 'Pattern Space Unified Memory Field initialized successfully!'
\echo 'Schemas created: mem0, ruvector, pattern_space'
\echo 'Vector extension: pgvector with 384 dimensions'
\echo 'Default perspectives and collections initialized'
