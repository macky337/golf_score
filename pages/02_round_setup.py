import streamlit as st
import datetime
from modules.db import SessionLocal
from modules.models import Round, Member, Score, HandicapMatch  # HandicapMatch を import

def run():
    """ラウンドの設定ページ"""
    st.title("Round Setup")
    st.write("Set up a new round with date, course, and players.")

    # 1) ラウンド情報の入力フォーム
    date_played = st.date_input("Date of Round", value=datetime.date.today())

    # 過去のラウンドから、使用済みのコース名を取得
    session = SessionLocal()
    past_courses = session.query(Round.course_name).distinct().all()
    session.close()
    past_course_list = [course for (course,) in past_courses if course]

    # 選択肢に「新規入力」を追加
    course_options = ["新規入力"] + past_course_list

    selected_option = st.selectbox("Select Course Name", course_options)
    if selected_option == "新規入力":
        course_name = st.text_input("Course Name", value="Sample Golf Club")
    else:
        course_name = selected_option

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

    # 3) ハンデキャップの設定
    st.subheader("Handicap Settings")
    match_handicaps = []
    for i in range(len(selected_members)):
        for j in range(len(selected_members)):
            if i != j:
                player1 = selected_members[i]
                player2 = selected_members[j]
                handicap = st.number_input(
                    f"{player1} → {player2}",
                    min_value=0,
                    max_value=50,
                    step=1,
                    value=0,
                    key=f"{player1}_to_{player2}"
                )
                match_handicaps.append({
                    "player1": player1,
                    "player2": player2,
                    "handicap": handicap
                })

    # 4) 特定のマッチの集計方法の選択
    st.subheader("Match Calculation Method")
    
    # チェックボックスで選択できるように変更
    match_choices = [
        "荒巻 vs 吉井", 
        "荒巻 vs 福澤", 
        "荒巻 vs 青山", 
        "吉井 vs 福澤", 
        "吉井 vs 青山", 
        "福澤 vs 青山"
    ]
    
    selected_matches = st.multiselect(
        "Select matches to score only total points (max 10 points):", 
        options=match_choices
    )

    # 5) 「Start Round」ボタン
    if st.button("Start Round"):
        if len(selected_members) < 2:
            st.error("少なくとも2人の参加者を選択してください。")
        else:
            session = SessionLocal()
            try:
                # roundsテーブルへINSERT
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

                # HandicapMatch テーブルにマッチ設定をINSERT
                for mh in match_handicaps:
                    p1_id = member_dict[mh["player1"]]
                    p2_id = member_dict[mh["player2"]]
                    new_match = HandicapMatch(
                        round_id=round_id,
                        player_1_id=p1_id,
                        player_2_id=p2_id,
                        player_1_to_2=mh["handicap"] if p1_id < p2_id else 0,
                        player_2_to_1=mh["handicap"] if p2_id < p1_id else 0
                    )
                    session.add(new_match)
                session.commit()

                # 特定マッチを選択した場合
                if selected_matches:
                    st.session_state.selected_matches = selected_matches  # 状態保存

                session.close()

                st.success(f"New round created! Round ID = {round_id}")
                st.info(f"Participants: {', '.join(selected_members)}")
                st.info("Match handicaps have been set:")
                for mh in match_handicaps:
                    st.write(f"- {mh['player1']} → {mh['player2']}: {mh['handicap']}")

            except Exception as e:
                session.rollback()
                st.error(f"エラーが発生しました: {e}")
            finally:
                session.close()

if __name__ == "__main__":
    run()
