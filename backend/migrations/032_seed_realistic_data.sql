BEGIN;

DELETE FROM work_comments WHERE work_id IN (SELECT id FROM works WHERE user_id BETWEEN 21 AND 28);
DELETE FROM work_likes WHERE work_id IN (SELECT id FROM works WHERE user_id BETWEEN 21 AND 28);
DELETE FROM works WHERE user_id BETWEEN 21 AND 28;
DELETE FROM user_follows WHERE follower_id BETWEEN 21 AND 28 OR following_id BETWEEN 21 AND 28;
DELETE FROM activity_feeds WHERE user_id BETWEEN 21 AND 28;
DELETE FROM user_stats WHERE user_id BETWEEN 21 AND 28;
DELETE FROM learning_records WHERE user_id BETWEEN 21 AND 28;
DELETE FROM users WHERE id BETWEEN 21 AND 28;

INSERT INTO users (id, username, email, password_hash, nickname, bio, level, exp, points, is_active, is_admin)
VALUES
(21, 'shenyanqiu', 'shenyanqiu@qingjin.cc', '$2b$12$LJ3m4ys3Lg2VBe4WMBSGOeJf7FfM1HqROpKlKEJOGCGBKwVJE3gKa', '沈砚秋', '半卷闲书一盏茶，偶拾旧句寄天涯', 6, 1680, 420, true, false),
(22, 'guqinghe', 'guqinghe@qingjin.cc', '$2b$12$LJ3m4ys3Lg2VBe4WMBSGOeJf7FfM1HqROpKlKEJOGCGBKwVJE3gKa', '顾清和', '竹影扫阶尘不动，月光入户梦初成', 5, 1120, 280, true, false),
(23, 'liuzhiwei', 'liuzhiwei@qingjin.cc', '$2b$12$LJ3m4ys3Lg2VBe4WMBSGOeJf7FfM1HqROpKlKEJOGCGBKwVJE3gKa', '柳知微', '云在青天水在瓶，一痕墨迹写空灵', 7, 2360, 590, true, false),
(24, 'luxingchuan', 'luxingchuan@qingjin.cc', '$2b$12$LJ3m4ys3Lg2VBe4WMBSGOeJf7FfM1HqROpKlKEJOGCGBKwVJE3gKa', '陆行川', '烟波江上使人愁，一阕新词寄小楼', 4, 640, 160, true, false),
(25, 'wenrulan', 'wenrulan@qingjin.cc', '$2b$12$LJ3m4ys3Lg2VBe4WMBSGOeJf7FfM1HqROpKlKEJOGCGBKwVJE3gKa', '温如岚', '松间明月长如此，身外浮云何足论', 8, 3180, 795, true, false),
(26, 'bailinzhou', 'bailinzhou@qingjin.cc', '$2b$12$LJ3m4ys3Lg2VBe4WMBSGOeJf7FfM1HqROpKlKEJOGCGBKwVJE3gKa', '白临舟', '疏影横斜水清浅，暗香浮动月黄昏', 3, 360, 90, true, false),
(27, 'zhouxinglan', 'zhouxinglan@qingjin.cc', '$2b$12$LJ3m4ys3Lg2VBe4WMBSGOeJf7FfM1HqROpKlKEJOGCGBKwVJE3gKa', '周星阑', '星河欲转千帆舞，夜深篝火照诗魂', 5, 1200, 300, true, false),
(28, 'xujianshan', 'xujianshan@qingjin.cc', '$2b$12$LJ3m4ys3Lg2VBe4WMBSGOeJf7FfM1HqROpKlKEJOGCGBKwVJE3gKa', '许见山', '兰亭已矣梓泽丘墟，逸兴遄飞不负韶华', 4, 800, 200, true, false)
ON CONFLICT (id) DO UPDATE SET
  username = EXCLUDED.username,
  email = EXCLUDED.email,
  nickname = EXCLUDED.nickname,
  bio = EXCLUDED.bio,
  level = EXCLUDED.level,
  exp = EXCLUDED.exp,
  points = EXCLUDED.points;

