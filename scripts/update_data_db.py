import sqlite3
import os
import shutil
from datetime import datetime

def update_data_database():
    """dataディレクトリのデータベースを更新"""
    # パスの設定
    root_db = os.path.join(os.getcwd(), 'golf_app.db')
    data_db = os.path.join(os.getcwd(), 'data', 'golf_app.db')
    backup_dir = os.path.join(os.getcwd(), 'data', 'backups')
    
    # バックアップディレクトリの作成
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        # 現在のdata/golf_app.dbのバックアップを作成
        if os.path.exists(data_db):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f'golf_app_{timestamp}.db')
            shutil.copy2(data_db, backup_path)
            print(f"現在のデータベースをバックアップしました: {backup_path}")
        
        # ルートディレクトリのDBをdataディレクトリにコピー
        shutil.copy2(root_db, data_db)
        print(f"データベースを更新しました: {data_db}")
        
        # データの確認
        conn = sqlite3.connect(data_db)
        cursor = conn.cursor()
        
        # テーブル一覧とレコード数の確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\nテーブル一覧とレコード数:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"- {table[0]}: {count}件")
        
        conn.close()
        print("\nデータベースの更新が完了しました")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        raise

if __name__ == "__main__":
    update_data_database()