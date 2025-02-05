# pages/05_extra_score_input.py

import streamlit as st
from modules.db import SessionLocal
from modules.models import Round, Score, Member

def run():
    st.title("Extra 9 Score Input (Optional)")

    session = SessionLocal()
    
    # 1) アクティブなラウンドを取得（例：finalized=False で最新）
    active_round = (
        session.query(Round)
        .filter_by(finalized=False)
        .order_by(Round.round_id.desc())
        .first()
    )
    if not active_round:
        st.warning("No active round found. Please set up a round first.")
        session.close()
        return

    st.write(f"**Round ID**: {active_round.round_id}, **Course**: {active_round.course_name}")

    # 2) "has_extra" フラグがFalseの場合の注意表示
    if not active_round.has_extra:
        st.info("This round is not marked as having extra holes, but you can still input them if needed.")

    # 3) Scoreテーブルから該当ラウンドのスコアをJOIN取得
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

    # 4) エキストラスコア入力フォーム
    updates = {}
    for sc in score_rows:
        st.subheader(f"Member: {sc.member.name}")

        # Extra Score: 0～200の範囲で整数
        extra_score_val = st.number_input(
            f"Extra Score ({sc.member.name})",
            value=sc.extra_score or 0,
            min_value=0,
            max_value=200,
            step=1,
            key=f"extra_score_{sc.score_id}"
        )

        # Extra Putt: 0～50の範囲で整数
        extra_putt_val = st.number_input(
            f"Extra Putt ({sc.member.name})",
            value=sc.extra_putt or 0,
            min_value=0,
            max_value=50,
            step=1,
            key=f"extra_putt_{sc.score_id}"
        )

        # Extra Game Points: 小数やマイナスもOK
        extra_game_pt_val = st.number_input(
            f"Extra Game Points ({sc.member.name})",
            value=float(sc.extra_game_pt or 0.0),
            step=0.1,        # 小数ステップ
            format="%.1f",   # 小数点以下1桁表示など必要に応じて変更
            key=f"extra_gamept_{sc.score_id}"
        )

        updates[sc.score_id] = (extra_score_val, extra_putt_val, extra_game_pt_val)

    # 5) "Save Extra Scores" ボタン
    if st.button("Save Extra Scores"):
        for sc in score_rows:
            es, ep, egp = updates[sc.score_id]
            sc.extra_score = int(es)       # extra_score は整数
            sc.extra_putt = int(ep)        # extra_putt も整数
            sc.extra_game_pt = float(egp)  # ゲームポイントは小数可能
        session.commit()
        st.success("Extra 9 scores saved successfully!")

    session.close()

if __name__ == "__main__":
    run()
