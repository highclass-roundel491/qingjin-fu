BEGIN;

ALTER TABLE learning_records
    DROP CONSTRAINT learning_records_user_id_fkey,
    ADD CONSTRAINT learning_records_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE learning_records
    DROP CONSTRAINT learning_records_poem_id_fkey,
    ADD CONSTRAINT learning_records_poem_id_fkey
        FOREIGN KEY (poem_id) REFERENCES poems(id) ON DELETE CASCADE;

ALTER TABLE poem_favorites
    DROP CONSTRAINT poem_favorites_user_id_fkey,
    ADD CONSTRAINT poem_favorites_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE poem_favorites
    DROP CONSTRAINT poem_favorites_poem_id_fkey,
    ADD CONSTRAINT poem_favorites_poem_id_fkey
        FOREIGN KEY (poem_id) REFERENCES poems(id) ON DELETE CASCADE;

INSERT INTO poets (name, dynasty, alias, birth_year, death_year, birth_death_desc, styles, brief, detailed_bio, representative_works, influence_score, poem_count)
VALUES
(
    '崔护',
    '唐代',
    '字殷功',
    '772',
    '846',
    '约772年—约846年',
    '清丽婉约,情感真挚',
    '唐代诗人，博陵（今河北安平）人，贞元十二年进士。以《题都城南庄》一诗名传千古，"人面桃花"典故即出于此。',
    '崔护，字殷功，博陵安平（今河北安平县）人。唐德宗贞元十二年（796年）登进士第，历任岭南节度使等职。崔护出身名门博陵崔氏，才学出众，但仕途并不顺遂，早年多在京中蹉跎。其诗风清丽，善于捕捉瞬间情感，语言自然而意蕴深远。最为人知的当属《题都城南庄》："去年今日此门中，人面桃花相映红。人面不知何处去，桃花依旧笑春风。"此诗以寻春遇艳、重访不遇的经历，将人事无常的感慨融入明丽的春景之中，创造了"人面桃花"这一经典意象，后世据此衍生出脍炙人口的传奇故事。崔护存诗仅六首，但凭此一篇即足以名垂诗史。',
    '题都城南庄,五月水边柳,郊行,晚鸡,三月五日陪裴大夫泛长沙东湖',
    65,
    6
),
(
    '韩翃',
    '唐代',
    '字君平',
    '719',
    '788',
    '约719年—约788年',
    '清新明快,意境优美',
    '唐代诗人，南阳（今河南南阳）人，"大历十才子"之一。天宝十三载进士，以《寒食》诗最为著名，深得唐德宗赏识。',
    '韩翃，字君平，南阳（今河南南阳）人，唐代中期著名诗人。天宝十三载（754年）登进士第，初任淄青节度使侯希逸幕府从事，后入朝为驾部郎中、知制诰，官至中书舍人。韩翃为"大历十才子"之一，诗风清新明快，善写春景与节令风物。其最负盛名之作为《寒食》："春城无处不飞花，寒食东风御柳斜。日暮汉宫传蜡烛，轻烟散入五侯家。"相传唐德宗欲任知制诰，宰相呈上同名者二人，德宗批曰"与诗人韩翃"，可见其诗名之盛。韩翃诗多写送别、边塞与节令之景，笔触细腻，色彩鲜明，在大历诗坛中独树一帜。',
    '寒食,同题仙游观,宿石邑山中,章台柳·寄柳氏,酬程延秋夜即事见赠',
    70,
    15
),
(
    '张养浩',
    '元代',
    '字希孟，号云庄',
    '1270',
    '1329',
    '1270年—1329年',
    '豪放沉郁,忧国忧民',
    '元代散曲家、政治家，济南历城人。历任监察御史、礼部尚书等职，为官清正。散曲雄浑苍凉，尤以《山坡羊·潼关怀古》最为人知。',
    '张养浩，字希孟，号云庄，济南历城（今山东济南）人，元代著名散曲作家与政治家。自幼聪慧好学，年仅十九即被荐为东平学正，后历任堂邑县尹、监察御史、翰林直学士、礼部尚书等职。为官清廉刚正，敢于直谏，曾因上书批评时政被罢官。后复起为陕西行台中丞，赴任途中见关中大旱，百姓流离失所，日夜操劳赈灾，最终积劳成疾，卒于任上。张养浩的散曲创作成就极高，与张可久并称"二张"，为元曲大家。其曲风豪放沉郁，气势磅礴，善于借古讽今，抒发忧国忧民之情。代表作《山坡羊·潼关怀古》以"兴，百姓苦；亡，百姓苦"的警句，深刻揭示了封建王朝更替中百姓始终受苦的历史悲剧，成为元散曲中最具思想深度的千古名篇。著有散曲集《云庄休居自适小乐府》。',
    '山坡羊·潼关怀古,山坡羊·骊山怀古,山坡羊·北邙山怀古,朝天曲,普天乐·大明湖泛舟',
    75,
    20
)
ON CONFLICT (name, dynasty) DO NOTHING;

COMMIT;
