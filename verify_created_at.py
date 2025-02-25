from modules.db import engine
from modules.models import Member, Round, Score, HandicapMatch
from sqlalchemy.orm import sessionmaker
import datetime

SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

def verify_member_created_at():
    # 新たなメンバーを登録する（サンプル）
    new_member = Member(name="テストユーザー")
    session.add(new_member)
    session.commit()
    
    # 登録済みのメンバーを全て取得して表示する
    members = session.query(Member).all()
    for m in members:
        print(f"ID: {m.member_id}, Name: {m.name}, Created At: {m.created_at}")

if __name__ == "__main__":
    verify_member_created_at()
    session.close()