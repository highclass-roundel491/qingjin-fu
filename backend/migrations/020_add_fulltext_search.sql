CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_poems_content_trgm ON poems USING GIN (content gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_poems_title_trgm ON poems USING GIN (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_poems_author_trgm ON poems USING GIN (author gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_poems_tags_trgm ON poems USING GIN (tags gin_trgm_ops);
