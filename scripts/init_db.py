# scripts/init_db.py
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db import Base, engine
from modules.models import Member, Round, Score, HandicapMatch

def init_db():
    # Alembic を使用してテーブルを管理するため、直接作成しない
    print("データベースの初期化は Alembic を通じて行ってください。")

if __name__ == "__main__":
    init_db()
