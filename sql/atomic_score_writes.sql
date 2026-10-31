-- Run once in the Supabase SQL Editor before deploying the matching application.
-- Score entry and round setup are each performed in one PostgreSQL transaction.

CREATE TABLE IF NOT EXISTS public.app_settings (
    key text PRIMARY KEY,
    value jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
GRANT ALL ON TABLE public.app_settings TO service_role;

ALTER TABLE public.rounds
    ADD COLUMN IF NOT EXISTS rule_settings jsonb;

DO $$
DECLARE
    table_name text;
    column_name text;
    sequence_name text;
    current_max bigint;
BEGIN
    FOREACH table_name IN ARRAY ARRAY['rounds', 'score', 'handicap_match', 'member'] LOOP
        column_name := CASE table_name
            WHEN 'rounds' THEN 'round_id'
            WHEN 'score' THEN 'score_id'
            WHEN 'member' THEN 'member_id'
            ELSE 'id'
        END;
        sequence_name := pg_get_serial_sequence(format('public.%I', table_name), column_name);
        IF sequence_name IS NULL THEN
            sequence_name := format('public.%I', table_name || '_' || column_name || '_atomic_seq');
            EXECUTE format('CREATE SEQUENCE IF NOT EXISTS %s', sequence_name);
            EXECUTE format('ALTER SEQUENCE %s OWNED BY public.%I.%I', sequence_name, table_name, column_name);
            EXECUTE format(
                'ALTER TABLE public.%I ALTER COLUMN %I SET DEFAULT nextval(%L::regclass)',
                table_name, column_name, sequence_name
            );
        END IF;
        EXECUTE format('SELECT MAX(%I) FROM public.%I', column_name, table_name) INTO current_max;
        PERFORM setval(sequence_name::regclass, COALESCE(current_max, 1), current_max IS NOT NULL);
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION public.create_golf_round_atomic(
    p_round jsonb,
    p_member_ids bigint[],
    p_handicaps jsonb
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
DECLARE
    created_round_id bigint;
    participant_count integer;
BEGIN
    IF jsonb_typeof(p_round) IS DISTINCT FROM 'object'
       OR jsonb_typeof(COALESCE(p_handicaps, '[]'::jsonb)) IS DISTINCT FROM 'array'
       OR COALESCE(array_length(p_member_ids, 1), 0) < 2 THEN
        RAISE EXCEPTION 'Invalid round setup';
    END IF;
    IF (SELECT count(DISTINCT ids.member_id) FROM unnest(p_member_ids) AS ids(member_id))
       <> array_length(p_member_ids, 1) THEN
        RAISE EXCEPTION 'Duplicate participants';
    END IF;
    participant_count := array_length(p_member_ids, 1);
    IF COALESCE((p_round->>'num_players')::integer, -1) <> participant_count THEN
        RAISE EXCEPTION 'Participant count does not match round';
    END IF;
    IF EXISTS (
        SELECT 1 FROM unnest(p_member_ids) AS ids(member_id)
        WHERE NOT EXISTS (SELECT 1 FROM public.member m WHERE m.member_id = ids.member_id)
    ) THEN
        RAISE EXCEPTION 'Participant not found';
    END IF;

    INSERT INTO public.rounds
        (date_played, date, course_name, course_id, num_players, has_extra, finalized, rule_settings)
    VALUES
        ((p_round->>'date_played')::date,
         (p_round->>'date')::date,
         p_round->>'course_name',
         (p_round->>'course_id')::bigint,
         participant_count,
         COALESCE((p_round->>'has_extra')::boolean, false),
         false,
         COALESCE(p_round->'rule_settings', '{}'::jsonb))
    RETURNING round_id INTO created_round_id;

    INSERT INTO public.score
        (round_id, member_id, front_score, back_score, extra_score,
         front_putt, back_putt, extra_putt, front_game_pt, back_game_pt,
         extra_game_pt, total_score)
    SELECT created_round_id, ids.member_id, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    FROM unnest(p_member_ids) AS ids(member_id);

    IF jsonb_array_length(p_handicaps) > 0 THEN
        INSERT INTO public.handicap_match
            (round_id, player_1_id, player_2_id, player_1_to_2, player_2_to_1, total_only)
        SELECT created_round_id, player_1_id, player_2_id,
               player_1_to_2, player_2_to_1, COALESCE(total_only, false)
        FROM jsonb_to_recordset(p_handicaps) AS h(
            player_1_id bigint,
            player_2_id bigint,
            player_1_to_2 integer,
            player_2_to_1 integer,
            total_only boolean
        );
    END IF;

    RETURN jsonb_build_object('round_id', created_round_id, 'players', participant_count);
END;
$$;

CREATE OR REPLACE FUNCTION public.save_golf_score_segment_atomic(
    p_round_id bigint,
    p_segment text,
    p_records jsonb,
    p_allow_finalized boolean DEFAULT false
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
DECLARE
    round_is_finalized boolean;
    score_count integer;
    record_count integer;
    updated_count integer;
BEGIN
    IF p_segment IS NULL OR p_segment NOT IN ('front', 'back', 'extra', 'all')
       OR jsonb_typeof(p_records) IS DISTINCT FROM 'array' THEN
        RAISE EXCEPTION 'Invalid score update';
    END IF;

    SELECT COALESCE(finalized, false) INTO round_is_finalized
    FROM public.rounds WHERE round_id = p_round_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Round not found'; END IF;
    IF round_is_finalized AND NOT p_allow_finalized THEN
        RAISE EXCEPTION 'Finalized rounds cannot be edited here';
    END IF;

    PERFORM 1 FROM public.score WHERE round_id = p_round_id ORDER BY member_id FOR UPDATE;
    SELECT count(*) INTO score_count FROM public.score WHERE round_id = p_round_id;
    SELECT count(*), count(DISTINCT (rows.value->>'member_id')::bigint)
      INTO record_count, updated_count FROM jsonb_array_elements(p_records) AS rows(value);
    IF score_count = 0 OR record_count <> score_count OR updated_count <> score_count
       OR EXISTS (
           SELECT 1 FROM jsonb_array_elements(p_records) AS rows(value)
           WHERE NOT EXISTS (
               SELECT 1 FROM public.score s
               WHERE s.round_id = p_round_id AND s.member_id = (rows.value->>'member_id')::bigint
           )
       ) THEN
        RAISE EXCEPTION 'Update must contain each participant exactly once';
    END IF;

    IF p_segment = 'front' THEN
        UPDATE public.score s SET
            front_score = r.front_score, front_putt = r.front_putt,
            front_game_pt = r.front_game_pt,
            total_score = COALESCE(r.total_score, s.total_score)
        FROM jsonb_to_recordset(p_records) AS r(
            member_id bigint, front_score integer, front_putt integer,
            front_game_pt integer, total_score integer
        ) WHERE s.round_id = p_round_id AND s.member_id = r.member_id;
    ELSIF p_segment = 'back' THEN
        UPDATE public.score s SET
            back_score = r.back_score, back_putt = r.back_putt,
            back_game_pt = r.back_game_pt,
            total_score = COALESCE(r.total_score, s.total_score)
        FROM jsonb_to_recordset(p_records) AS r(
            member_id bigint, back_score integer, back_putt integer,
            back_game_pt integer, total_score integer
        ) WHERE s.round_id = p_round_id AND s.member_id = r.member_id;
    ELSIF p_segment = 'extra' THEN
        UPDATE public.score s SET
            extra_score = r.extra_score, extra_putt = r.extra_putt,
            extra_game_pt = r.extra_game_pt
        FROM jsonb_to_recordset(p_records) AS r(
            member_id bigint, extra_score integer, extra_putt integer,
            extra_game_pt integer
        ) WHERE s.round_id = p_round_id AND s.member_id = r.member_id;
    ELSE
        UPDATE public.score s SET
            front_score = r.front_score, front_putt = r.front_putt,
            front_game_pt = r.front_game_pt,
            back_score = r.back_score, back_putt = r.back_putt,
            back_game_pt = r.back_game_pt,
            extra_score = COALESCE(r.extra_score, s.extra_score),
            extra_putt = COALESCE(r.extra_putt, s.extra_putt),
            extra_game_pt = COALESCE(r.extra_game_pt, s.extra_game_pt),
            total_score = COALESCE(r.total_score, s.total_score)
        FROM jsonb_to_recordset(p_records) AS r(
            member_id bigint, front_score integer, front_putt integer,
            front_game_pt integer, back_score integer, back_putt integer,
            back_game_pt integer, extra_score integer, extra_putt integer,
            extra_game_pt integer, total_score integer
        ) WHERE s.round_id = p_round_id AND s.member_id = r.member_id;
    END IF;
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    IF updated_count <> record_count THEN
        RAISE EXCEPTION 'Not all score records were updated';
    END IF;
    RETURN jsonb_build_object('round_id', p_round_id, 'updated_players', updated_count);
END;
$$;

REVOKE ALL ON FUNCTION public.create_golf_round_atomic(jsonb, bigint[], jsonb) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.save_golf_score_segment_atomic(bigint, text, jsonb, boolean) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.create_golf_round_atomic(jsonb, bigint[], jsonb) TO service_role;
GRANT EXECUTE ON FUNCTION public.save_golf_score_segment_atomic(bigint, text, jsonb, boolean) TO service_role;
