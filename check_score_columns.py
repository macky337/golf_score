import os
from supabase import create_client
from dotenv import load_dotenv

def check_score_columns():
    """Supabaseのscoreテーブルのカラムを確認する"""
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("環境変数が設定されていません")
        return
    
    # Supabaseに接続
    supabase = create_client(url, key)
    
    try:
        # scoreテーブルのデータを1件取得してカラム構造を確認
        score_data = supabase.table('score').select('*').limit(1).execute()
        if score_data.data:
            print("=== scoreテーブルのカラム一覧 ===")
            columns = list(score_data.data[0].keys())
            columns.sort()
            
            for column in columns:
                print(f"- {column}")
            
            print(f"\n総カラム数: {len(columns)}")
            
            # total_ptカラムの存在確認
            if 'total_pt' in columns:
                print("✓ total_ptカラムが存在します")
            else:
                print("✗ total_ptカラムが存在しません")
            
            print("\nサンプルデータ:")
            for key, value in score_data.data[0].items():
                print(f"  {key}: {value}")
                
        else:
            print("scoreテーブルにデータがありません")
            
    except Exception as e:
        print(f"エラー: {str(e)}")

if __name__ == "__main__":
    check_score_columns()
