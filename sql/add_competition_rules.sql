-- 競技ルール設定と、ラウンド作成時のルールスナップショットを追加する。
-- Supabase SQL Editorで一度だけ実行する。

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE rounds
    ADD COLUMN IF NOT EXISTS rule_settings JSONB;

INSERT INTO app_settings (key, value)
VALUES (
    'competition_rules',
    '{
      "version": 1,
      "match_win_points": 10,
      "putt_3_solo_winner": 20,
      "putt_3_solo_loser": -10,
      "putt_3_two_winners": 5,
      "putt_3_two_losers": -10,
      "putt_4_solo_winner": 30,
      "putt_4_solo_loser": -10,
      "putt_4_two_winners": 10,
      "putt_4_two_losers": -10,
      "putt_4_three_winners": 5,
      "putt_4_three_losers": -15,
      "game_points_2": [10, -10],
      "game_points_3": [30, 0, -30],
      "game_points_4": [30, 10, -10, -30]
    }'::jsonb
)
ON CONFLICT (key) DO NOTHING;
