from modules.supabase_client import get_supabase_client

def fix_security_direct_sql():
    """セキュリティ設定を直接SQLで修正する"""
    print("Golf Scoreデータベースセキュリティ修正ツール (シンプル版)")
    print("====================================")
    
    sql = """
    -- まずすべてのポリシーを削除
    DO $$
    DECLARE
        policy_record RECORD;
    BEGIN
        FOR policy_record IN 
            SELECT policyname 
            FROM pg_policies 
            WHERE tablename = 'round_results' 
        LOOP
            EXECUTE 'DROP POLICY IF EXISTS "' || policy_record.policyname || '" ON public.round_results';
            RAISE NOTICE 'Dropped policy: %', policy_record.policyname;
        END LOOP;
    END $$;

    -- RLSを一度無効化してからもう一度有効化 (リセットのため)
    ALTER TABLE public.round_results DISABLE ROW LEVEL SECURITY;
    ALTER TABLE public.round_results ENABLE ROW LEVEL SECURITY;

    -- シンプルなポリシーを作成
    CREATE POLICY "all_access_policy" ON public.round_results
    USING (true) WITH CHECK (true);

    -- 権限を確認
    GRANT ALL ON public.round_results TO authenticated;
    GRANT SELECT ON public.round_results TO anon;
    """
    
    print("\nSupabase Dashboard (https://supabase.com/dashboard) のSQL Editorで次のSQLを実行してください:")
    print("\n" + "-" * 60)
    print(sql)
    print("-" * 60)
    
    print("\nこのSQLを実行することで:")
    print("1. すべての既存ポリシーを削除")
    print("2. RLSをリセット (無効化してから再有効化)")
    print("3. すべてのユーザーに対するシンプルなアクセスポリシーを作成")
    print("4. 適切な権限を設定")
    
    print("\nSQL実行後、アプリケーションを再起動してください。")

if __name__ == "__main__":
    fix_security_direct_sql()
