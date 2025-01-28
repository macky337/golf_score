# scripts/view_data.py
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db import SessionLocal
from modules.models import Round, HandicapMatch, Member, Score

def view_data():
    session = SessionLocal()
    try:
        rounds = session.query(Round).all()
        print("Rounds:")
        for rnd in rounds:
            print(f"ID: {rnd.round_id}, Course: {rnd.course_name}, Date: {rnd.date_played}")

        matches = session.query(HandicapMatch).all()
        print("\nHandicap Matches:")
        for match in matches:
            print(f"Match ID: {match.match_id}, Round ID: {match.round_id}, Player 1 ID: {match.player_1_id}, Player 2 ID: {match.player_2_id}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    view_data()