SELECT setval('users_id_seq', GREATEST((SELECT MAX(id) FROM users), 28));

INSERT INTO user_stats (user_id, total_learned, total_favorites, study_time, streak_days)
VALUES
(21, 86, 34, 4200, 12),
(22, 72, 28, 3600, 8),
(23, 104, 45, 5800, 18),
(24, 53, 19, 2400, 5),
(25, 128, 52, 7200, 24),
(26, 41, 15, 1800, 3),
(27, 67, 26, 3200, 9),
(28, 58, 22, 2800, 6)
ON CONFLICT (user_id) DO UPDATE SET
  total_learned = EXCLUDED.total_learned,
  total_favorites = EXCLUDED.total_favorites,
  study_time = EXCLUDED.study_time,
  streak_days = EXCLUDED.streak_days;

INSERT INTO works (id, user_id, title, content, genre, status, ai_grammar_score, ai_artistic_score, ai_total_score, ai_feedback, like_count, view_count, comment_count, exp_awarded, published_at)
VALUES
(101, 21, '花香蝶影_春信', E'春山入墨迟\n溪月照松枝\n纸上新词暖\n清风与我知', '五言绝句', 'published', 94, 92, 93, '起句以"入墨"拟春山之缓，颇具画意；结句"清风与我知"收得空灵，全篇气韵流畅。', 126, 538, 8, 30, NOW() - INTERVAL '6 hours'),
(102, 22, '竹韵松风_月魂', E'雨洗青苔净\n云分竹影深\n小窗临古帖\n一字见初心', '五言绝句', 'published', 90, 89, 90, '首联写景清新，"雨洗""云分"对仗工稳；尾句"一字见初心"点题精妙，意在言外。', 98, 412, 5, 25, NOW() - INTERVAL '2 days 3 hours'),
(103, 23, '云水禅心_墨痕', E'水纹轻皱月华新\n小桨归时岸柳匀\n一段清辞留白处\n更添江上晚来春', '七言绝句', 'published', 88, 95, 91, '全篇以水月为经，词句为纬，"留白处"三字尤见匠心，末句收束有余韵。', 118, 620, 12, 28, NOW() - INTERVAL '5 days 8 hours'),
(104, 24, '灯火阑珊_夜读', E'灯静书声慢\n更深砚气温\n一行唐句在\n照见读诗人', '五言绝句', 'published', 86, 87, 86, '以灯、书、砚三物勾勒夜读之境，末句"照见读诗人"自然而有禅意。', 76, 301, 3, 22, NOW() - INTERVAL '8 days 10 hours'),
(105, 25, '芦花渡口_新声', E'蘸水芦花白\n鸣榔夜色分\n归舟摇一盏\n照破渡头云', '五言绝句', 'published', 91, 93, 92, '"蘸水"二字极妙，芦花似蘸水而白；"照破渡头云"气象开阔，收束有力。', 132, 690, 15, 30, NOW() - INTERVAL '12 days 4 hours'),
(106, 26, '秋声入句_霜笔', E'一叶先知晚\n疏钟入短窗\n新凉辞未稳\n已觉笔端霜', '五言绝句', 'published', 83, 84, 84, '以秋声入诗，层层递进；"辞未稳"与"笔端霜"呼应，写出创作中的秋意体验。', 64, 256, 2, 20, NOW() - INTERVAL '16 days 7 hours'),
(107, 27, '潮生海色_乡书', E'潮痕初上石\n海色半侵窗\n欲写乡关远\n先闻雁一双', '五言绝句', 'published', 85, 88, 86, '前二句写海景，后二句转乡思，"先闻雁一双"以声入情，转折自然。', 88, 470, 6, 24, NOW() - INTERVAL '23 days 5 hours'),
(108, 28, '竹里清风_茶烟', E'对坐无人处\n风声替我言\n茶烟分远近\n皆入一窗山', '五言绝句', 'published', 81, 82, 81, '写竹林独坐之趣，"风声替我言"拟人生动；末句以山收束，意境悠远。', 58, 220, 1, 18, NOW() - INTERVAL '34 days 2 hours'),
(109, 21, '墨梅冰骨_横斜', E'不向东风借颜色\n自将冰骨写横斜\n砚池水浅难磨意\n且把清香入墨花', '七言绝句', 'published', 92, 90, 91, '咏梅而不滞于梅，以墨写梅、以梅喻志，"砚池水浅难磨意"尤见功力。', 104, 486, 9, 28, NOW() - INTERVAL '3 days 12 hours'),
(110, 23, '松间石泉_禅茶', E'石上清泉石下苔\n松间一径绕云开\n山僧不语分茶坐\n只有泉声送客来', '七言绝句', 'published', 89, 91, 90, '以泉声贯穿全篇，"山僧不语"与"泉声送客"动静相生，禅意盎然。', 96, 402, 7, 26, NOW() - INTERVAL '10 days 6 hours'),
(111, 25, '江天暮色_渔笛', E'江天一色暮云平\n远岫含烟似有情\n欲寄新诗无雁到\n且听渔笛过芦汀', '七言绝句', 'published', 90, 92, 91, '首句大开，次句收拢，三四句以"无雁"转"渔笛"，虚实相间，余韵悠长。', 112, 558, 10, 28, NOW() - INTERVAL '7 days 9 hours'),
(112, 27, '灯花剪影_秋史', E'灯花剪尽夜初长\n翻到兴亡第几章\n窗外一声寒雁过\n恰如书里说边疆', '七言绝句', 'published', 87, 89, 88, '以读史为题，"灯花剪尽"起笔沉稳；末联以窗外雁声应书中边事，虚实交映。', 82, 368, 4, 24, NOW() - INTERVAL '20 days 3 hours')
ON CONFLICT (id) DO UPDATE SET
  user_id = EXCLUDED.user_id,
  title = EXCLUDED.title,
  content = EXCLUDED.content,
  genre = EXCLUDED.genre,
  status = EXCLUDED.status,
  ai_grammar_score = EXCLUDED.ai_grammar_score,
  ai_artistic_score = EXCLUDED.ai_artistic_score,
  ai_total_score = EXCLUDED.ai_total_score,
  ai_feedback = EXCLUDED.ai_feedback,
  like_count = EXCLUDED.like_count,
  view_count = EXCLUDED.view_count,
  comment_count = EXCLUDED.comment_count,
  exp_awarded = EXCLUDED.exp_awarded,
  published_at = EXCLUDED.published_at;

