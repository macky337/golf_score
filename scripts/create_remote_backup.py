import sqlite3
import json
from datetime import datetime
import os
from pathlib import Path

def find_database():
    """データベースファイルを検索"""
    search_paths = [
        os.path.join(os.getcwd(), 'golf_app.db'),            # ルートディレクトリ
        os.path.join(os.getcwd(), 'backups', 'golf_app.db'), # backupsディレクトリ
        os.path.join(os.getcwd(), 'data', 'golf_app.db'),    # dataディレクトリ
    ]
    
    print("データベースファイルを検索中...")
    for path in search_paths:
        if os.path.exists(path):
            print(f"データベースが見つかりました: {path}")
            # データが存在するか確認
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM score")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 0:
                print(f"スコアデータあり（{count}件）- このDBを使用します")
                return path
            else:
                print("スコアデータなし - スキップします")
    
    raise FileNotFoundError("有効なデータベースファイルが見つかりません")

def create_backup_from_sqlite():
    """SQLiteデータベースからgame_ptを含むバックアップを作成"""
    db_path = find_database()
    print(f"\n使用するデータベース: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # game_ptデータの取得
        cursor.execute('''
            SELECT 
                score_id,
                round_id,
                member_id,
                front_game_pt,
                back_game_pt,
                extra_game_pt
            FROM score
            ORDER BY score_id
        ''')
        
        scores = cursor.fetchall()
        print(f"\n取得したスコア数: {len(scores)}")
        
        backup_data = {
            'scores': [
                {
                    'score_id': score[0],
                    'round_id': score[1],
                    'member_id': score[2],
                    'front_game_pt': score[3],
                    'back_game_pt': score[4],
                    'extra_game_pt': score[5]
                }
                for score in scores
            ]
        }
        
        # バックアップファイルの保存
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{backup_dir}/remote_main_backup_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nバックアップファイルを作成しました: {filename}")
        print(f"スコアデータ数: {len(backup_data['scores'])}")
        
        return filename
        
    finally:
        conn.close()

if __name__ == "__main__":
    try:
        backup_file = create_backup_from_sqlite()
        print(f"\nバックアップが正常に完了しました: {backup_file}")
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()