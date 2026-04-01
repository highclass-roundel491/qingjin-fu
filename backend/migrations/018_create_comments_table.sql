CREATE TABLE IF NOT EXISTS work_comments (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES work_comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_work_comments_work_id ON work_comments(work_id);
CREATE INDEX IF NOT EXISTS idx_work_comments_user_id ON work_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_work_comments_parent_id ON work_comments(parent_id);

CREATE TABLE IF NOT EXISTS work_comment_likes (
    id SERIAL PRIMARY KEY,
    comment_id INTEGER NOT NULL REFERENCES work_comments(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(comment_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_work_comment_likes_comment_id ON work_comment_likes(comment_id);

ALTER TABLE works ADD COLUMN IF NOT EXISTS comment_count INTEGER DEFAULT 0;