SELECT setval('works_id_seq', GREATEST((SELECT MAX(id) FROM works), 112));

INSERT INTO user_follows (follower_id, following_id) VALUES
(21, 23), (21, 25), (22, 21), (22, 23),
(23, 25), (23, 27), (24, 21), (24, 22),
(25, 23), (25, 21), (26, 25), (26, 22),
(27, 21), (27, 23), (28, 25), (28, 27)
ON CONFLICT DO NOTHING;

INSERT INTO work_likes (user_id, work_id) VALUES
(22, 101), (23, 101), (25, 101), (27, 101),
(21, 102), (23, 102), (25, 102),
(21, 103), (22, 103), (24, 103), (25, 103), (28, 103),
(21, 105), (22, 105), (23, 105), (24, 105), (26, 105),
(21, 109), (23, 109), (25, 109), (27, 109),
(22, 110), (24, 110), (25, 110),
(21, 111), (22, 111), (23, 111), (26, 111), (28, 111)
ON CONFLICT DO NOTHING;

-- 修复已有填字题目的 blank_count（__ 代表两个字）
UPDATE daily_challenges SET blank_count = 2
WHERE challenge_type = 'fill_blank' AND blank_count = 1
  AND sentence_template LIKE '%\\_\\_%';

-- 续写接力测试数据
INSERT INTO daily_challenges (id, challenge_type, creator_id, is_daily, sentence_template, blank_count, difficulty, status, response_count, created_at)
VALUES
(201, 'continue_line', 21, false, '春江潮水连海平，海上明月共潮生', 1, 'medium', 'active', 3, NOW() - INTERVAL '2 days'),
(202, 'continue_line', 23, false, '大漠孤烟直，长河落日圆', 1, 'easy', 'active', 5, NOW() - INTERVAL '3 days'),
(203, 'continue_line', 25, false, '落霞与孤鹜齐飞，秋水共长天一色', 1, 'hard', 'active', 2, NOW() - INTERVAL '1 day'),
(204, 'continue_line', 22, false, '人生得意须尽欢，莫使金樽空对月', 1, 'medium', 'active', 4, NOW() - INTERVAL '5 days'),
(205, 'continue_line', 27, false, '明月松间照，清泉石上流', 1, 'easy', 'active', 6, NOW() - INTERVAL '4 days'),
(206, 'continue_line', 24, false, '千山鸟飞绝，万径人踪灭', 1, 'medium', 'active', 3, NOW() - INTERVAL '6 days'),
(207, 'continue_line', 26, false, '两个黄鹂鸣翠柳，一行白鹭上青天', 1, 'easy', 'active', 7, NOW() - INTERVAL '7 days'),
(208, 'continue_line', 28, false, '独在异乡为异客，每逢佳节倍思亲', 1, 'medium', 'active', 2, NOW() - INTERVAL '8 days')
ON CONFLICT (id) DO UPDATE SET
  challenge_type = EXCLUDED.challenge_type,
  creator_id = EXCLUDED.creator_id,
  sentence_template = EXCLUDED.sentence_template,
  difficulty = EXCLUDED.difficulty,
  status = EXCLUDED.status,
  response_count = EXCLUDED.response_count;

