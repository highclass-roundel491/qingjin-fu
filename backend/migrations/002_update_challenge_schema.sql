DROP TABLE IF EXISTS challenge_submissions CASCADE;
DROP TABLE IF EXISTS daily_challenges CASCADE;

CREATE TABLE daily_challenges (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    poem_id INTEGER NOT NULL REFERENCES poems(id),
    original_content TEXT NOT NULL,
    blank_position INTEGER NOT NULL,
    original_char VARCHAR(10) NOT NULL,
    hint VARCHAR(200),
    difficulty VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_daily_challenges_date ON daily_challenges(date);
CREATE INDEX idx_daily_challenges_poem_id ON daily_challenges(poem_id);

CREATE TABLE challenge_submissions (
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
