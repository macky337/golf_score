# pages/03_front_score_input.py

import streamlit as st
from modules.db import SessionLocal
from modules.models import Round, Score, Member

def run():
    st.title("Front 9 Score Input")

    session = SessionLocal()
    
    # 1) 未確定( finalized=False )のラウンドを取得
    active_round = session.query(Round).filter_by(finalized=False).order_by(Round.round_id.desc()).first()
    if not active_round:
        st.warning("No active round found. Please set up a round first.")
        session.close()
        return

    st.write(f"**Round ID**: {active_round.round_id}, **Course**: {active_round.course_name}")

    # 2) 該当ラウンドの scores を JOIN してメンバー情報と一緒に取得
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

    # 3) 入力フォーム: 各メンバーの前半スコア(front_score)、パット(front_putt)、ゲームポイント(front_game_pt)
    updates = {}
    for sc in score_rows:
        st.subheader(f"Member: {sc.member.name}")
        
        # Front Score: 0～200 の範囲で整数
        front_score_val = st.number_input(
            f"Front Score ({sc.member.name})",
            value=sc.front_score or 0,
            min_value=0,
            max_value=200,
            step=1,
            key=f"front_score_{sc.score_id}"
        )
        
        # Front Putt: 0～50 の範囲で整数
        front_putt_val = st.number_input(
            f"Front Putt ({sc.member.name})",
            value=sc.front_putt or 0,
            min_value=0,
            max_value=50,
            step=1,
            key=f"front_putt_{sc.score_id}"
        )
        
        # Front Game Points: 小数やマイナスもOK、範囲制限なし
        front_game_pt_val = st.number_input(
            f"Front Game Points ({sc.member.name})",
            value=float(sc.front_game_pt or 0.0),
            step=0.1,          # 小数ステップ
            format="%.1f",     # 小数点以下1桁表示など、必要に応じて調整
            key=f"front_gamept_{sc.score_id}"
        )
        
        updates[sc.score_id] = (front_score_val, front_putt_val, front_game_pt_val)

    # 4) "Save Front Scores" ボタン
    if st.button("Save Front Scores"):
        for sc in score_rows:
            fs, fp, fgp = updates[sc.score_id]
            sc.front_score = int(fs)            # front_scoreは整数カラムに保存想定
            sc.front_putt = int(fp)            # front_puttも整数カラム
            sc.front_game_pt = float(fgp)      # game_pt は小数OKにする
        session.commit()
        st.success("Front 9 scores saved successfully!")

    session.close()

if __name__ == "__main__":
    run()