-- 续写接力的提交记录
INSERT INTO challenge_submissions (id, user_id, challenge_id, answer, content, ai_score, beauty_score, creativity_score, mood_score, exp_gained, points_gained, submitted_at)
VALUES
(301, 22, 201, '续写', '滟滟随波千万里，何处春江无月明', 78, 24, 26, 28, 15, 8, NOW() - INTERVAL '1 day 6 hours'),
(302, 25, 201, '续写', '江流宛转绕芳甸，月照花林皆似霰', 82, 26, 28, 28, 18, 9, NOW() - INTERVAL '1 day 3 hours'),
(303, 27, 201, '续写', '空里流霜不觉飞，汀上白沙看不见', 75, 22, 25, 28, 14, 7, NOW() - INTERVAL '1 day 1 hour'),
(304, 21, 202, '续写', '萧关逢候骑，都护在燕然', 85, 28, 28, 29, 20, 10, NOW() - INTERVAL '2 days 8 hours'),
(305, 24, 202, '续写', '征蓬出汉塞，归雁入胡天', 80, 26, 26, 28, 17, 9, NOW() - INTERVAL '2 days 5 hours'),
(306, 26, 202, '续写', '单车欲问边，属国过居延', 77, 24, 25, 28, 15, 8, NOW() - INTERVAL '2 days 3 hours'),
(307, 28, 202, '续写', '使至塞上行，边城暮雨生', 72, 22, 24, 26, 13, 7, NOW() - INTERVAL '2 days 1 hour'),
(308, 23, 202, '续写', '回看射雕处，千里暮云平', 83, 27, 28, 28, 19, 10, NOW() - INTERVAL '2 days'),
(309, 21, 203, '续写', '渔舟唱晚，响穷彭蠡之滨', 88, 29, 29, 30, 22, 11, NOW() - INTERVAL '12 hours'),
(310, 22, 203, '续写', '雁阵惊寒，声断衡阳之浦', 86, 28, 29, 29, 21, 11, NOW() - INTERVAL '6 hours'),
(311, 23, 204, '续写', '天生我材必有用，千金散尽还复来', 90, 30, 30, 30, 24, 12, NOW() - INTERVAL '4 days 6 hours'),
(312, 25, 204, '续写', '烹羊宰牛且为乐，会须一饮三百杯', 87, 28, 29, 30, 21, 11, NOW() - INTERVAL '4 days 3 hours'),
(313, 26, 204, '续写', '岑夫子，丹丘生，将进酒，杯莫停', 84, 27, 28, 29, 20, 10, NOW() - INTERVAL '4 days 1 hour'),
(314, 28, 204, '续写', '与君歌一曲，请君为我倾耳听', 81, 26, 27, 28, 18, 9, NOW() - INTERVAL '4 days'),
(315, 21, 205, '续写', '竹喧归浣女，莲动下渔舟', 86, 28, 29, 29, 21, 11, NOW() - INTERVAL '3 days 8 hours'),
(316, 23, 205, '续写', '随意春芳歇，王孙自可留', 84, 27, 28, 29, 20, 10, NOW() - INTERVAL '3 days 5 hours'),
(317, 24, 205, '续写', '空山新雨后，天气晚来秋', 82, 26, 28, 28, 18, 9, NOW() - INTERVAL '3 days 3 hours'),
(318, 26, 205, '续写', '薄暮空潭曲，安禅制毒龙', 79, 25, 26, 28, 16, 8, NOW() - INTERVAL '3 days 1 hour'),
(319, 27, 205, '续写', '深林人不知，明月来相照', 83, 27, 28, 28, 19, 10, NOW() - INTERVAL '3 days'),
(320, 28, 205, '续写', '返景入深林，复照青苔上', 80, 26, 26, 28, 17, 9, NOW() - INTERVAL '2 days 20 hours')
ON CONFLICT (id) DO NOTHING;

