CREATE TABLE IF NOT EXISTS poet_relation_cache (
    id SERIAL PRIMARY KEY,
    poet_a VARCHAR(50) NOT NULL,
    poet_b VARCHAR(50) NOT NULL,
    cache_key VARCHAR(120) NOT NULL UNIQUE,
    summary TEXT NOT NULL DEFAULT '',
    sections JSONB NOT NULL DEFAULT '[]',
    known_relation VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_poet_relation_cache_key ON poet_relation_cache(cache_key);
CREATE INDEX idx_poet_relation_cache_poets ON poet_relation_cache(poet_a, poet_b);
