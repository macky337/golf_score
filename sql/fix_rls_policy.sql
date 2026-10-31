-- round_resultsテーブルのRLSポリシーを確認
-- 既存のポリシーを一時的に無効化または削除
DROP POLICY IF EXISTS "Enable read access for authenticated users" ON "public"."round_results";
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON "public"."round_results";
DROP POLICY IF EXISTS "Enable update for users based on id" ON "public"."round_results";
DROP POLICY IF EXISTS "Enable delete for users based on id" ON "public"."round_results";
DROP POLICY IF EXISTS "Allow full access for authenticated users" ON "public"."round_results";
DROP POLICY IF EXISTS "authenticated_full_access" ON "public"."round_results";
DROP POLICY IF EXISTS "Allow read access for anonymous users" ON "public"."round_results";
DROP POLICY IF EXISTS "anon_read_only" ON "public"."round_results";

REVOKE ALL ON "public"."round_results" FROM anon, authenticated;
GRANT ALL ON "public"."round_results" TO service_role;
