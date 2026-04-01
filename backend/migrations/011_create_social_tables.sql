CREATE TABLE IF NOT EXISTS user_follows (
    id SERIAL PRIMARY KEY,
    follower_id INTEGER NOT NULL REFERENCES users(id),
    following_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_user_follow UNIQUE (follower_id, following_id)
);

CREATE INDEX IF NOT EXISTS idx_user_follows_follower ON user_follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_user_follows_following ON user_follows(following_id);

CREATE TABLE IF NOT EXISTS activity_feeds (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    reference_id INTEGER,
    reference_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_feeds_user_id ON activity_feeds(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_feeds_type ON activity_feeds(type);
CREATE INDEX IF NOT EXISTS idx_activity_feeds_created_at ON activity_feeds(created_at DESC);

CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    rarity VARCHAR(20) NOT NULL DEFAULT 'common',
    condition_type VARCHAR(50) NOT NULL,
    condition_value INTEGER NOT NULL,
    exp_reward INTEGER DEFAULT 0,
    points_reward INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_achievements_code ON achievements(code);
CREATE INDEX IF NOT EXISTS idx_achievements_category ON achievements(category);

CREATE TABLE IF NOT EXISTS user_achievements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    achievement_id INTEGER NOT NULL REFERENCES achievements(id),
    unlocked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_user_achievement UNIQUE (user_id, achievement_id)
);

CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_achievement_id ON user_achievements(achievement_id);

INSERT INTO achievements (code, name, description, icon, category, rarity, condition_type, condition_value, exp_reward, points_reward, sort_order) VALUES
('poem_reader_10', '初窥门径', '阅读10首诗词', 'poem_reader_10', 'learning', 'common', 'poems_read', 10, 50, 10, 1),
('poem_reader_50', '博览群书', '阅读50首诗词', 'poem_reader_50', 'learning', 'rare', 'poems_read', 50, 100, 20, 2),
('poem_reader_200', '学富五车', '阅读200首诗词', 'poem_reader_200', 'learning', 'epic', 'poems_read', 200, 200, 50, 3),
('poem_reader_500', '汗牛充栋', '阅读500首诗词', 'poem_reader_500', 'learning', 'legendary', 'poems_read', 500, 500, 100, 4),
('favorite_10', '雅好初成', '收藏10首诗词', 'favorite_10', 'learning', 'common', 'poems_favorited', 10, 30, 5, 5),
('favorite_50', '珍藏满室', '收藏50首诗词', 'favorite_50', 'learning', 'rare', 'poems_favorited', 50, 80, 15, 6),
('first_work', '初露锋芒', '发布第一首作品', 'first_work', 'creation', 'common', 'works_published', 1, 50, 10, 1),
('works_10', '笔耕不辍', '发布10首作品', 'works_10', 'creation', 'rare', 'works_published', 10, 150, 30, 2),
('works_50', '著作等身', '发布50首作品', 'works_50', 'creation', 'epic', 'works_published', 50, 300, 80, 3),
('likes_50', '声名鹊起', '累计获得50个点赞', 'likes_50', 'creation', 'rare', 'works_liked_received', 50, 100, 20, 4),
('likes_200', '万众瞩目', '累计获得200个点赞', 'likes_200', 'creation', 'epic', 'works_liked_received', 200, 250, 60, 5),
('first_follow', '结交诗友', '关注第一位用户', 'first_follow', 'social', 'common', 'following_count', 1, 20, 5, 1),
('followers_10', '小有名气', '拥有10位粉丝', 'followers_10', 'social', 'rare', 'followers_count', 10, 100, 20, 2),
('followers_50', '桃李满天', '拥有50位粉丝', 'followers_50', 'social', 'epic', 'followers_count', 50, 250, 60, 3),
('challenge_7', '七日不辍', '完成7次每日挑战', 'challenge_7', 'challenge', 'common', 'challenges_completed', 7, 70, 15, 1),
('challenge_30', '持之以恒', '完成30次每日挑战', 'challenge_30', 'challenge', 'rare', 'challenges_completed', 30, 200, 40, 2),
('challenge_100', '百战不殆', '完成100次每日挑战', 'challenge_100', 'challenge', 'epic', 'challenges_completed', 100, 500, 100, 3),
('relay_first', '初试接龙', '完成第一场诗词接龙', 'relay_first', 'relay', 'common', 'relay_games', 1, 30, 5, 1),
('relay_10', '接龙高手', '完成10场诗词接龙', 'relay_10', 'relay', 'rare', 'relay_games', 10, 100, 25, 2),
('relay_combo_5', '五连珠', '在接龙中达成5连击', 'relay_combo_5', 'relay', 'rare', 'relay_max_combo', 5, 80, 20, 3),
('relay_combo_10', '十连珠', '在接龙中达成10连击', 'relay_combo_10', 'relay', 'epic', 'relay_max_combo', 10, 200, 50, 4),
('relay_combo_20', '二十连珠', '在接龙中达成20连击', 'relay_combo_20', 'relay', 'legendary', 'relay_max_combo', 20, 500, 100, 5)
ON CONFLICT (code) DO NOTHING;
