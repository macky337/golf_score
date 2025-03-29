import os
from modules.supabase_client import get_supabase_client

def main():
    supabase = get_supabase_client()
    
    try:
        # 1. 利用可能なテーブル名を取得
        print("Supabaseのテーブル情報を取得中...")
        
        # publicスキーマ内の全テーブルを取得（直接テーブル名をクエリ）
        # これは supabase.from_() APIを使用する一般的な方法
        tables_to_check = [
            "rounds", 
            "score", 
            "members", 
            "handicap_match", 
            "round_results",
            "courses",  # 追加: コーステーブル
            "member"    # 追加: メンバーテーブル (members ではなく)
        ]
        
        print("\n=== Supabaseテーブル情報 ===\n")
        
        for table_name in tables_to_check:
            try:
                # 各テーブルのデータを1件だけ取得してカラム名を確認
                result = supabase.table(table_name).select("*").limit(1).execute()
                
                if result.data:
                    print(f"\n● テーブル: {table_name}")
                    print("  カラム:")
                    sample_record = result.data[0]
                    for key in sample_record.keys():
                        print(f"  - {key}")
                else:
                    # テーブルは存在するがデータがない場合
                    print(f"\n● テーブル: {table_name} (データなし)")
                    # テーブル構造だけ取得を試みる
                    try:
                        metadata = supabase.table(table_name).select("*").limit(0).execute()
                        print("  テーブルは存在しますが、データがありません。")
                    except Exception as e:
                        print(f"  エラー: {e}")
            except Exception as e:
                print(f"\n● テーブル: {table_name}")
                print(f"  エラー: {e}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
