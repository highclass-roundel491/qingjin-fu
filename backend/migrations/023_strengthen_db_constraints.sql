DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_poem_favorite_user_poem'
    ) THEN
        ALTER TABLE poem_favorites
        ADD CONSTRAINT uq_poem_favorite_user_poem UNIQUE (user_id, poem_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_poems_genre ON poems(genre);
CREATE INDEX IF NOT EXISTS idx_timed_sessions_user_status_started_at ON timed_challenge_sessions(user_id, status, started_at);
CREATE INDEX IF NOT EXISTS idx_timed_sessions_status_started_at ON timed_challenge_sessions(status, started_at);
