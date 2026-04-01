ALTER TABLE feihualing_rounds ADD COLUMN IF NOT EXISTS poem_author VARCHAR(100);
ALTER TABLE feihualing_rounds ADD COLUMN IF NOT EXISTS poem_title VARCHAR(200);
ALTER TABLE feihualing_rounds ADD COLUMN IF NOT EXISTS poem_dynasty VARCHAR(50);
