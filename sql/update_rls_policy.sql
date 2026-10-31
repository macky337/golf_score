-- 既存のポリシーを確認してから更新する修正スクリプト

DROP POLICY IF EXISTS "Allow full access for authenticated users" ON "public"."round_results";
DROP POLICY IF EXISTS "authenticated_full_access" ON "public"."round_results";

DROP POLICY IF EXISTS "Allow read access for anonymous users" ON "public"."round_results";
DROP POLICY IF EXISTS "anon_read_only" ON "public"."round_results";

REVOKE ALL ON "public"."round_results" FROM anon, authenticated;

-- RLSが有効になっているか確認
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE tablename = 'round_results' 
        AND rowsecurity = true
    ) THEN
        -- RLSが無効の場合は有効化
        EXECUTE 'ALTER TABLE "public"."round_results" ENABLE ROW LEVEL SECURITY';
    END IF;
END
$$;

-- テーブルへの権限確認
GRANT ALL ON "public"."round_results" TO service_role;
