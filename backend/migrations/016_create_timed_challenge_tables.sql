CREATE TABLE IF NOT EXISTS timed_challenge_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    difficulty VARCHAR(20) NOT NULL DEFAULT 'medium',
    question_type VARCHAR(20) NOT NULL DEFAULT 'mixed',
    total_questions INTEGER NOT NULL DEFAULT 10,
    answered_count INTEGER NOT NULL DEFAULT 0,
    correct_count INTEGER NOT NULL DEFAULT 0,
    total_score INTEGER NOT NULL DEFAULT 0,
    combo INTEGER NOT NULL DEFAULT 0,
    max_combo INTEGER NOT NULL DEFAULT 0,
    time_per_question INTEGER NOT NULL DEFAULT 15,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    exp_gained INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_timed_sessions_user ON timed_challenge_sessions(user_id);
CREATE INDEX idx_timed_sessions_status ON timed_challenge_sessions(status);

CREATE TABLE IF NOT EXISTS timed_challenge_answers (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES timed_challenge_sessions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    question_index INTEGER NOT NULL,
    question_type VARCHAR(20) NOT NULL,
    poem_id INTEGER REFERENCES poems(id),
    question_text TEXT NOT NULL,
    options TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    user_answer TEXT,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    time_spent INTEGER NOT NULL DEFAULT 0,
    score INTEGER NOT NULL DEFAULT 0,
    answered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_timed_answers_session ON timed_challenge_answers(session_id);
CREATE INDEX idx_timed_answers_user ON timed_challenge_answers(user_id);
