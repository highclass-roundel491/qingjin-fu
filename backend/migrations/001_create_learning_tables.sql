CREATE TABLE IF NOT EXISTS learning_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    poem_id INTEGER NOT NULL REFERENCES poems(id),
    action VARCHAR(20) NOT NULL,
    duration INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_learning_records_user_id ON learning_records(user_id);
CREATE INDEX idx_learning_records_poem_id ON learning_records(poem_id);

CREATE TABLE IF NOT EXISTS poem_favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    poem_id INTEGER NOT NULL REFERENCES poems(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, poem_id)
);

CREATE INDEX idx_poem_favorites_user_id ON poem_favorites(user_id);
CREATE INDEX idx_poem_favorites_poem_id ON poem_favorites(poem_id);

CREATE TABLE IF NOT EXISTS user_stats (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
    total_learned INTEGER DEFAULT 0,
    total_favorites INTEGER DEFAULT 0,
    study_time INTEGER DEFAULT 0,
    streak_days INTEGER DEFAULT 0,
    last_study_date TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_stats_user_id ON user_stats(user_id);

CREATE TABLE IF NOT EXISTS daily_challenges (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    sentence VARCHAR(200) NOT NULL,
    blank_position INTEGER NOT NULL,
    correct_answers VARCHAR(100) NOT NULL,
    hint VARCHAR(200),
    difficulty VARCHAR(20) DEFAULT 'medium',
    category VARCHAR(50),
    reference_poem_ids VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_daily_challenges_date ON daily_challenges(date);

CREATE TABLE IF NOT EXISTS challenge_submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    challenge_id INTEGER NOT NULL REFERENCES daily_challenges(id),
    answer VARCHAR(10) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    score INTEGER DEFAULT 0,
    ai_feedback TEXT,
    exp_gained INTEGER DEFAULT 0,
    points_gained INTEGER DEFAULT 0,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, challenge_id)
);

CREATE INDEX idx_challenge_submissions_user_id ON challenge_submissions(user_id);
CREATE INDEX idx_challenge_submissions_challenge_id ON challenge_submissions(challenge_id);
