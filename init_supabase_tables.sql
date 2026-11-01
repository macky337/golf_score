-- Golf Score App: 新規Supabaseプロジェクト用の初期スキーマ
-- 既存環境の修復・移行には使用せず、sql/ 配下の個別マイグレーションを実行してください。

CREATE TABLE IF NOT EXISTS public.courses (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.member (
    member_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.rounds (
    round_id BIGSERIAL PRIMARY KEY,
    date DATE,
    date_played DATE NOT NULL,
    course_name VARCHAR(255) NOT NULL,
    course_id BIGINT REFERENCES public.courses(id),
    num_players INTEGER NOT NULL CHECK (num_players BETWEEN 2 AND 4),
    has_extra BOOLEAN NOT NULL DEFAULT false,
    finalized BOOLEAN NOT NULL DEFAULT false,
    rule_settings JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.score (
    score_id BIGSERIAL PRIMARY KEY,
    round_id BIGINT NOT NULL REFERENCES public.rounds(round_id) ON DELETE CASCADE,
    member_id BIGINT NOT NULL REFERENCES public.member(member_id),
    front_score INTEGER NOT NULL DEFAULT 0,
    back_score INTEGER NOT NULL DEFAULT 0,
    extra_score INTEGER NOT NULL DEFAULT 0,
    front_putt INTEGER NOT NULL DEFAULT 0,
    back_putt INTEGER NOT NULL DEFAULT 0,
    extra_putt INTEGER NOT NULL DEFAULT 0,
    front_game_pt INTEGER NOT NULL DEFAULT 0,
    back_game_pt INTEGER NOT NULL DEFAULT 0,
    extra_game_pt INTEGER NOT NULL DEFAULT 0,
    total_score INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(round_id, member_id)
);

CREATE TABLE IF NOT EXISTS public.handicap_match (
    id BIGSERIAL PRIMARY KEY,
    round_id BIGINT NOT NULL REFERENCES public.rounds(round_id) ON DELETE CASCADE,
    player_1_id BIGINT NOT NULL REFERENCES public.member(member_id),
    player_2_id BIGINT NOT NULL REFERENCES public.member(member_id),
    player_1_to_2 INTEGER NOT NULL DEFAULT 0,
    player_2_to_1 INTEGER NOT NULL DEFAULT 0,
    total_only BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (player_1_id <> player_2_id),
    UNIQUE(round_id, player_1_id, player_2_id)
);

CREATE TABLE IF NOT EXISTS public.round_results (
    id BIGSERIAL PRIMARY KEY,
    round_id BIGINT NOT NULL REFERENCES public.rounds(round_id) ON DELETE CASCADE,
    member_id BIGINT NOT NULL REFERENCES public.member(member_id),
    match_front INTEGER NOT NULL DEFAULT 0,
    match_back INTEGER NOT NULL DEFAULT 0,
    match_total INTEGER NOT NULL DEFAULT 0,
    match_extra INTEGER NOT NULL DEFAULT 0,
    match_pt INTEGER NOT NULL DEFAULT 0,
    putt_pt INTEGER NOT NULL DEFAULT 0,
    temp_game_pt INTEGER NOT NULL DEFAULT 0,
    total_game_pt INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(round_id, member_id)
);

CREATE TABLE IF NOT EXISTS public.app_settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.backups (
    backup_id TEXT PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    description TEXT
);

CREATE INDEX IF NOT EXISTS rounds_date_played_idx ON public.rounds(date_played DESC);
CREATE INDEX IF NOT EXISTS score_round_id_idx ON public.score(round_id);
CREATE INDEX IF NOT EXISTS handicap_match_round_id_idx ON public.handicap_match(round_id);
CREATE INDEX IF NOT EXISTS round_results_round_id_idx ON public.round_results(round_id);
