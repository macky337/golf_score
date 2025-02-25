from sqlalchemy import create_engine
from modules.models import Base
from modules.db import engine

def init_database():
    """SQLiteデータベースの初期化"""
    try:
        # テーブルの作成
        Base.metadata.create_all(engine)
        print("データベーステーブルを作成しました。")
        
    except Exception as e:
        print(f"データベース初期化エラー: {e}")

if __name__ == "__main__":
    init_database()