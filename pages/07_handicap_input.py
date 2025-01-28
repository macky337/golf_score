# pages/07_handicap_input.py

import streamlit as st
from modules.db import SessionLocal
from modules.models import Round, Member, HandicapMatch

def run():
    """マッチ形式でのペアごとのハンデ設定ページ"""
    st.title("Handicap Match Setup")

    # 1) ラウンド選択フォーム
    session = SessionLocal()

    # 未確定のラウンドを取得
    active_round = session.query(Round).filter_by(finalized=False).order_by(Round.round_id.desc()).first()
    if not active_round:
        st.warning("No active round found. Please set up and finalize a round first.")
        session.close()
        return

    st.write(f"**Round ID**: {active_round.round_id}, **Course**: {active_round.course_name}")

    # 2) 該当ラウンドの参加メンバーを取得
    participants = session.query(Member).join(
        HandicapMatch,
        (HandicapMatch.round_id == active_round.round_id) &
        (HandicapMatch.player_1_id == Member.member_id)  # 明示的にplayer_1_idを使用
    ).all()

    if len(participants) < 2:
        st.warning("Not enough participants for a match.")
        session.close()
        return

    # 3) ペアごとのハンデ設定を入力
    st.write("Select the pairs and specify the handicap (打数) each player will give.")
    
    pairings = []

    for i in range(len(participants)):
        for j in range(i + 1, len(participants)):
            player_1 = participants[i]
            player_2 = participants[j]

            # ペアごとに何打ハンデを渡すかを入力
            st.subheader(f"Match: {player_1.name} vs {player_2.name}")

            player_1_to_2 = st.number_input(f"How many shots will {player_1.name} give to {player_2.name}?", min_value=0, max_value=20, value=0, key=f"handicap_{player_1.member_id}_{player_2.member_id}_1to2")
            player_2_to_1 = st.number_input(f"How many shots will {player_2.name} give to {player_1.name}?", min_value=0, max_value=20, value=0, key=f"handicap_{player_1.member_id}_{player_2.member_id}_2to1")

            pairings.append({
                'player_1_id': player_1.member_id,
                'player_2_id': player_2.member_id,
                'player_1_to_2': player_1_to_2,
                'player_2_to_1': player_2_to_1,
            })

    # 4) 保存ボタン
    if st.button("Save Handicap Settings"):
        for pairing in pairings:
            # ハンデ設定をhandicap_matchテーブルに保存
            new_handicap = HandicapMatch(
                round_id=active_round.round_id,
                player_1_id=pairing['player_1_id'],
                player_2_id=pairing['player_2_id'],
                player_1_to_2=pairing['player_1_to_2'],
                player_2_to_1=pairing['player_2_to_1']
            )
            session.add(new_handicap)

        session.commit()
        session.close()

        st.success("Handicap settings have been saved!")

if __name__ == "__main__":
    run()
