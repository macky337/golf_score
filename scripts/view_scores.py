# scripts/view_scores.py
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db import SessionLocal
from modules.models import Score

def view_scores():
    session = SessionLocal()
    try:
        scores = session.query(Score).all()
        print("Scores:")
        for score in scores:
            print(f"Round ID: {score.round_id}, Member ID: {score.member_id}, Front Score: {score.front_score}, Back Score: {score.back_score}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    view_scores()