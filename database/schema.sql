-- VERTICE-CODE DATABASE SCHEMA
-- Multi-tenant SaaS platform with GDPR compliance
-- PostgreSQL 15+ with Row Level Security

-- =============================================================================
-- EXTENSIONS
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- =============================================================================
-- BASE TABLES
-- =============================================================================

-- Workspaces (Tenants)
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,

    -- Billing & Limits
    subscription_plan VARCHAR(50) DEFAULT 'free',
    monthly_token_limit INTEGER DEFAULT 100000,
    storage_limit_gb INTEGER DEFAULT 5,

    -- Encryption (GDPR compliance)
    data_encryption_key BYTEA, -- Encrypted with master key
    key_encryption_version INTEGER DEFAULT 1,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,

    -- Soft delete for GDPR
    deleted_at TIMESTAMP WITH TIME ZONE,
    deletion_reason TEXT
);

-- Users (Google Identity integration)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auth_id VARCHAR(255) UNIQUE NOT NULL,

    -- Profile
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    username VARCHAR(100) UNIQUE,
    avatar_url TEXT,

    -- Workspace membership
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member', -- owner, admin, member

    -- Preferences
    preferences JSONB DEFAULT '{}',
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',

    -- Security
    last_login_at TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    mfa_enabled BOOLEAN DEFAULT false,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,

    -- GDPR compliance
    data_retention_until TIMESTAMP WITH TIME ZONE,
    consent_given_at TIMESTAMP WITH TIME ZONE,
    marketing_consent BOOLEAN DEFAULT false
);

-- Agents (Autonomous AI agents)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,

    -- Identity
    agent_name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) DEFAULT 'generic', -- coder, researcher, devops, etc.
    description TEXT,

    -- API Key (hashed for security)
    api_key_hash VARCHAR(128) UNIQUE NOT NULL,
    key_rotation_required BOOLEAN DEFAULT false,

    -- Capabilities & Limits
    scopes TEXT[] DEFAULT ARRAY['read:memory', 'write:logs'],
    daily_token_budget INTEGER DEFAULT 1000,
    max_concurrent_sessions INTEGER DEFAULT 5,

    -- Status
    is_active BOOLEAN DEFAULT true,
    last_seen_at TIMESTAMP WITH TIME ZONE,
    total_tokens_used INTEGER DEFAULT 0,

    -- Configuration
    system_prompt TEXT,
    model_preferences JSONB DEFAULT '{}',
    custom_instructions TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    -- GDPR compliance
    data_encryption_key BYTEA,
    retention_policy VARCHAR(50) DEFAULT 'standard' -- standard, extended, minimal
);

-- =============================================================================
-- VECTOR DATABASE INTEGRATION
-- =============================================================================

-- Knowledge base entries (RAG data)
CREATE TABLE knowledge_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,

    -- Content
    content_type VARCHAR(50) NOT NULL, -- document, conversation, code, etc.
    title VARCHAR(500),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',

    -- Vector embeddings (stored in external vector DB)
    vector_id VARCHAR(255), -- Reference to Qdrant/Pinecone ID
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-ada-002',
    content_hash VARCHAR(64), -- For deduplication

    -- Access control
    access_level VARCHAR(50) DEFAULT 'workspace', -- workspace, team, private
    owner_id UUID REFERENCES users(id),

    -- Encryption (GDPR)
    is_encrypted BOOLEAN DEFAULT false,
    encryption_key_version INTEGER DEFAULT 1,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    last_accessed_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- BILLING & USAGE TRACKING
-- =============================================================================

-- Usage records (for billing)
CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,

    -- What was used
    resource_type VARCHAR(100) NOT NULL, -- llm_tokens, storage_gb, api_calls
    resource_id VARCHAR(255), -- model name, file ID, etc.

    -- Quantities
    quantity_used DECIMAL(15,6) NOT NULL,
    unit VARCHAR(50) NOT NULL, -- tokens, gb, calls

    -- Cost calculation
    unit_cost DECIMAL(10,6), -- Cost per unit
    total_cost DECIMAL(12,6), -- Pre-calculated total

    -- Attribution
    user_id UUID REFERENCES users(id),
    agent_id UUID REFERENCES agents(id),
    session_id VARCHAR(255),

    -- Metadata
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    billing_period DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Subscription management
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID UNIQUE NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,

    -- Stripe integration
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255) NOT NULL,

    -- Plan details
    plan_name VARCHAR(100) NOT NULL,
    plan_interval VARCHAR(20) DEFAULT 'month', -- month, year
    unit_amount INTEGER NOT NULL, -- Cents
    currency VARCHAR(3) DEFAULT 'usd',

    -- Status
    status VARCHAR(50) NOT NULL, -- active, canceled, past_due, etc.
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,

    -- Usage limits
    token_limit INTEGER,
    storage_limit_gb INTEGER,
    api_call_limit INTEGER,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    canceled_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- AUDIT & COMPLIANCE
