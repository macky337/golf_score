-- round_resultsテーブルのRLSポリシーを確認
-- 既存のポリシーを一時的に無効化または削除
DROP POLICY IF EXISTS "Enable read access for authenticated users" ON "public"."round_results";
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON "public"."round_results";
DROP POLICY IF EXISTS "Enable update for users based on id" ON "public"."round_results";
DROP POLICY IF EXISTS "Enable delete for users based on id" ON "public"."round_results";

-- 新しいポリシーを作成
-- 認証されたユーザーにCRUDアクセスを許可する
CREATE POLICY "Allow full access for authenticated users" 
ON "public"."round_results"
FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- 認証されていないユーザーには読み取りのみを許可する
CREATE POLICY "Allow read access for anonymous users" 
ON "public"."round_results"
FOR SELECT
TO anon
USING (true);
