# filepath: /c:/Users/user/Documents/GitHub/golf_score/add_participant.py
from modules.db import SessionLocal
from modules.models import Member, Round, Score

def add_participant(round_id, member_name, base_handicap=0):
    session = SessionLocal()
    try:
        # メンバーの作成
        new_member = Member(name=member_name, base_handicap=base_handicap)
        session.add(new_member)
        session.commit()
        session.refresh(new_member)

        # ラウンドの取得
        round_instance = session.query(Round).filter(Round.round_id == round_id).first()
        if not round_instance:
            print(f"Round ID {round_id} が見つかりません。")
            return

        # スコアの作成
        new_score = Score(round_id=round_id, member_id=new_member.member_id)
        session.add(new_score)
        session.commit()

        print(f"メンバー '{member_name}' がラウンドID {round_id} に追加されました。")
    except Exception as e:
        session.rollback()
        print(f"エラーが発生しました: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    add_participant(round_id=5, member_name="Jane Smith", base_handicap=12)