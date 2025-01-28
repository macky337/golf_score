# pages/02_round_setup.py

import streamlit as st
import datetime
from modules.db import SessionLocal
from modules.models import Round, Member, Score  # Scoreをimport

def run():
    """ラウンドの設定ページ"""
    st.title("Round Setup")
    st.write("Set up a new round with date, course, and players.")

    # 1) ラウンド情報の入力フォーム
    date_played = st.date_input("Date of Round", value=datetime.date.today())
    course_name = st.text_input("Course Name", value="Sample Golf Club")
    num_players = st.selectbox("Number of Players", [3, 4], index=1)

    # 2) DBから既存メンバーを取得し、参加者を選択
    session = SessionLocal()
    all_members = session.query(Member).all()
    session.close()

    # メンバー名 -> メンバーID の辞書
    member_dict = {m.name: m.member_id for m in all_members}

    selected_members = st.multiselect(
        "Select participants", 
        options=list(member_dict.keys())
    )

    # 3) 「Start Round」ボタン
    if st.button("Start Round"):
        # roundsテーブルへINSERT
        session = SessionLocal()
        new_round = Round(
            date_played=date_played,
            course_name=course_name.strip(),
            num_players=num_players,
            has_extra=False,
            finalized=False
        )
        session.add(new_round)
        session.commit()

        round_id = new_round.round_id  # 作成されたラウンドのID

        # scoresテーブルへ各メンバー分のスコア枠をINSERT
        for member_name in selected_members:
            member_id = member_dict[member_name]
            new_score = Score(round_id=round_id, member_id=member_id)
            session.add(new_score)
        session.commit()

        session.close()

        st.success(f"New round created! Round ID = {round_id}")
        st.info(f"Participants: {', '.join(selected_members)}")

if __name__ == "__main__":
    run()
