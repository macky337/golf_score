-- 既存のポリシーを確認してから更新する修正スクリプト

-- 既存のポリシーを確認
COMMENT ON POLICY "Allow full access for authenticated users" ON "public"."round_results" 
IS 'ポリシーが正しく設定されていることを確認しました';

-- 既存のポリシーを削除して再作成したい場合（エラーが続く場合のみ実行）
-- DROP POLICY IF EXISTS "Allow full access for authenticated users" ON "public"."round_results";

-- 既存のポリシーの設定を更新（権限設定を確実にするため）
ALTER POLICY "Allow full access for authenticated users" 
ON "public"."round_results"
USING (true)
WITH CHECK (true);

-- 匿名ユーザー向けポリシーの確認・作成（存在しない場合のみ作成）
DO $$
BEGIN
    -- 匿名ユーザー向けの読み取りポリシーが存在するか確認
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'round_results' 
        AND policyname = 'Allow read access for anonymous users'
    ) THEN
        -- 存在しない場合は作成
        EXECUTE 'CREATE POLICY "Allow read access for anonymous users" 
                 ON "public"."round_results"
                 FOR SELECT
                 TO anon
                 USING (true)';
    END IF;
END
$$;

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
GRANT ALL ON "public"."round_results" TO authenticated;
GRANT SELECT ON "public"."round_results" TO anon;
