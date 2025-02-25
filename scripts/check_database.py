import sqlite3
import os

def check_database():
    """データベースの内容を確認"""
    # データベースパスの設定
    db_paths = [
        os.path.join(os.getcwd(), 'golf_app.db'),
        os.path.join(os.getcwd(), 'data', 'golf_app.db'),
        os.path.join(os.getcwd(), 'backups', 'golf_app.db')
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"\nデータベースファイル: {db_path}")
            print(f"ファイルサイズ: {os.path.getsize(db_path)} bytes")
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # テーブル一覧
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                print("\nテーブル一覧:")
                for table in tables:
                    print(f"- {table[0]}")
                    # 各テーブルのレコード数を表示
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    print(f"  レコード数: {count}")
                
                # scoreテーブルのサンプルデータ
                print("\nscoreテーブルの最新の5件:")
                cursor.execute("""
                    SELECT score_id, round_id, member_id, 
                           front_score, back_score, extra_score
                    FROM score
                    ORDER BY score_id DESC
                    LIMIT 5
                """)
                rows = cursor.fetchall()
                for row in rows:
                    print(f"ID: {row[0]}, Round: {row[1]}, Member: {row[2]}, "
                          f"Scores: {row[3]}/{row[4]}/{row[5]}")
                
            except Exception as e:
                print(f"エラー: {str(e)}")
            finally:
                conn.close()

if __name__ == "__main__":
    check_database()