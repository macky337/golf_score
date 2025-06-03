from modules.supabase_client import get_supabase_client

def main():
    supabase = get_supabase_client()

    # round_resultsテーブルの構造を確認
    print('=== round_results テーブル構造 ===')
    try:
        result = supabase.table('round_results').select('*').limit(1).execute()
        if result.data:
            print('カラム一覧:')
            for col in sorted(result.data[0].keys()):
                print(f'- {col}')
            print()
            
            # total_ptカラムの存在確認
            has_total_pt = 'total_pt' in result.data[0]
            print(f'total_ptカラムの存在: {has_total_pt}')
        else:
            print('データがありません')
    except Exception as e:
        print(f'エラー: {e}')

    print()

    # scoreテーブルの構造も確認
    print('=== score テーブル構造 ===')
    try:
        result = supabase.table('score').select('*').limit(1).execute()
        if result.data:
            print('カラム一覧:')
            for col in sorted(result.data[0].keys()):
                print(f'- {col}')
            print()
            
            # total_ptカラムの存在確認
            has_total_pt = 'total_pt' in result.data[0]
            print(f'total_ptカラムの存在: {has_total_pt}')
        else:
            print('データがありません')
    except Exception as e:
        print(f'エラー: {e}')

if __name__ == "__main__":
    main()
