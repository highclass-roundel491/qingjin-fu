BEGIN;

ALTER TABLE activity_feeds
    DROP CONSTRAINT activity_feeds_user_id_fkey,
    ADD CONSTRAINT activity_feeds_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE challenge_submissions
    DROP CONSTRAINT challenge_submissions_user_id_fkey,
    ADD CONSTRAINT challenge_submissions_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE challenge_submissions
    DROP CONSTRAINT challenge_submissions_challenge_id_fkey,
    ADD CONSTRAINT challenge_submissions_challenge_id_fkey
        FOREIGN KEY (challenge_id) REFERENCES daily_challenges(id) ON DELETE CASCADE;

ALTER TABLE daily_challenges
    DROP CONSTRAINT daily_challenges_creator_id_fkey,
    ADD CONSTRAINT daily_challenges_creator_id_fkey
        FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE feihualing_rounds
    DROP CONSTRAINT feihualing_rounds_poem_id_fkey,
    ADD CONSTRAINT feihualing_rounds_poem_id_fkey
        FOREIGN KEY (poem_id) REFERENCES poems(id) ON DELETE SET NULL;

ALTER TABLE relay_players
    DROP CONSTRAINT relay_players_room_id_fkey,
    ADD CONSTRAINT relay_players_room_id_fkey
        FOREIGN KEY (room_id) REFERENCES relay_rooms(id) ON DELETE CASCADE;

ALTER TABLE relay_players
    DROP CONSTRAINT relay_players_user_id_fkey,
    ADD CONSTRAINT relay_players_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE relay_rooms
    DROP CONSTRAINT relay_rooms_host_id_fkey,
    ADD CONSTRAINT relay_rooms_host_id_fkey
        FOREIGN KEY (host_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE relay_rooms
    DROP CONSTRAINT relay_rooms_current_turn_user_id_fkey,
    ADD CONSTRAINT relay_rooms_current_turn_user_id_fkey
        FOREIGN KEY (current_turn_user_id) REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE relay_rounds
    DROP CONSTRAINT relay_rounds_room_id_fkey,
    ADD CONSTRAINT relay_rounds_room_id_fkey
        FOREIGN KEY (room_id) REFERENCES relay_rooms(id) ON DELETE CASCADE;

ALTER TABLE timed_challenge_answers
    DROP CONSTRAINT timed_challenge_answers_user_id_fkey,
    ADD CONSTRAINT timed_challenge_answers_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE timed_challenge_answers
    DROP CONSTRAINT timed_challenge_answers_poem_id_fkey,
    ADD CONSTRAINT timed_challenge_answers_poem_id_fkey
        FOREIGN KEY (poem_id) REFERENCES poems(id) ON DELETE SET NULL;

ALTER TABLE timed_challenge_sessions
    DROP CONSTRAINT timed_challenge_sessions_user_id_fkey,
    ADD CONSTRAINT timed_challenge_sessions_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE user_achievements
    DROP CONSTRAINT user_achievements_user_id_fkey,
    ADD CONSTRAINT user_achievements_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE user_achievements
    DROP CONSTRAINT user_achievements_achievement_id_fkey,
    ADD CONSTRAINT user_achievements_achievement_id_fkey
        FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE;

ALTER TABLE user_follows
    DROP CONSTRAINT user_follows_follower_id_fkey,
    ADD CONSTRAINT user_follows_follower_id_fkey
        FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE user_follows
    DROP CONSTRAINT user_follows_following_id_fkey,
    ADD CONSTRAINT user_follows_following_id_fkey
        FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE user_stats
    DROP CONSTRAINT user_stats_user_id_fkey,
    ADD CONSTRAINT user_stats_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE work_likes
    DROP CONSTRAINT work_likes_user_id_fkey,
    ADD CONSTRAINT work_likes_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE work_likes
    DROP CONSTRAINT work_likes_work_id_fkey,
    ADD CONSTRAINT work_likes_work_id_fkey
        FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE;

ALTER TABLE works
    DROP CONSTRAINT works_user_id_fkey,
    ADD CONSTRAINT works_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

COMMIT;
