CREATE TABLE IF NOT EXISTS agent_memory_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL DEFAULT 'poem_chat',
    dedup_key VARCHAR(80) NOT NULL UNIQUE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    extracted_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_agent_memory_events_user_status ON agent_memory_events(user_id, status);
CREATE INDEX idx_agent_memory_events_status_retry ON agent_memory_events(status, next_retry_at);
CREATE INDEX idx_agent_memory_events_created_at ON agent_memory_events(created_at DESC);
