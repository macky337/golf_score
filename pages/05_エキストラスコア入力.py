# pages/04_back_score_input.py

import streamlit as st
from modules.db import SessionLocal
from modules.models import Round, Score, Member

def run():
    st.title("Back 9 Score Input")

    session = SessionLocal()
    
    # 1) アクティブなラウンドを取得（例：finalized=False で最新）
    active_round = session.query(Round).filter_by(finalized=False).order_by(Round.round_id.desc()).first()
    if not active_round:
        st.warning("No active round found. Please set up a round first.")
        session.close()
        return

    st.write(f"**Round ID**: {active_round.round_id}, **Course**: {active_round.course_name}")

    # 2) "has_extra" フラグがFalseなら注意メッセージ
    if not active_round.has_extra:
        st.info("This round is not marked as having extra holes, but you can still input them if needed.")

    # 3) scoresテーブルから該当ラウンドのスコアをJOIN取得
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

    # 3) ユーザー入力フォーム (各メンバーのエキストラスコア・パット・ゲームPT)
    updates = {}
    for sc in score_rows:
        st.subheader(f"Member: {sc.member.name}")
        
        # エキストラスコア: 0～200の範囲で整数入力
        extra_score_val = st.number_input(
            f"Extra Score ({sc.member.name})",
            value=sc.extra_score or 0,
            min_value=0,
            max_value=200,
            step=1,
            key=f"extra_score_{sc.score_id}"
        )
        
        # エキストラパット: 0～50の範囲で整数入力
        extra_putt_val = st.number_input(
            f"Extra Putt ({sc.member.name})",
            value=sc.extra_putt or 0,
            min_value=0,
            max_value=50,
            step=1,
            key=f"extra_putt_{sc.score_id}"
        )
        
        # エキストラゲームポイント: 小数やマイナスも受け付ける
        extra_game_pt_val = st.number_input(
            f"Extra Game Points ({sc.member.name})",
            value=float(sc.extra_game_pt or 0.0),
            min_value=-999.0,  # マイナス値を許可
            max_value=999.0,
            step=0.1,      # 小数ステップ
            format="%.1f",  # 表示書式: 小数第1位まで
            key=f"extra_gamept_{sc.score_id}"
        )
        
        updates[sc.score_id] = (extra_score_val, extra_putt_val, extra_game_pt_val)

    # 4) "Save Back Scores" ボタン
    if st.button("Save Back Scores"):
        for sc in score_rows:
            es, ep, egp = updates[sc.score_id]
            sc.extra_score = es
            sc.extra_putt = ep
            sc.extra_game_pt = egp
        session.commit()
        st.success("Back 9 scores saved successfully!")

    session.close()

if __name__ == "__main__":
    run()
