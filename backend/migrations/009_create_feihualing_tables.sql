CREATE TABLE IF NOT EXISTS feihualing_games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'playing',
    user_score INTEGER DEFAULT 0,
    ai_score INTEGER DEFAULT 0,
    total_rounds INTEGER DEFAULT 0,
    result VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feihualing_rounds (
    id SERIAL PRIMARY KEY,
    game_id UUID NOT NULL REFERENCES feihualing_games(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    player VARCHAR(10) NOT NULL,
    poem_content TEXT NOT NULL,
    poem_id INTEGER REFERENCES poems(id),
    response_time INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_feihualing_games_user_id ON feihualing_games(user_id);
CREATE INDEX idx_feihualing_games_created_at ON feihualing_games(created_at DESC);
CREATE INDEX idx_feihualing_rounds_game_id ON feihualing_rounds(game_id);
