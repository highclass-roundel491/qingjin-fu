CREATE TABLE IF NOT EXISTS poets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    dynasty VARCHAR(50) NOT NULL,
    alias VARCHAR(200),
    birth_year VARCHAR(50),
    death_year VARCHAR(50),
    birth_death_desc VARCHAR(100),
    styles TEXT,
    brief TEXT,
    detailed_bio TEXT,
    representative_works TEXT,
    influence_score INTEGER DEFAULT 50,
    poem_count INTEGER DEFAULT 0,
    portrait_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_poets_name_dynasty ON poets(name, dynasty);
CREATE INDEX IF NOT EXISTS idx_poets_name ON poets(name);
CREATE INDEX IF NOT EXISTS idx_poets_dynasty ON poets(dynasty);
CREATE INDEX IF NOT EXISTS idx_poets_influence ON poets(influence_score DESC);
