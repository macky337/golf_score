import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

def get_latest_backup():
    """最新のバックアップファイルを取得"""
    backup_dir = "backups"
    backup_files = [f for f in os.listdir(backup_dir) 
                   if f.startswith("remote_main_backup_") and f.endswith(".json")]
    
    if not backup_files:
        raise FileNotFoundError("バックアップファイルが見つかりません")
    
    latest_backup = max(backup_files)
    return os.path.join(backup_dir, latest_backup)

def connect_to_supabase() -> Client:
    """Supabaseに接続"""
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URLまたはSUPABASE_KEYが設定されていません")
    
    return create_client(url, key)

def restore_to_supabase():
    """バックアップデータをSupabaseに復元"""
    try:
        backup_file = get_latest_backup()
        print(f"バックアップファイル '{backup_file}' から復元を開始します...")
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        supabase = connect_to_supabase()
        
        # テーブル構造の確認
        print("Supabaseのテーブル構造を確認中...")
        result = supabase.table('score').select('*').limit(1).execute()
        if result.data:
            print(f"テーブル構造: {list(result.data[0].keys())}")
            print(f"サンプルデータ: {result.data[0]}")
        
        success_count = 0
        error_count = 0
        
        for score in backup_data['scores']:
            try:
                # 更新前のデータを確認
                current = supabase.table('score').select('*').eq('score_id', score['score_id']).execute()
                if current.data:
                    print(f"\n更新前 (ID: {score['score_id']}): {current.data[0]}")
                
                # データ更新
                result = supabase.table('score').update({
                    'front_game_pt': score['front_game_pt'],
                    'back_game_pt': score['back_game_pt'],
                    'extra_game_pt': score['extra_game_pt']
                }).eq('score_id', score['score_id']).execute()
                
                # 更新後のデータを確認
                if result.data:
                    print(f"更新後: {result.data[0]}")
                
                success_count += 1
                if success_count % 5 == 0:  # 5件ごとに進捗を表示
                    print(f"進捗: {success_count}件更新完了")
                
            except Exception as e:
                error_count += 1
                print(f"スコアID {score['score_id']} の更新に失敗: {str(e)}")
                print(f"エラー詳細: {e.__class__.__name__}")
        
        print(f"\n復元完了:")
        print(f"成功: {success_count}件")
        print(f"失敗: {error_count}件")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        restore_to_supabase()
        print("\n復元プロセスが完了しました")
    except Exception as e:
        print(f"復元プロセスが失敗しました: {str(e)}")