-- 填字广场测试数据
INSERT INTO daily_challenges (id, challenge_type, creator_id, is_daily, sentence_template, sentence_template_2, blank_count, hint, difficulty, status, response_count, created_at)
VALUES
(211, 'fill_blank', 21, false, '山色湖光__鹤梦', '月华水影__梅魂', 2, '伴,送', 'medium', 'active', 4, NOW() - INTERVAL '1 day'),
(212, 'fill_blank', 23, false, '春风__柳千条绿', '秋雨__花万点红', 2, '拂,催', 'medium', 'active', 3, NOW() - INTERVAL '2 days'),
(213, 'fill_blank', 25, false, '云__远山青似黛', '风__近水绿如蓝', 2, '开,过', 'easy', 'active', 5, NOW() - INTERVAL '3 days'),
(214, 'fill_blank', 22, false, '竹影__窗月半弯', '松声__枕雨三更', 2, '入,伴', 'medium', 'active', 2, NOW() - INTERVAL '4 days'),
(215, 'fill_blank', 27, false, '一帘__雨春将老', '满地__花人未归', 2, '细,落', 'easy', 'active', 6, NOW() - INTERVAL '5 days'),
(216, 'fill_blank', 24, false, '笔__千山皆入画', '墨__万水尽成诗', 2, '走,行', 'hard', 'active', 1, NOW() - INTERVAL '6 days')
ON CONFLICT (id) DO UPDATE SET
  challenge_type = EXCLUDED.challenge_type,
  creator_id = EXCLUDED.creator_id,
  sentence_template = EXCLUDED.sentence_template,
  sentence_template_2 = EXCLUDED.sentence_template_2,
  blank_count = EXCLUDED.blank_count,
  hint = EXCLUDED.hint,
  difficulty = EXCLUDED.difficulty,
  status = EXCLUDED.status,
  response_count = EXCLUDED.response_count;

SELECT setval('daily_challenges_id_seq', GREATEST((SELECT MAX(id) FROM daily_challenges), 216));
SELECT setval('challenge_submissions_id_seq', GREATEST((SELECT MAX(id) FROM challenge_submissions), 320));

COMMIT;