-- =============================================================================

-- Audit log (GDPR Article 30)
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,

    -- Event details
    event_type VARCHAR(100) NOT NULL,
    event_description TEXT,
    severity VARCHAR(20) DEFAULT 'info', -- debug, info, warn, error

    -- Actor information
    actor_type VARCHAR(50) NOT NULL, -- user, agent, system
    actor_id VARCHAR(255), -- User ID, Agent ID, or system identifier
    actor_ip INET,

    -- Resource affected
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),

    -- Event data
    old_values JSONB,
    new_values JSONB,
    metadata JSONB DEFAULT '{}',

    -- Compliance
    gdpr_processing BOOLEAN DEFAULT false,
    data_subject_id VARCHAR(255), -- For GDPR tracking

    -- AI Safety & ISO 42001 (Extended for LLM interactions)
    ai_interaction BOOLEAN DEFAULT false,
    input_prompt TEXT, -- Raw input prompt for AI safety auditing
    output_generated TEXT, -- Raw output from AI model
    model_used VARCHAR(100), -- LLM model identifier (gpt-4, claude-3, etc.)
    latency_ms INTEGER, -- Response time in milliseconds
    token_count INTEGER, -- Number of tokens used
    cost_cents DECIMAL(8,4), -- Cost in cents for this interaction
    safety_flags JSONB DEFAULT '{}', -- Detected safety violations
    bias_score DECIMAL(3,2), -- Fairness score (0.0-1.0)
    content_filter_triggered BOOLEAN DEFAULT false,

    -- Timestamp (immutable)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) WITH (fillfactor = 70); -- Optimize for inserts

-- Data subject requests (GDPR)
CREATE TABLE gdpr_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,

    -- Request details
    request_type VARCHAR(50) NOT NULL, -- access, rectification, erasure, etc.
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, rejected

    -- Data subject
    data_subject_id VARCHAR(255) NOT NULL, -- Email or user identifier
    data_subject_type VARCHAR(50) DEFAULT 'user', -- user, agent

    -- Request content
    request_details TEXT,
    supporting_evidence TEXT,

    -- Processing
    assigned_to UUID REFERENCES users(id),
    completed_at TIMESTAMP WITH TIME ZONE,
    completion_notes TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    requested_by UUID REFERENCES users(id)
);

-- =============================================================================
-- INDEXES & CONSTRAINTS
-- =============================================================================

-- Performance indexes
CREATE INDEX CONCURRENTLY idx_workspaces_slug ON workspaces(slug);
CREATE INDEX CONCURRENTLY idx_users_auth_id ON users(auth_id);
CREATE INDEX CONCURRENTLY idx_users_workspace_id ON users(workspace_id);
CREATE INDEX CONCURRENTLY idx_agents_workspace_id ON agents(workspace_id);
CREATE INDEX CONCURRENTLY idx_agents_api_key_hash ON agents(api_key_hash);
CREATE INDEX CONCURRENTLY idx_knowledge_workspace_id ON knowledge_entries(workspace_id);
CREATE INDEX CONCURRENTLY idx_usage_workspace_period ON usage_records(workspace_id, billing_period);
CREATE INDEX CONCURRENTLY idx_audit_workspace_created ON audit_log(workspace_id, created_at DESC);

-- Unique constraints
ALTER TABLE workspaces ADD CONSTRAINT workspaces_slug_unique UNIQUE (slug);
ALTER TABLE users ADD CONSTRAINT users_auth_id_unique UNIQUE (auth_id);
ALTER TABLE agents ADD CONSTRAINT agents_api_key_hash_unique UNIQUE (api_key_hash);

-- =============================================================================
-- ROW LEVEL SECURITY (RLS)
-- =============================================================================

-- Enable RLS on all tenant-scoped tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE gdpr_requests ENABLE ROW LEVEL SECURITY;

-- RLS Policies will be created by application code based on user context

-- =============================================================================
-- FUNCTIONS & TRIGGERS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to relevant tables
CREATE TRIGGER update_workspaces_updated_at BEFORE UPDATE ON workspaces
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function for GDPR-compliant data deletion
CREATE OR REPLACE FUNCTION gdpr_safe_delete(target_table TEXT, record_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    delete_query TEXT;
BEGIN
    -- Build dynamic query for safe deletion
    delete_query := format('UPDATE %I SET deleted_at = NOW() WHERE id = $1 AND deleted_at IS NULL', target_table);
    EXECUTE delete_query USING record_id;

    -- Return success
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert default workspace for development
INSERT INTO workspaces (name, slug, description) VALUES
('Default Workspace', 'default', 'Default workspace for development and testing');

-- Create indexes after data insertion for better performance
REINDEX TABLE workspaces;
REINDEX TABLE users;
REINDEX TABLE agents;