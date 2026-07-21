-- Supabase SQL Editor で一度実行してください。
-- 途中で1件でも失敗した場合、関数内の削除・挿入はすべてロールバックされます。

CREATE OR REPLACE FUNCTION public.restore_golf_score_backup(backup_data jsonb)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = public
AS $$
DECLARE
    restored_counts jsonb;
    sequence_name text;
BEGIN
    IF backup_data IS NULL OR jsonb_typeof(backup_data) <> 'object' THEN
        RAISE EXCEPTION 'backup_data must be a JSON object';
    END IF;

    IF jsonb_typeof(COALESCE(backup_data->'members', '[]'::jsonb)) <> 'array'
       OR jsonb_typeof(COALESCE(backup_data->'rounds', '[]'::jsonb)) <> 'array'
       OR jsonb_typeof(COALESCE(backup_data->'scores', '[]'::jsonb)) <> 'array'
       OR jsonb_typeof(COALESCE(backup_data->'handicap_matches', '[]'::jsonb)) <> 'array'
       OR jsonb_typeof(COALESCE(backup_data->'round_results', '[]'::jsonb)) <> 'array'
       OR jsonb_typeof(COALESCE(backup_data->'app_settings', '[]'::jsonb)) <> 'array' THEN
        RAISE EXCEPTION 'backup table values must be JSON arrays';
    END IF;

    DELETE FROM public.round_results;
    DELETE FROM public.handicap_match;
    DELETE FROM public.score;
    DELETE FROM public.rounds;
    DELETE FROM public.member;
    DELETE FROM public.app_settings;

    INSERT INTO public.app_settings
    SELECT * FROM jsonb_populate_recordset(
        NULL::public.app_settings,
        COALESCE(backup_data->'app_settings', '[]'::jsonb)
    );

    INSERT INTO public.member
    SELECT * FROM jsonb_populate_recordset(
        NULL::public.member,
        COALESCE(backup_data->'members', '[]'::jsonb)
    );

    INSERT INTO public.rounds
    SELECT * FROM jsonb_populate_recordset(
        NULL::public.rounds,
        COALESCE(backup_data->'rounds', '[]'::jsonb)
    );

    INSERT INTO public.score
    SELECT * FROM jsonb_populate_recordset(
        NULL::public.score,
        COALESCE(backup_data->'scores', '[]'::jsonb)
    );

    INSERT INTO public.handicap_match
    SELECT * FROM jsonb_populate_recordset(
        NULL::public.handicap_match,
        COALESCE(backup_data->'handicap_matches', '[]'::jsonb)
    );

    INSERT INTO public.round_results
    SELECT * FROM jsonb_populate_recordset(
        NULL::public.round_results,
        COALESCE(backup_data->'round_results', '[]'::jsonb)
    );

    -- 明示的なIDを復元した後、次回INSERT用のシーケンスを追従させる。
    sequence_name := pg_get_serial_sequence('public.member', 'member_id');
    IF sequence_name IS NOT NULL THEN
        PERFORM setval(sequence_name, COALESCE((SELECT MAX(member_id) FROM public.member), 1), EXISTS (SELECT 1 FROM public.member));
    END IF;

    sequence_name := pg_get_serial_sequence('public.rounds', 'round_id');
    IF sequence_name IS NOT NULL THEN
        PERFORM setval(sequence_name, COALESCE((SELECT MAX(round_id) FROM public.rounds), 1), EXISTS (SELECT 1 FROM public.rounds));
    END IF;

    sequence_name := pg_get_serial_sequence('public.score', 'score_id');
    IF sequence_name IS NOT NULL THEN
        PERFORM setval(sequence_name, COALESCE((SELECT MAX(score_id) FROM public.score), 1), EXISTS (SELECT 1 FROM public.score));
    END IF;

    sequence_name := pg_get_serial_sequence('public.handicap_match', 'id');
    IF sequence_name IS NOT NULL THEN
        PERFORM setval(sequence_name, COALESCE((SELECT MAX(id) FROM public.handicap_match), 1), EXISTS (SELECT 1 FROM public.handicap_match));
    END IF;

    sequence_name := pg_get_serial_sequence('public.round_results', 'id');
    IF sequence_name IS NOT NULL THEN
        PERFORM setval(sequence_name, COALESCE((SELECT MAX(id) FROM public.round_results), 1), EXISTS (SELECT 1 FROM public.round_results));
    END IF;

    restored_counts := jsonb_build_object(
        'members', (SELECT COUNT(*) FROM public.member),
        'rounds', (SELECT COUNT(*) FROM public.rounds),
        'scores', (SELECT COUNT(*) FROM public.score),
        'handicap_matches', (SELECT COUNT(*) FROM public.handicap_match),
        'round_results', (SELECT COUNT(*) FROM public.round_results),
        'app_settings', (SELECT COUNT(*) FROM public.app_settings)
    );
    RETURN restored_counts;
END;
$$;

REVOKE ALL ON FUNCTION public.restore_golf_score_backup(jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.restore_golf_score_backup(jsonb) FROM anon;
REVOKE ALL ON FUNCTION public.restore_golf_score_backup(jsonb) FROM authenticated;
GRANT EXECUTE ON FUNCTION public.restore_golf_score_backup(jsonb) TO service_role;
