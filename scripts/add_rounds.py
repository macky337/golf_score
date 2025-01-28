# scripts/add_rounds.py
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db import SessionLocal
from modules.models import Round
from datetime import date

def add_round(round_id, date_played, course_name, num_players, has_extra=False, finalized=False):
    session = SessionLocal()
    try:
        existing_round = session.query(Round).filter(Round.round_id == round_id).first()
        if existing_round:
            print(f"Round ID {round_id} は既に存在します。")
            return
        new_round = Round(
            round_id=round_id,
            date_played=date_played,
            course_name=course_name,
            num_players=num_players,
            has_extra=has_extra,
            finalized=finalized
        )
        session.add(new_round)
        session.commit()
        print(f"Round ID {round_id} を追加しました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    add_round(round_id=5, date_played=date(2025, 1, 28), course_name="Golf Course A", num_players=4)
    add_round(round_id=6, date_played=date(2025, 2, 15), course_name="Golf Course B", num_players=4)