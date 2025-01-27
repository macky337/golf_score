# scripts/insert_sample.py
import sys
import os

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from modules.db import SessionLocal
from modules.models import Member, Round

def insert_sample_data():
    session = SessionLocal()
    # 例: Member, Round, Score にINSERT
    member_x = Member(name="player-X")
    session.add(member_x)
    session.commit()
    session.close()
    print("Inserted sample member data.")

if __name__ == "__main__":
    insert_sample_data()
