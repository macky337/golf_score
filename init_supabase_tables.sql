-- 1. roundsテーブルの作成
CREATE TABLE IF NOT EXISTS rounds (
    round_id BIGSERIAL PRIMARY KEY,
    date_played DATE NOT NULL,
    course_name VARCHAR(255) NOT NULL,
    finalized BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. membersテーブルの作成
CREATE TABLE IF NOT EXISTS members (
    member_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. handicap_matchテーブルの作成
CREATE TABLE IF NOT EXISTS handicap_match (
    handicap_id BIGSERIAL PRIMARY KEY,
    round_id BIGINT NOT NULL,
    player_1_id BIGINT NOT NULL,
    player_2_id BIGINT NOT NULL,
    player_1_to_2 INTEGER DEFAULT 0,
    player_2_to_1 INTEGER DEFAULT 0,
    total_only BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (round_id) REFERENCES rounds(round_id),
    FOREIGN KEY (player_1_id) REFERENCES members(member_id),
    FOREIGN KEY (player_2_id) REFERENCES members(member_id),
    UNIQUE(round_id, player_1_id, player_2_id)
);

-- 4. scoresテーブルの作成
CREATE TABLE IF NOT EXISTS scores (
    id BIGSERIAL PRIMARY KEY,
    round_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    front_score INTEGER DEFAULT 0,
    back_score INTEGER DEFAULT 0,
    extra_score INTEGER DEFAULT 0,
    front_putt INTEGER DEFAULT 0,
    back_putt INTEGER DEFAULT 0,
    extra_putt INTEGER DEFAULT 0,
    front_game_pt INTEGER DEFAULT 0,
    back_game_pt INTEGER DEFAULT 0,
    extra_game_pt INTEGER DEFAULT 0,
    total_pt INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (round_id) REFERENCES rounds(round_id),
    FOREIGN KEY (member_id) REFERENCES members(member_id),
    UNIQUE(round_id, member_id)
);

-- 5. round_resultsテーブルの作成
CREATE TABLE IF NOT EXISTS round_results (
    id BIGSERIAL PRIMARY KEY,
    round_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    match_front INTEGER DEFAULT 0,
    match_back INTEGER DEFAULT 0,
    match_total INTEGER DEFAULT 0,
    match_extra INTEGER DEFAULT 0,
    match_pt INTEGER DEFAULT 0,
    putt_pt INTEGER DEFAULT 0,
    temp_game_pt INTEGER DEFAULT 0,
    total_game_pt INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (round_id) REFERENCES rounds(round_id),
    FOREIGN KEY (member_id) REFERENCES members(member_id),
    UNIQUE(round_id, member_id)
);