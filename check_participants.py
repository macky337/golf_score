from modules.db import SessionLocal
from modules.models import Round, Score, Member

def check_participants(round_id):
    session = SessionLocal()
    try:
        round_instance = session.query(Round).filter(Round.round_id == round_id).first()
        if not round_instance:
            print(f"Round ID {round_id} が見つかりません。")
            return

        scores = session.query(Score).filter(Score.round_id == round_id).all()
        participants = [score.member.name for score in scores if score.member]
        print(f"Round ID {round_id} の参加者数: {len(participants)}")
        print(f"参加者リスト: {participants}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_participants(round_id=6)