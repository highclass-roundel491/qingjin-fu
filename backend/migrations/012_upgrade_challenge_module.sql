ALTER TABLE daily_challenges
    ADD COLUMN IF NOT EXISTS challenge_type VARCHAR(20) NOT NULL DEFAULT 'fill_blank',
    ADD COLUMN IF NOT EXISTS creator_id INTEGER REFERENCES users(id),
    ADD COLUMN IF NOT EXISTS is_daily BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS response_count INTEGER DEFAULT 0;

ALTER TABLE daily_challenges
    ALTER COLUMN date DROP NOT NULL;

DROP INDEX IF EXISTS ix_daily_challenges_date;
CREATE INDEX IF NOT EXISTS ix_daily_challenges_challenge_type ON daily_challenges(challenge_type);
CREATE INDEX IF NOT EXISTS ix_daily_challenges_creator_id ON daily_challenges(creator_id);
CREATE INDEX IF NOT EXISTS ix_daily_challenges_date ON daily_challenges(date);

ALTER TABLE challenge_submissions
    ADD COLUMN IF NOT EXISTS content TEXT,
    ADD COLUMN IF NOT EXISTS likes_count INTEGER DEFAULT 0;

UPDATE daily_challenges SET is_daily = TRUE WHERE date IS NOT NULL;
UPDATE daily_challenges SET challenge_type = 'fill_blank' WHERE challenge_type IS NULL;
