import os
from modules.supabase_client import get_supabase_client

def main():
    supabase = get_supabase_client()
    
    # round_results テーブルからデータを取得する単純な方法
    result = supabase.table("round_results").select("*").limit(1).execute()
    
    if result.data:
        print("round_resultsテーブルが存在し、以下のキー構造を持っています:")
        sample_record = result.data[0]
        for key in sample_record.keys():
            print(f"- {key}")
    else:
        # テーブルが存在しない場合は別の名前かもしれない
        print("round_resultsテーブルからデータを取得できませんでした。テーブル名が異なる可能性があります。")
        # 全テーブルリストの取得を試みる（可能であれば）
        try:
            from supabase.lib.client_options import ClientOptions
            print("Supabase内の利用可能なテーブルを確認中...")
            # この部分はSupabaseのバージョンによって異なる場合があります
        except ImportError:
            print("Supabaseクライアントのバージョンによっては、テーブルリストの取得ができない場合があります。")

if __name__ == "__main__":
    main()
