-- セキュリティ設定を修正するためのスクリプト
-- 警告: このスクリプトを実行すると、RLSが有効になり、正しく設定されていないとアクセスできなくなる場合があります

-- まず既存のポリシーを削除（クリーンな状態にするため）
DROP POLICY IF EXISTS "Allow full access for authenticated users" ON "public"."round_results";
DROP POLICY IF EXISTS "Allow read access for anonymous users" ON "public"."round_results";
DROP POLICY IF EXISTS "Allow all operations" ON "public"."round_results";
DROP POLICY IF EXISTS "Allow authenticated INSERT on round_results" ON "public"."round_results";
DROP POLICY IF EXISTS "Allow authenticated SELECT on round_results" ON "public"."round_results";
DROP POLICY IF EXISTS "Enable read access for all users" ON "public"."round_results";
DROP POLICY IF EXISTS "allow_insert_for_authenticated" ON "public"."round_results";
-- 既存のポリシーを明示的にドロップ
DROP POLICY IF EXISTS "authenticated_full_access" ON "public"."round_results";
DROP POLICY IF EXISTS "anon_read_only" ON "public"."round_results";

-- RLSを有効化
ALTER TABLE "public"."round_results" ENABLE ROW LEVEL SECURITY;

-- 適切なポリシーを作成
-- 認証されたユーザーに全ての操作を許可
CREATE POLICY "authenticated_full_access" 
ON "public"."round_results"
FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- 匿名ユーザーには読み取りのみを許可
CREATE POLICY "anon_read_only" 
ON "public"."round_results"
FOR SELECT
TO anon
USING (true);

-- テーブルへの権限を設定
GRANT ALL ON "public"."round_results" TO authenticated;
GRANT SELECT ON "public"."round_results" TO anon;

-- 確認用
SELECT tablename, policyname 
FROM pg_policies 
WHERE tablename = 'round_results';

-- RLS状態を確認
SELECT relname, relrowsecurity 
FROM pg_class 
WHERE relname = 'round_results';
