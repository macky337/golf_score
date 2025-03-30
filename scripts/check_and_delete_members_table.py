import os
import sys
from modules.supabase_client import get_supabase_client

def main():
    print("Supabase テーブル確認・削除ユーティリティ")
    print("-------------------------------------")
    supabase = get_supabase_client()
    
    # 既知のテーブルリスト
    tables_to_check = [
        "rounds", 
        "score", 
        "members",  # 削除候補
        "handicap_match", 
        "round_results",
        "courses",
        "member"
    ]
    
    existing_tables = []
    
    # 既存テーブルを確認
    print("\n1. 既存テーブルの確認中...")
    for table_name in tables_to_check:
        try:
            # テーブルが存在するか確認（レコードを0件取得してみる）
            result = supabase.table(table_name).select("*").limit(0).execute()
            existing_tables.append(table_name)
            print(f"  ✓ テーブル '{table_name}' が存在します")
            
            # レコード数を確認
            count_result = supabase.table(table_name).select("*", count="exact").execute()
            record_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
            print(f"    - レコード数: {record_count}")
            
            # テーブル構造を確認（サンプルレコードの取得）
            if count_result.data:
                sample = supabase.table(table_name).select("*").limit(1).execute()
                if sample.data:
                    print(f"    - カラム: {', '.join(sample.data[0].keys())}")
        except Exception as e:
            print(f"  ✗ テーブル '{table_name}' は存在しないか、エラーが発生しました: {str(e)}")
    
    # members テーブルが存在する場合
    if "members" in existing_tables:
        print("\n2. 'members' テーブルが見つかりました。")
        
        # 確認
        confirm = input("  'members' テーブルを削除しますか？[y/N]: ")
        
        if confirm.lower() == 'y':
            try:
                # レコードの有無を確認
                members_count = supabase.table("members").select("*", count="exact").execute()
                record_count = members_count.count if hasattr(members_count, 'count') else len(members_count.data)
                
                if record_count > 0:
                    print(f"  ⚠ 警告: members テーブルには {record_count} 件のレコードが存在します。")
                    final_confirm = input("  本当に削除しますか？このアクションは元に戻せません。[y/N]: ")
                    
                    if final_confirm.lower() != 'y':
                        print("  削除をキャンセルしました。")
                        return
                
                # テーブル削除（SQLクエリ実行）
                supabase.table("members").delete().neq("id", 0).execute()
                print("  ✓ 'members' テーブルのレコードを削除しました。")
                
                # Supabaseではテーブル自体の削除はRLS制約等があり複雑なため警告を表示
                print("\n  ℹ 注意: Supabaseでテーブルスキーマ自体を削除するには、")
                print("    Supabase管理画面のTable Editorから操作するか、")
                print("    SQLエディタで 'DROP TABLE members;' を実行してください。")
                
            except Exception as e:
                print(f"  ✗ エラー: {str(e)}")
        else:
            print("  削除をキャンセルしました。")
    else:
        print("\n2. 'members' テーブルは存在しません。")
        print("  追加の操作は必要ありません。")

if __name__ == "__main__":
    main()
