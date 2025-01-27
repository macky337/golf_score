# scripts/example_check.py
import sys, os

# [追加] このスクリプトの1つ上のディレクトリ(= golf_score)をPythonパスに加える
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db import SessionLocal
from modules.models import Member

def main():
    session = SessionLocal()
    members = session.query(Member).all()
    for m in members:
        print(m.member_id, m.name)
    session.close()

if __name__ == "__main__":
    main()
