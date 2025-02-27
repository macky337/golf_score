import os
from supabase import create_client
from dotenv import load_dotenv

def check_score_table():
    """Supabaseのscoreテーブル構造を確認する"""
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("環境変数が設定されていません")
        return
    
    # Supabaseに接続
    supabase = create_client(url, key)
    
    try:
        # scoreテーブルのデータを取得して構造を確認
        score_data = supabase.table('score').select('*').limit(1).execute()
        if score_data.data:
            print("\n=== scoreテーブルの構造 ===")
            print("カラム一覧:")
            for column in score_data.data[0].keys():
                print(f"- {column}")
            
            print("\nサンプルデータ:")
            print(score_data.data[0])
        else:
            print("\nscoreテーブルにデータがありません")
            
        # 他にもテーブル情報を取得
        for table in ['rounds', 'member', 'handicap_match']:
            try:
                data = supabase.table(table).select('*').limit(1).execute()
                if data.data:
                    print(f"\n=== {table}テーブルの構造 ===")
                    print("カラム一覧:")
                    for column in data.data[0].keys():
                        print(f"- {column}")
                else:
                    print(f"\n{table}テーブルにデータがありません")
            except Exception as e:
                print(f"{table}テーブルの確認中にエラー: {str(e)}")
    
    except Exception as e:
        print(f"エラー: {str(e)}")

if __name__ == "__main__":
    check_score_table()