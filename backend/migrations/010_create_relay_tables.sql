CREATE TABLE IF NOT EXISTS relay_rooms (
    id SERIAL PRIMARY KEY,
    room_code VARCHAR(20) UNIQUE NOT NULL,
    host_id INTEGER NOT NULL REFERENCES users(id),
    mode VARCHAR(20) NOT NULL DEFAULT 'single',
    difficulty VARCHAR(20) NOT NULL DEFAULT 'normal',
    status VARCHAR(20) NOT NULL DEFAULT 'waiting',
    max_rounds INTEGER DEFAULT 20,
    time_limit INTEGER DEFAULT 30,
    current_round INTEGER DEFAULT 0,
    next_char VARCHAR(10),
    started_at TIMESTAMP WITH TIME ZONE,
    finished_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_relay_rooms_room_code ON relay_rooms(room_code);
CREATE INDEX IF NOT EXISTS idx_relay_rooms_host_id ON relay_rooms(host_id);
CREATE INDEX IF NOT EXISTS idx_relay_rooms_status ON relay_rooms(status);

CREATE TABLE IF NOT EXISTS relay_players (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES relay_rooms(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    score INTEGER DEFAULT 0,
    combo INTEGER DEFAULT 0,
    max_combo INTEGER DEFAULT 0,
    rounds_played INTEGER DEFAULT 0,
    total_time INTEGER DEFAULT 0,
    hints_used INTEGER DEFAULT 0,
    is_host BOOLEAN DEFAULT FALSE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_relay_players_room_id ON relay_players(room_id);
CREATE INDEX IF NOT EXISTS idx_relay_players_user_id ON relay_players(user_id);

CREATE TABLE IF NOT EXISTS relay_rounds (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES relay_rooms(id),
    round_number INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    verse VARCHAR(200) NOT NULL,
    poem_title VARCHAR(200),
    author VARCHAR(100),
    match_type VARCHAR(20),
    score INTEGER DEFAULT 0,
    time_used INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_relay_rounds_room_id ON relay_rounds(room_id);
