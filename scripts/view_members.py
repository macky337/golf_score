# scripts/view_members.py
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db import SessionLocal
from modules.models import Member

def view_members():
    session = SessionLocal()
    try:
        members = session.query(Member).all()
        print("Members:")
        for member in members:
            print(f"ID: {member.member_id}, Name: {member.name}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    view_members()