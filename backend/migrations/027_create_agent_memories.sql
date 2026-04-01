CREATE TABLE IF NOT EXISTS agent_memories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL DEFAULT 'preference',
    memory_key VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    importance INTEGER NOT NULL DEFAULT 1,
    access_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE UNIQUE INDEX uq_agent_memory_user_key ON agent_memories(user_id, memory_key);
CREATE INDEX idx_agent_memories_user_category ON agent_memories(user_id, category);
CREATE INDEX idx_agent_memories_user_importance ON agent_memories(user_id, importance DESC);
CREATE INDEX idx_agent_memories_expires ON agent_memories(expires_at) WHERE expires_at IS NOT NULL;
