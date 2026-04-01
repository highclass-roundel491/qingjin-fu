UPDATE achievements
SET is_active = TRUE
WHERE is_active IS NULL;

ALTER TABLE achievements
ALTER COLUMN is_active SET DEFAULT TRUE;

ALTER TABLE achievements
ALTER COLUMN is_active SET NOT NULL;
