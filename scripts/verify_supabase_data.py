import os
from supabase import create_client, Client
from dotenv import load_dotenv

def verify_supabase_data():
    """Supabaseのデータを確認"""
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("環境変数が設定されていません")
    
    supabase = create_client(url, key)
    
    # スコアデータの確認
    result = supabase.table('score').select('*').execute()
    
    if result.data:
        print(f"\n総スコア数: {len(result.data)}")
        print("\nサンプルデータ（最初の3件）:")
        for score in result.data[:3]:
            print(f"\nスコアID: {score['score_id']}")
            print(f"game_pt: {score['front_game_pt']}/{score['back_game_pt']}/{score['extra_game_pt']}")
    else:
        print("スコアデータが見つかりません")

if __name__ == "__main__":
    verify_supabase_data()