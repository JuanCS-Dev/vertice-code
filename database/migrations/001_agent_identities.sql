-- Migration: 001_agent_identities.sql
-- Description: Separate Agent Identity (Auth) from Agent Configuration (Logic)
-- Compliant with: Code Constitution v2.0 (Single Responsibility)

-- 1. Create specialized table for Agent Identities (Machine-to-Machine Auth)
CREATE TABLE IF NOT EXISTS agent_identities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE NOT NULL,
    
    -- Identity
    agent_name VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(255) NOT NULL UNIQUE, -- Store only SHA-256 hash
    
    -- Security & Limits (Circuit Breakers)
    scopes JSONB DEFAULT '["read:memory", "write:logs"]'::jsonb,
    daily_budget_cents INTEGER DEFAULT 1000 CHECK (daily_budget_cents > 0),
    
    -- Lifecycle
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE
);

-- 2. Performance Indexes
CREATE INDEX IF NOT EXISTS idx_agent_identities_api_key_hash ON agent_identities(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_agent_identities_workspace_id ON agent_identities(workspace_id);

-- 3. Trigger for updated_at
DROP TRIGGER IF EXISTS update_agent_identities_updated_at ON agent_identities;
CREATE TRIGGER update_agent_identities_updated_at BEFORE UPDATE ON agent_identities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 4. Enable RLS
ALTER TABLE agent_identities ENABLE ROW LEVEL SECURITY;

-- Note: The existing 'agents' table should eventually be refactored to 'agent_profiles'
-- linking back to 'agent_identities' for configuration, or deprecated if redundant.
