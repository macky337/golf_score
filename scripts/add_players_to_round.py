# scripts\add_players_to_round.py
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.db import SessionLocal
from modules.models import Round, Member, Score
from datetime import date

def add_player_to_round(round_id, member_id):
    session = SessionLocal()
    try:
        # Round が存在するか確認
        round_obj = session.query(Round).filter(Round.round_id == round_id).first()
        if not round_obj:
            print(f"Round ID {round_id} が見つかりません。")
            return
        
        # Member が存在するか確認
        member = session.query(Member).filter(Member.member_id == member_id).first()
        if not member:
            print(f"Member ID {member_id} が見つかりません。")
            return
        
        # 既にスコアが存在するか確認
        existing_score = session.query(Score).filter(
            Score.round_id == round_id,
            Score.member_id == member_id
        ).first()
        if existing_score:
            print(f"Member ID {member_id} は既に Round ID {round_id} に関連付けられています。")
            return
        
        # Score エントリを作成
        new_score = Score(
            round_id=round_id,
            member_id=member_id,
            front_score=0,
            back_score=0,
            extra_score=0,
            front_putt=0,
            back_putt=0,
            extra_putt=0,
            front_game_pt=0,
            back_game_pt=0,
            extra_game_pt=0
        )
        session.add(new_score)
        session.commit()
        print(f"Member ID {member_id} を Round ID {round_id} に追加しました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # 必要なプレイヤーIDをここに追加
    add_player_to_round(round_id=7, member_id=1)
    add_player_to_round(round_id=7, member_id=2)