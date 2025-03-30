import os
from modules.supabase_client import get_supabase_client

def main():
    supabase = get_supabase_client()
    
    try:
        # 既知のテーブルに対してクエリを実行し、存在確認と構造を取得
        known_tables = [
            "rounds", "score", 
            # "members" テーブルは削除済み
            "handicap_match", "round_results", 
            # 追加指定されたテーブル
            "courses", "member",
            # 追加の可能性のあるテーブル
            "scores", "users", "players", "matches", "settings", "games"
        ]
        
        existing_tables = []
        
        print("=== テーブル探索中... ===\n")
        
        for table_name in known_tables:
            try:
                # 各テーブルの存在確認（SELECT * LIMIT 0）
                result = supabase.table(table_name).select("*").limit(0).execute()
                # エラーがなければテーブルは存在する
                existing_tables.append(table_name)
                print(f"✓ テーブル '{table_name}' が見つかりました")
            except Exception:
                # エラーが発生した場合はテーブルが存在しない
                print(f"✗ テーブル '{table_name}' は存在しません")
        
        print(f"\n合計 {len(existing_tables)} テーブルが見つかりました\n")
        
        # 見つかったテーブルのカラム情報を取得
        for table_name in existing_tables:
            try:
                # 各テーブルのデータを1件だけ取得してカラム名を確認
                result = supabase.table(table_name).select("*").limit(1).execute()
                
                print(f"\n● テーブル: {table_name}")
                if result.data:
                    print("  カラム:")
                    sample_record = result.data[0]
                    for key in sample_record.keys():
                        print(f"  - {key}")
                else:
                    print("  (データなし)")
            except Exception as e:
                print(f"  テーブル情報取得エラー: {e}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
