ALTER TABLE relay_rooms ADD COLUMN IF NOT EXISTS current_turn_user_id INTEGER REFERENCES users(id);
ALTER TABLE relay_rooms ADD COLUMN IF NOT EXISTS max_players INTEGER DEFAULT 2;
ALTER TABLE relay_rooms ADD COLUMN IF NOT EXISTS turn_time_left INTEGER DEFAULT 30;

CREATE INDEX IF NOT EXISTS idx_relay_rooms_current_turn ON relay_rooms(current_turn_user_id);
