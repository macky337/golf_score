import sys
from modules.db import SessionLocal
from modules.models import HandicapMatch, Round, Score

def setup_handicap_match(round_id):
    session = SessionLocal()
    try:
        # ラウンドの取得
        round_instance = session.query(Round).filter(Round.round_id == round_id).first()
        if not round_instance:
            print(f"Round ID {round_id} が見つかりません。")
            return

        # 参加者の取得
        scores = session.query(Score).filter(Score.round_id == round_id).all()
        if len(scores) < 2:
            print("Not enough participants for a match.")
            return

        # HandicapMatchの作成
        new_match = HandicapMatch(
            round_id=round_id,
            player_1_id=scores[0].member_id,
            player_2_id=scores[1].member_id
        )
        session.add(new_match)
        session.commit()
        print(f"Handicap Match がラウンドID {round_id} にセットアップされました。")
    except Exception as e:
        session.rollback()
        print(f"エラーが発生しました: {e}")
    finally:
        session.close()

def setup_match(round_id):
    session = SessionLocal()
    try:
        round_exists = session.query(Round).filter(Round.round_id == round_id).first()
        if not round_exists:
            print(f"Round ID {round_id} が見つかりません。")
            return
        
        matches = session.query(HandicapMatch).filter(HandicapMatch.round_id == round_id).all()
        if not matches:
            print(f"Round ID {round_id} にマッチは存在しません。")
            # ここでマッチを作成するロジックを追加
            # 例:
            # new_match = HandicapMatch(round_id=round_id, player_1_id=1, player_2_id=2)
            # session.add(new_match)
            # session.commit()
            print(f"Round ID {round_id} に新しいマッチを追加しました。")
        else:
            print(f"Round ID {round_id} に既にマッチが存在します。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python match_setup.py <round_id>")
    else:
        try:
            round_id = int(sys.argv[1])
            setup_handicap_match(round_id)
        except ValueError:
            print("ラウンドID は整数で指定してください。")