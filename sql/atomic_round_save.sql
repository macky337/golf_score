-- 新しいアプリをデプロイする前に、Supabase SQL Editorで実行してください。
-- 入力値の比較、計算結果・確定状態の更新は1トランザクション。
-- SECURITY INVOKERのため、既存のテーブル権限とRLSがそのまま適用されます。
DROP FUNCTION IF EXISTS public.save_golf_round_atomic(bigint, jsonb, jsonb, jsonb, jsonb, boolean);
DROP FUNCTION IF EXISTS public.save_golf_round_atomic(bigint, jsonb, jsonb, jsonb, jsonb, jsonb, boolean);
DROP FUNCTION IF EXISTS public.save_golf_round_atomic(bigint, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, boolean);

CREATE OR REPLACE FUNCTION public.save_golf_round_atomic(
    p_round_id bigint,
    p_expected_scores jsonb,
    p_results jsonb,
    p_expected_round jsonb DEFAULT NULL,
    p_expected_handicaps jsonb DEFAULT NULL,
    p_replacement_handicaps jsonb DEFAULT NULL,
    p_replacement_scores jsonb DEFAULT NULL,
    p_finalize boolean DEFAULT false
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
DECLARE
    round_row public.rounds%ROWTYPE;
    current_scores jsonb;
    current_handicaps jsonb;
    sorted_expected jsonb;
    player_count integer;
    row_data jsonb;
    field_name text;
    field_value numeric;
    replacement_pair_count integer;
BEGIN
    SELECT * INTO round_row FROM public.rounds
        WHERE round_id = p_round_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Round not found'; END IF;
    IF p_finalize AND COALESCE(round_row.finalized, false) AND p_replacement_scores IS NULL THEN
        RAISE EXCEPTION 'Finalized rounds cannot be finalized again';
    END IF;
    IF p_expected_round IS NOT NULL AND to_jsonb(round_row) IS DISTINCT FROM p_expected_round THEN
        RAISE EXCEPTION 'Round settings changed; reload before saving';
    END IF;

    PERFORM 1 FROM public.score WHERE round_id = p_round_id ORDER BY member_id FOR UPDATE;
    PERFORM 1 FROM public.handicap_match WHERE round_id = p_round_id ORDER BY player_1_id, player_2_id FOR UPDATE;
    SELECT COALESCE(jsonb_agg(jsonb_build_object(
            'member_id', s.member_id,
            'front_score', COALESCE(s.front_score, 0),
            'front_putt', COALESCE(s.front_putt, 0),
            'back_score', COALESCE(s.back_score, 0),
            'back_putt', COALESCE(s.back_putt, 0),
            'extra_score', COALESCE(s.extra_score, 0),
            'extra_putt', COALESCE(s.extra_putt, 0),
            'front_game_pt', COALESCE(s.front_game_pt, 0),
            'back_game_pt', COALESCE(s.back_game_pt, 0),
            'extra_game_pt', COALESCE(s.extra_game_pt, 0)
        ) ORDER BY s.member_id), '[]'::jsonb)
        INTO current_scores FROM public.score s WHERE s.round_id = p_round_id;
    player_count := jsonb_array_length(current_scores);
    IF player_count = 0 THEN RAISE EXCEPTION 'Round has no scores'; END IF;
    IF jsonb_typeof(p_expected_scores) IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION 'Expected scores must be an array';
    END IF;
    SELECT jsonb_agg(value ORDER BY (value->>'member_id')::bigint)
        INTO sorted_expected FROM jsonb_array_elements(p_expected_scores);
    IF current_scores IS DISTINCT FROM sorted_expected THEN
        RAISE EXCEPTION 'Scores changed; reload before saving';
    END IF;
    IF p_replacement_scores IS NOT NULL THEN
        IF jsonb_typeof(p_replacement_scores) IS DISTINCT FROM 'array'
           OR jsonb_array_length(p_replacement_scores) <> player_count
           OR (SELECT count(DISTINCT (value->>'member_id')::bigint)
               FROM jsonb_array_elements(p_replacement_scores)) <> player_count
           OR EXISTS (
               SELECT 1 FROM jsonb_array_elements(p_replacement_scores) r
               WHERE NOT EXISTS (SELECT 1 FROM public.score s WHERE s.round_id = p_round_id
                                 AND s.member_id = (r->>'member_id')::bigint)
                  OR EXISTS (
                      SELECT 1 FROM unnest(ARRAY['front_score', 'front_putt', 'back_score', 'back_putt',
                                                'extra_score', 'extra_putt', 'front_game_pt', 'back_game_pt',
                                                'extra_game_pt']) AS f(name)
                      WHERE jsonb_typeof(r->f.name) IS DISTINCT FROM 'number'
                  )
           ) THEN RAISE EXCEPTION 'Invalid replacement scores'; END IF;
    END IF;
    IF p_expected_handicaps IS NOT NULL THEN
        SELECT COALESCE(jsonb_agg(to_jsonb(h) ORDER BY h.player_1_id, h.player_2_id), '[]'::jsonb)
            INTO current_handicaps FROM public.handicap_match h WHERE h.round_id = p_round_id;
        SELECT COALESCE(jsonb_agg(value ORDER BY (value->>'player_1_id')::bigint, (value->>'player_2_id')::bigint), '[]'::jsonb)
            INTO sorted_expected FROM jsonb_array_elements(p_expected_handicaps);
        IF current_handicaps IS DISTINCT FROM sorted_expected THEN
            RAISE EXCEPTION 'Handicaps changed; reload before saving';
        END IF;
    END IF;

    IF jsonb_typeof(p_results) IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION 'Results must be an array';
    END IF;
    IF jsonb_array_length(p_results) <> player_count
       OR (SELECT count(DISTINCT (value->>'member_id')::bigint) FROM jsonb_array_elements(p_results)) <> player_count
       OR EXISTS (
           SELECT 1 FROM jsonb_array_elements(p_results) r
           WHERE NOT EXISTS (SELECT 1 FROM public.score s WHERE s.round_id = p_round_id AND s.member_id = (r->>'member_id')::bigint)
       ) THEN RAISE EXCEPTION 'Results must contain every participant exactly once'; END IF;
    FOR row_data IN SELECT value FROM jsonb_array_elements(p_results) LOOP
        FOREACH field_name IN ARRAY ARRAY['match_front', 'match_back', 'match_total', 'match_extra', 'match_pt', 'putt_pt', 'temp_game_pt', 'total_game_pt'] LOOP
            IF jsonb_typeof(row_data->field_name) IS DISTINCT FROM 'number' THEN
                RAISE EXCEPTION 'Invalid result field: %', field_name;
            END IF;
            field_value := (row_data->>field_name)::numeric;
            IF field_value <> trunc(field_value) THEN RAISE EXCEPTION 'Result points must be integers'; END IF;
        END LOOP;
    END LOOP;

    IF p_replacement_handicaps IS NOT NULL THEN
        IF jsonb_typeof(p_replacement_handicaps) IS DISTINCT FROM 'array' THEN
            RAISE EXCEPTION 'Replacement handicaps must be an array';
        END IF;
        IF EXISTS (
            SELECT 1 FROM jsonb_array_elements(p_replacement_handicaps) h
            WHERE jsonb_typeof(h->'player_1_id') IS DISTINCT FROM 'number'
               OR jsonb_typeof(h->'player_2_id') IS DISTINCT FROM 'number'
               OR jsonb_typeof(h->'player_1_to_2') IS DISTINCT FROM 'number'
               OR jsonb_typeof(h->'player_2_to_1') IS DISTINCT FROM 'number'
               OR jsonb_typeof(h->'total_only') IS DISTINCT FROM 'boolean'
               OR (h->>'player_1_id')::bigint = (h->>'player_2_id')::bigint
               OR NOT EXISTS (SELECT 1 FROM public.score s WHERE s.round_id = p_round_id
                              AND s.member_id = (h->>'player_1_id')::bigint)
               OR NOT EXISTS (SELECT 1 FROM public.score s WHERE s.round_id = p_round_id
                              AND s.member_id = (h->>'player_2_id')::bigint)
               OR (h->>'player_1_to_2')::numeric <> trunc((h->>'player_1_to_2')::numeric)
               OR (h->>'player_2_to_1')::numeric <> trunc((h->>'player_2_to_1')::numeric)
        ) THEN
            RAISE EXCEPTION 'Invalid replacement handicap';
        END IF;
        SELECT count(*) INTO replacement_pair_count FROM (
            SELECT DISTINCT LEAST((h->>'player_1_id')::bigint, (h->>'player_2_id')::bigint),
                            GREATEST((h->>'player_1_id')::bigint, (h->>'player_2_id')::bigint)
            FROM jsonb_array_elements(p_replacement_handicaps) h
        ) pairs;
        IF replacement_pair_count <> jsonb_array_length(p_replacement_handicaps) THEN
            RAISE EXCEPTION 'Duplicate replacement handicap pair';
        END IF;
    END IF;

    IF p_replacement_scores IS NOT NULL THEN
        UPDATE public.score s SET
            front_score = incoming.front_score, front_putt = incoming.front_putt,
            back_score = incoming.back_score, back_putt = incoming.back_putt,
            extra_score = incoming.extra_score, extra_putt = incoming.extra_putt,
            front_game_pt = incoming.front_game_pt, back_game_pt = incoming.back_game_pt,
            extra_game_pt = incoming.extra_game_pt,
            total_score = incoming.front_score + incoming.back_score
        FROM jsonb_to_recordset(p_replacement_scores) AS incoming(
            member_id bigint, front_score integer, front_putt integer, back_score integer,
            back_putt integer, extra_score integer, extra_putt integer,
            front_game_pt integer, back_game_pt integer, extra_game_pt integer
        ) WHERE s.round_id = p_round_id AND s.member_id = incoming.member_id;
    END IF;

    IF p_finalize THEN
        IF COALESCE((to_jsonb(round_row)->>'num_players')::integer, player_count) <> player_count
           OR EXISTS (SELECT 1 FROM public.score s WHERE s.round_id = p_round_id AND (
               COALESCE(s.front_score, 0) <= 0 OR COALESCE(s.back_score, 0) <= 0
               OR COALESCE(s.front_putt, 0) <= 0 OR COALESCE(s.back_putt, 0) <= 0
               OR (COALESCE((to_jsonb(round_row)->>'has_extra')::boolean, false)
                   AND (COALESCE(s.extra_score, 0) <= 0 OR COALESCE(s.extra_putt, 0) <= 0))
           )) THEN RAISE EXCEPTION 'Complete scores and putts are required to finalize'; END IF;
        FOREACH field_name IN ARRAY ARRAY['match_pt', 'putt_pt', 'total_game_pt'] LOOP
            IF (SELECT sum((value->>field_name)::numeric) FROM jsonb_array_elements(p_results)) <> 0 THEN
                RAISE EXCEPTION 'Unbalanced points: %', field_name;
            END IF;
        END LOOP;
    END IF;

    IF p_replacement_handicaps IS NOT NULL THEN
        DELETE FROM public.handicap_match WHERE round_id = p_round_id;
        INSERT INTO public.handicap_match (
            round_id, player_1_id, player_2_id, player_1_to_2, player_2_to_1, total_only
        )
        SELECT p_round_id, player_1_id, player_2_id, player_1_to_2, player_2_to_1, total_only
        FROM jsonb_to_recordset(p_replacement_handicaps) AS incoming(
            player_1_id bigint, player_2_id bigint, player_1_to_2 integer,
            player_2_to_1 integer, total_only boolean
        );
    END IF;

    DELETE FROM public.round_results WHERE round_id = p_round_id;
    INSERT INTO public.round_results (round_id, member_id, match_front, match_back, match_total, match_extra, match_pt, putt_pt, temp_game_pt, total_game_pt)
    SELECT p_round_id, member_id, match_front, match_back, match_total, match_extra, match_pt, putt_pt, temp_game_pt, total_game_pt
    FROM jsonb_to_recordset(p_results) AS incoming(member_id bigint, match_front integer, match_back integer, match_total integer, match_extra integer, match_pt integer, putt_pt integer, temp_game_pt integer, total_game_pt integer);
    IF p_finalize THEN
        UPDATE public.rounds SET finalized = true WHERE round_id = p_round_id;
    END IF;
    RETURN jsonb_build_object('round_id', p_round_id, 'saved_players', player_count);
END;
$$;

REVOKE ALL ON FUNCTION public.save_golf_round_atomic(bigint, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, boolean) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.save_golf_round_atomic(bigint, jsonb, jsonb, jsonb, jsonb, jsonb, jsonb, boolean) TO service_role;
