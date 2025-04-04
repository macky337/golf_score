-- RLSを完全に無効化する緊急対応スクリプト
-- ※注意: 本番環境では使用しないでください。テスト環境専用です

-- すべてのポリシーを削除して一からクリーンに
DROP POLICY IF EXISTS "Allow full access for authenticated users" ON "public"."round_results";
DROP POLICY IF EXISTS "Allow read access for anonymous users" ON "public"."round_results";
DROP POLICY IF EXISTS "Enable read access for authenticated users" ON "public"."round_results";
DROP POLICY IF EXISTS "Enable insert for authenticated users" ON "public"."round_results";
DROP POLICY IF EXISTS "Enable update for users based on id" ON "public"."round_results";
DROP POLICY IF EXISTS "Enable delete for users based on id" ON "public"."round_results";

-- RLSを無効化
ALTER TABLE "public"."round_results" DISABLE ROW LEVEL SECURITY;

-- すべてのユーザーに権限を与える
GRANT ALL ON "public"."round_results" TO authenticated;
GRANT ALL ON "public"."round_results" TO anon;
GRANT ALL ON "public"."round_results" TO service_role;

-- テスト用データ挿入を修正（外部キー制約のため）
DO $$
DECLARE
  test_round_id INT;
BEGIN
  -- 既存のテストデータがあるか確認
  SELECT round_id INTO test_round_id FROM rounds WHERE round_id = 9999;
  
  -- テスト用のラウンドが存在しない場合は作成
  IF test_round_id IS NULL THEN
    -- まずroundsテーブルにテスト用レコードを作成
    INSERT INTO rounds (round_id, date_played, course_name, num_players, has_extra, finalized)
    VALUES (9999, CURRENT_DATE, 'テスト用コース', 3, false, false)
    ON CONFLICT (round_id) DO NOTHING;
  END IF;
  
  -- テスト用のround_resultsデータを挿入
  DELETE FROM round_results WHERE round_id = 9999;
  
  INSERT INTO round_results (round_id, member_id, match_front, total_pt)
  VALUES (9999, 1, 10, 10)
  ON CONFLICT DO NOTHING;
  
  -- テスト成功メッセージ
  RAISE NOTICE 'テストデータの挿入が完了しました';
EXCEPTION
  WHEN OTHERS THEN
    -- エラーが発生した場合はエラーを報告するが処理は続行
    RAISE NOTICE 'テストデータ挿入中にエラーが発生しました: %', SQLERRM;
END
$$;
