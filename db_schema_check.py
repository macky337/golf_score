"""
データベーススキーマを確認するためのユーティリティツール
実行方法: python db_schema_check.py
"""
from modules.supabase_client import get_supabase_client

def check_table_schema(table_name):
    """テーブルのスキーマ情報を取得して表示する"""
    try:
        print(f"\n=== {table_name} テーブルのスキーマ確認 ===")
        supabase = get_supabase_client()
        
        # データがあるかを確認
        result = supabase.table(table_name).select('*').limit(1).execute()
        
        if result.data:
            print(f"カラム一覧: {', '.join(sorted(result.data[0].keys()))}")
            print(f"サンプルデータ: {result.data[0]}")
            
            # サンプルデータを詳細表示
            print("\n詳細情報:")
            for key, value in sorted(result.data[0].items()):
                print(f"  {key}: {value} ({type(value).__name__})")
        else:
            print(f"警告: {table_name}テーブルにデータがありません")
            
        return True
    except Exception as e:
        print(f"エラー: {table_name}テーブル確認中に問題が発生しました: {e}")
        return False

def main():
    """主要テーブルのスキーマをチェック"""
    print("Golf Scoreデータベーススキーマ確認ツール")
    print("=============================")
    
    # 主要テーブルのチェック
    tables = ["rounds", "score", "round_results", "member", "handicap_match"]
    
    for table in tables:
        check_table_schema(table)
        
    print("\nスキーマ確認が完了しました。")
    print("結果を見て、コード内で使用しているカラム名が実際のスキーマと一致しているか確認してください。")

if __name__ == "__main__":
    main()
