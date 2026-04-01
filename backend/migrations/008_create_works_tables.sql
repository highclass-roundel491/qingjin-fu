CREATE TABLE IF NOT EXISTS works (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    genre VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    ai_grammar_score INTEGER,
    ai_artistic_score INTEGER,
    ai_total_score INTEGER,
    ai_feedback TEXT,
    like_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

CREATE INDEX idx_works_user_id ON works(user_id);
CREATE INDEX idx_works_status ON works(status);
CREATE INDEX idx_works_genre ON works(genre);
CREATE INDEX idx_works_published_at ON works(published_at);

CREATE TABLE IF NOT EXISTS work_likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    work_id INTEGER NOT NULL REFERENCES works(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, work_id)
);

CREATE INDEX idx_work_likes_user_id ON work_likes(user_id);
CREATE INDEX idx_work_likes_work_id ON work_likes(work_id);
