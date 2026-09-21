-- 新しいアプリをデプロイする前に、Supabase SQL Editorで実行してください。
-- 入力値の比較、計算結果・確定状態の更新は1トランザクション。
-- SECURITY INVOKERのため、既存のテーブル権限とRLSがそのまま適用されます。
DROP FUNCTION IF EXISTS public.save_golf_round_atomic(bigint, jsonb, jsonb, jsonb, jsonb, jsonb, boolean);

CREATE OR REPLACE FUNCTION public.save_golf_round_atomic(
    p_round_id bigint,
    p_expected_scores jsonb,
    p_results jsonb,
    p_expected_round jsonb DEFAULT NULL,
    p_expected_handicaps jsonb DEFAULT NULL,
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
BEGIN
    SELECT * INTO round_row FROM public.rounds
        WHERE round_id = p_round_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Round not found'; END IF;
    IF p_finalize AND COALESCE(round_row.finalized, false) THEN
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

REVOKE ALL ON FUNCTION public.save_golf_round_atomic(bigint, jsonb, jsonb, jsonb, jsonb, boolean) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.save_golf_round_atomic(bigint, jsonb, jsonb, jsonb, jsonb, boolean) TO anon, authenticated, service_role;
