# pages/04_back_score_input.py

import streamlit as st
from modules.db import SessionLocal
from modules.models import Round, Score, Member

def run():
    st.title("Back 9 Score Input")

    session = SessionLocal()
    
    # 1) アクティブなラウンドを取得 (例: 未確定の最新ラウンド)
    active_round = session.query(Round).filter_by(finalized=False).order_by(Round.round_id.desc()).first()
    if not active_round:
        st.warning("No active round found. Please set up a round first.")
        session.close()
        return

    st.write(f"**Round ID**: {active_round.round_id}, **Course**: {active_round.course_name}")

    # 2) scoresテーブルから該当ラウンドの行をJOIN取得
    score_rows = (
        session.query(Score)
        .join(Member, Score.member_id == Member.member_id)
        .filter(Score.round_id == active_round.round_id)
        .all()
    )

    if not score_rows:
        st.warning("No participants found for this round.")
        session.close()
        return

    # 3) ユーザー入力フォーム (各メンバーの後半スコア・パット・ゲームPT)
    updates = {}
    for sc in score_rows:
        st.subheader(f"Member: {sc.member.name}")
        back_score_val = st.number_input(
            f"Back Score ({sc.member.name})",
            value=sc.back_score or 0,
            min_value=0, max_value=200,
            key=f"back_score_{sc.score_id}"
        )
        back_putt_val = st.number_input(
            f"Back Putt ({sc.member.name})",
            value=sc.back_putt or 0,
            min_value=0, max_value=50,
            key=f"back_putt_{sc.score_id}"
        )
        back_game_pt_val = st.number_input(
            f"Back Game Points ({sc.member.name})",
            value=sc.back_game_pt or 0,
            min_value=0, max_value=999,
            key=f"back_gamept_{sc.score_id}"
        )
        updates[sc.score_id] = (back_score_val, back_putt_val, back_game_pt_val)

    # 4) "Save Back Scores" ボタン
    if st.button("Save Back Scores"):
        for sc in score_rows:
            bs, bp, bgp = updates[sc.score_id]
            sc.back_score = bs
            sc.back_putt = bp
            sc.back_game_pt = bgp
        session.commit()
        st.success("Back 9 scores saved successfully!")

    session.close()

if __name__ == "__main__":
    run()
