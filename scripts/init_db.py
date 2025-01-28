# scripts/init_db.py
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db import engine, Base
from modules.models import Member, Round, Score, MatchHandicap

def init_db():
    # 既存のテーブルを全て削除（必要に応じてコメントアウト）
    Base.metadata.drop_all(bind=engine)
    # テーブルを全て作成
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("データベースの初期化が完了しました。")
