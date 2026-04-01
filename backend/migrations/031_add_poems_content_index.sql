-- 添加 pg_trgm GIN 索引以加速飞花令诗词搜索
-- 此索引将显著提升 LIKE 和 similarity 查询性能（预期10倍提升）

-- 确保 pg_trgm 扩展已启用
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 为 poems 表的 content 字段创建 GIN 索引
-- 使用 CONCURRENTLY 避免锁表，允许在生产环境安全执行
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_poems_content_trgm
ON poems USING gin (content gin_trgm_ops);

-- 验证索引创建成功
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'poems' AND indexname = 'idx_poems_content_trgm';
